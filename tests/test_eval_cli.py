"""End-to-end smoke test of `ic score` on a small hand-made sample, labels and prediction files."""

import json
import random

from click.testing import CliRunner

from ic.eval.cli import score

POI = [
    "bathroom-contractor",
    "painter",
    "hardware-store-and-building-supplies",
    "home-improvement-service",
]


def _jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _setup(tmp_path, n=60):
    rng = random.Random(0)
    hosts = [f"h{i:03d}.de" for i in range(n)]
    strata = [f"poi2:s{i % 4}" for i in range(n)]
    sample = []
    for i, h in enumerate(hosts):
        M, m = 40, n // 4
        pi = m / M * 0.005
        sample.append(
            {
                "host": h,
                "stratum": strata[i],
                "M_h": M,
                "m_h": m,
                "pi": pi,
                "weight": 1 / pi,
                "core": i % 2 == 0,
                "fold": i % 5,
                "fold_group": strata[i],
                "classes": [],
                "selected_for": [],
            }
        )
    _jsonl(tmp_path / "sample.jsonl", sample)
    truth = {h: rng.choice(POI) for h in hosts}

    def addr(h):
        return [
            {
                "role": "operator",
                "street": f"Weg {h[1:4]}",
                "number": "1",
                "postcode": "30173",
                "town": "Hannover",
                "country": "",
            }
        ]

    labels, asg = {"L1": [], "L2": []}, []
    for i, h in enumerate(hosts):
        for L in ("L1", "L2") if i < 20 else ("L1",):
            main = truth[h] if L == "L1" or i % 4 else rng.choice(POI)
            labels[L].append(
                {
                    "host": h,
                    "site_status": "live",
                    "imprint_present": True,
                    "addresses": addr(h),
                    "main_address_index": 0,
                    "no_address_reason": None,
                    "topic_labels": {"poi": {"main": main, "extra": []}, "wz": None},
                    "flags": [],
                    "annotator": L,
                }
            )
            asg.append(
                {
                    "item": i,
                    "host": h,
                    "labeller": L,
                    "role": "primary" if L == "L1" else "second",
                    "order": i,
                }
            )
    (tmp_path / "labels").mkdir()
    for L, rows in labels.items():
        _jsonl(tmp_path / "labels" / f"{L}.jsonl", rows)
    _jsonl(tmp_path / "assignment.jsonl", asg)

    preds = tmp_path / "preds"
    preds.mkdir()
    usage = {"calls": 1, "prompt_tokens": 2000, "completion_tokens": 50}
    for model, acc, tag in (
        ("gemma4-31b-it", 0.9, "flat__gemma"),
        ("qwen38-27b", 0.75, "flat__qwen"),
    ):
        rows = [
            {
                "host": h,
                "task": "topic",
                "schema": "poi3",
                "tag": tag,
                "model": model,
                "latency_s": 3.0,
                "main": truth[h] if rng.random() < acc else rng.choice(POI),
                "error": None,
                "usage": usage,
            }
            for h in hosts
        ]
        _jsonl(preds / f"{tag}.jsonl", rows)
    rows = [
        {
            "host": h,
            "task": "address",
            "schema": "address",
            "tag": "address__gemma",
            "model": "gemma4-31b-it",
            "addresses": addr(h),
            "main_index": 0,
            "no_address_reason": None,
            "error": None,
            "usage": usage,
            "latency_s": 2.0,
        }
        for h in hosts
    ]
    _jsonl(preds / "address__gemma.jsonl", rows)
    return tmp_path


def test_cli_writes_all_outputs(tmp_path):
    d = _setup(tmp_path)
    out = tmp_path / "out"
    args = [
        "--sample",
        str(d / "sample.jsonl"),
        "--labels",
        str(d / "labels" / "*.jsonl"),
        "--assignment",
        str(d / "assignment.jsonl"),
        "--preds",
        str(d / "preds"),
        "--out-root",
        str(out),
        "--run-id",
        "t1",
        "--set",
        "B=200",
        "--set",
        "ens2_pairs=all",
    ]
    r = CliRunner().invoke(score, args, catch_exceptions=False)
    assert r.exit_code == 0, r.output
    run = out / "t1"
    for f in (
        "params.json",
        "summary.json",
        "summary.md",
        "agreement.md",
        "reference/stats.json",
        "scores/all.csv",
        "scores/efficiency.md",
    ):
        assert (run / f).is_file(), f
    params = json.loads((run / "params.json").read_text())
    assert params["B"] == 200 and params["method"] == "taylor"
    summ = json.loads((run / "summary.json").read_text())
    assert summ["n_items"] == 60 and summ["n_double"] == 20
    assert set(summ["groups"]) == {"poi", "address"}
    poi = summ["groups"]["poi"]
    names = set(poi["candidates"])
    assert any("ens2" in n for n in names) and len(names) == 3
    assert poi["decision"]["choice"] is not None
    header = (run / "scores/all.csv").read_text().splitlines()[0]
    assert header.startswith("group,candidate,block,metric,est,se,lo,hi")
