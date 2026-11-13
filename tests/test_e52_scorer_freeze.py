"""E52 step 1: freeze the topic scorers.

The E49 scorer (scripts/E49/score.py) and the E50 scorer (scripts/E50/compare.py) must reproduce the unweighted
tables of results/E49/poi3c/summary.md on the E49 references (dev and held-out, all hosts and offline). The gold-set
scores of E52 use these scorers; a change that moves these numbers fails here.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "E49"))
sys.path.insert(0, str(ROOT / "scripts" / "E50"))
import compare as CP  # noqa: E402
from score import score  # noqa: E402
from tree import load_schema  # noqa: E402

B = ROOT / "results/E49/poi3b/preds"
C = ROOT / "results/E49/poi3c/preds"
Q = "flat__qwen__both__dmax__nt-path__think__nl-both.jsonl"
G = "flat__gemma__both__dmax__nt-path__reason__nl-both.jsonl"
E = "ens2__qwen_gemma__nl-both.jsonl"
SETS = {
    "dev": (
        "results/E49/refs/poi_v3.jsonl",
        B / "dev/poi3" / Q,
        C / "dev/poi3" / G,
        C / "dev/poi3" / E,
    ),
    "held-out": (
        "results/E49/heldout/refs/poi_v3.jsonl",
        B / "heldout/poi3" / Q,
        B / "heldout/poi3" / G,
        C / "heldout/poi3" / E,
    ),
}
SUMMARY = ROOT / "results/E49/poi3c/summary.md"


def _load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _summary_rows() -> dict:
    """(set, subset, config) -> table cells from summary.md."""
    out, head = {}, None
    for line in SUMMARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            s, sub = line[4:].split(" (n=")[0].split(", ")
            head = (s, sub)
        elif (
            head
            and line.startswith("| ")
            and _cells(line)[0] in ("qwen b", "gemma b", "ens2")
        ):
            if len(_cells(line)) == 15:
                out[head + (_cells(line)[0],)] = _cells(line)
    return out


def _cases():
    tree = load_schema("poi3")
    for sname, (refs_p, qp, gp, ep) in SETS.items():
        refs = {r["host"]: r for r in _load(ROOT / refs_p)}
        preds = {
            k: {p["host"]: p for p in _load(f)}
            for k, f in (("qwen b", qp), ("gemma b", gp), ("ens2", ep))
        }
        keep = {h for h, r in refs.items() if r["main"] is not None}
        for ps in preds.values():
            keep &= {h for h, p in ps.items() if p.get("error") != "no_input"}
        for sub, hosts in (
            ("all hosts", keep),
            ("offline", {h for h in keep if not refs[h]["online_only"]}),
        ):
            yield tree, sname, sub, refs, preds, sorted(hosts)


@pytest.fixture(scope="module")
def rows():
    r = _summary_rows()
    assert len(r) == 12  # 2 sets x 2 subsets x 3 configs
    return r


def test_e49_score_reproduces_poi3c(rows):
    f = lambda v: "n/a" if v is None else f"{v:.3f}"  # noqa: E731
    for tree, sname, sub, refs, preds, hs in _cases():
        for k, ps in preds.items():
            m = score(tree, refs, [p for h, p in ps.items() if h in set(hs)])
            L = {x["level"]: x for x in m["levels"]}
            c = m["cost_per_host"]
            got = (
                [k, str(m["abstain"]), str(m["errors"])]
                + [f(L[i]["precision"]) for i in (1, 2, 3)]
                + [f(L[i]["acc_trunc"]) for i in (1, 2, 3)]
                + [f(L[i]["coverage"]) for i in (1, 2, 3)]
                + [
                    str(c["latency_s"]),
                    str(c["prompt_tokens"]),
                    str(c["completion_tokens"]),
                ]
            )
            assert got == rows[(sname, sub, k)], (sname, sub, k)


def test_e50_compare_reproduces_poi3c(rows):
    """compare.py (E50) gives the same P@1-3 as score.py (E49) on the same hosts, and its acc@L is score.py's
    hit / n_ref rescaled to all hosts.

    acc@L is defined differently in the two scorers: score.py acc_trunc (the acc columns of summary.md) truncates
    both paths to L, so a reference that stops above L still counts as a hit when the prediction equals it;
    compare.py counts a hit at L only if the reference reaches L. The two agree when every reference reaches L
    (L1); they differ at L2 by up to 0.010 and at L3 by about 0.3 on these sets.
    """
    for tree, sname, sub, refs, preds, hs in _cases():
        for k, ps in preds.items():
            v = CP.host_vectors(tree, refs, list(ps.values()))
            assert set(hs) <= set(v)
            s = CP.summary(v, hs, 2)
            want = rows[(sname, sub, k)]
            assert [f"{x:.3f}" for x in s["P"][:3]] == want[3:6], (sname, sub, k)
            assert f"{s['acc'][0]:.3f}" == want[6], (
                sname,
                sub,
                k,
            )  # every reference reaches L1
            m = score(tree, refs, [p for h, p in ps.items() if h in set(hs)])
            for j, lv in enumerate(m["levels"]):
                if lv["acc"] is not None:
                    assert s["acc"][j] == pytest.approx(
                        lv["acc"] * lv["n_ref"] / len(hs), abs=0.002
                    ), (sname, sub, k, j)
