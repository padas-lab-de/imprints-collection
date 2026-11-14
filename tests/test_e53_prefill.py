"""E53 prefill: ledger arithmetic, budget refusal, stop midway, resume, no-imprint skip, ic_fetch adapter. No network."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "E53"))
_spec = importlib.util.spec_from_file_location(
    "e53_prefill", ROOT / "scripts" / "E53" / "prefill.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

TEXT = "Muster GmbH\nMusterstraße 12a\n12345 Musterstadt\nTel 0123"


def item(host, text=TEXT):
    return {"host": host, "imprint_text": text, "homepage_text": "", "meta": {}}


def fake_post(cost=0.001, answer=None, with_cost=True):
    ans = answer or {
        "address": {
            "street": "Musterstraße",
            "number": "12a",
            "postcode": "12345",
            "town": "Musterstadt",
            "country": "",
        },
        "no_address_reason": None,
    }

    def f(key, body):
        assert body["usage"] == {"include": True}
        u = {"prompt_tokens": 1000, "completion_tokens": 50}
        if with_cost:
            u["cost"] = cost
        return {
            "choices": [
                {"message": {"content": json.dumps(ans)}, "finish_reason": "stop"}
            ],
            "usage": u,
        }

    return f


def ledger_rows(p):
    return P.read_ledger(p)


def test_ledger_totals_and_limit():
    rows = [
        {"date_utc": "2026-11-13", "experiment": "E53-prefill", "usd": "1.5"},
        {"date_utc": "2026-11-13", "experiment": "E22", "usd": "4"},
        {"date_utc": "2026-11-12", "experiment": "E53-prefill", "usd": "2"},
    ]
    assert P.ledger_totals(rows, "2026-11-13") == (3.5, 5.5)
    lim, name = P.run_limit(3.5, 5.5)
    assert (lim, name) == (6.5, "D61 total $10")
    assert P.run_limit(0, 29.9)[1] == "UTC day $30"
    assert P.run_limit(0, 0, 0.2) == (0.2, "--max-usd")
    assert P.run_limit(12, 0)[0] == 0.0


def test_append_creates_ledger_with_header(tmp_path):
    p = tmp_path / "l.csv"
    P.append_ledger(
        p, {"date_utc": "2026-11-13", "experiment": "E53-prefill", "usd": "0.1"}
    )
    P.append_ledger(
        p, {"date_utc": "2026-11-13", "experiment": "E53-prefill", "usd": "0.2"}
    )
    assert p.read_text().splitlines()[0] == ",".join(P.COLUMNS)
    assert len(ledger_rows(p)) == 2


def test_estimate_skips_no_imprint():
    e = P.estimate([item("a.de"), item("b.de", ""), item("c.de")])
    assert e["calls"] == 2 and e["skipped_no_imprint"] == 1
    assert e["usd"] == pytest.approx(P.usd_of(e["input_tokens"], e["output_tokens"]))
    assert e["usd_worst"] > e["usd"]


def test_budget_refusal():
    est = {
        "usd": 0.5,
        "calls": 1,
        "input_tokens": 1,
        "output_tokens": 1,
        "usd_worst": 0.5,
    }
    rows = [{"date_utc": "2026-11-13", "experiment": "E53-prefill", "usd": "9.7"}]
    ok, msg = P.check_budget(est, rows, "2026-11-13")
    assert not ok and "9.7" in msg
    assert P.check_budget(est, [], "2026-11-13")[0]
    assert not P.check_budget(est, [], "2026-11-13", max_usd=0.2)[0]
    day = [{"date_utc": "2026-11-13", "experiment": "other", "usd": "29.8"}]
    assert not P.check_budget(est, day, "2026-11-13")[0]


def test_run_writes_output_and_ledger(tmp_path):
    out, led = tmp_path / "o" / "prefill.jsonl", tmp_path / "l.csv"
    s = P.run(
        [item("a.de"), item("b.de")],
        out,
        "k",
        1.0,
        2,
        led,
        "pilot",
        post_fn=fake_post(0.002),
    )
    assert (
        s["calls"] == 2
        and s["usd"] == pytest.approx(0.004)
        and s["usd_source"] == "reported"
    )
    r = json.loads(out.read_text().splitlines()[0])
    assert r["prefilled_from"] == "anthropic/claude-haiku-5.5 via openrouter"
    assert (
        r["label"]["main_address_index"] == 0
        and r["label"]["addresses"][0]["postcode"] == "12345"
    )
    assert r["label"]["addresses"][0]["check"] == []
    assert (
        r["label"]["addresses"][0]["evidence"] == "Musterstraße 12a\n12345 Musterstadt"
    )
    row = ledger_rows(led)[0]
    assert (
        row["experiment"] == "E53-prefill"
        and row["calls"] == "2"
        and row["input_tokens"] == "2000"
    )
    assert row["note"] == "pilot" and float(row["usd"]) == pytest.approx(0.004)


def test_unverbatim_field_is_checked(tmp_path):
    ans = {
        "address": {
            "street": "Hauptstr.",
            "number": "1",
            "postcode": "12345",
            "town": "Musterstadt",
            "country": "",
        },
        "no_address_reason": None,
    }
    out = tmp_path / "p.jsonl"
    P.run(
        [item("a.de")],
        out,
        "k",
        1.0,
        1,
        tmp_path / "l.csv",
        "",
        post_fn=fake_post(answer=ans),
    )
    assert "street" in json.loads(out.read_text())["label"]["addresses"][0]["check"]


def test_no_imprint_no_call(tmp_path):
    def boom(key, body):
        raise AssertionError("called")

    out = tmp_path / "p.jsonl"
    s = P.run(
        [item("a.de", "")], out, "k", 1.0, 1, tmp_path / "l.csv", "", post_fn=boom
    )
    r = json.loads(out.read_text())
    assert (
        r["no_address_reason"] == "no_imprint"
        and r["label"]["addresses"] == []
        and r["error"] is None
    )
    assert s["calls"] == 0 and s["no_imprint"] == 1


def test_stop_midway_and_resume(tmp_path):
    out, led = tmp_path / "p.jsonl", tmp_path / "l.csv"
    items = [item(f"h{i}.de") for i in range(10)]
    worst = P.usd_of(P.est_input_tokens(P.AD.messages(items[0], P.CFG)), P.MAX_TOKENS)
    limit = (
        worst * 3.5
    )  # one worker; each call is reported at the worst case, so 3 calls fit
    s = P.run(items, out, "k", limit, 1, led, "", post_fn=fake_post(cost=worst))
    assert s["written"] == 3 and "stopped" in s["status"]
    assert s["usd"] <= limit
    assert s["stopped_unprocessed"] == 7
    assert "stopped" in ledger_rows(led)[0]["note"]
    first = {json.loads(l)["host"] for l in out.open()}
    seen = []

    def post2(key, body):
        seen.append(1)
        return fake_post()(key, body)

    s2 = P.run(items, out, "k", 5.0, 1, led, "resume", post_fn=post2)
    assert len(seen) == 7 and s2["written"] == 7
    assert {json.loads(l)["host"] for l in out.open()} == {it["host"] for it in items}
    assert first.isdisjoint(
        {json.loads(l)["host"] for l in out.read_text().splitlines()[3:]}
    )
    assert len(ledger_rows(led)) == 2


def test_missing_cost_is_estimated(tmp_path):
    s = P.run(
        [item("a.de")],
        tmp_path / "p.jsonl",
        "k",
        1.0,
        1,
        tmp_path / "l.csv",
        "",
        post_fn=fake_post(with_cost=False),
    )
    assert s["usd_source"] == "estimated" and s["usd"] == pytest.approx(
        P.usd_of(1000, 50)
    )


def test_parse_failure_and_api_error_are_retried_on_resume(tmp_path):
    out, led = tmp_path / "p.jsonl", tmp_path / "l.csv"

    def bad(key, body):
        r = fake_post()(key, body)
        r["choices"][0]["message"]["content"] = "keine Antwort"
        return r

    def api(key, body):
        raise RuntimeError("HTTP 500")

    s = P.run([item("a.de")], out, "k", 1.0, 1, led, "", post_fn=bad)
    assert (
        s["parse_failures"] == 1 and s["calls"] == 1 and s["usd"] > 0
    )  # a parse failure was still billed
    P.run([item("b.de")], out, "k", 1.0, 1, led, "", post_fn=api)
    assert P.done_hosts(out) == set()
    P.run([item("a.de"), item("b.de")], out, "k", 1.0, 1, led, "", post_fn=fake_post())
    assert P.done_hosts(out) == {"a.de", "b.de"}


def test_crash_still_writes_ledger_row(tmp_path):
    led = tmp_path / "l.csv"

    def boom(key, body):
        raise KeyboardInterrupt

    with pytest.raises(BaseException):
        P.run([item("a.de")], tmp_path / "p.jsonl", "k", 1.0, 1, led, "x", post_fn=boom)
    assert "failed" in ledger_rows(led)[0]["note"]


def test_ic_fetch_adapter(tmp_path):
    d = tmp_path / "x.de"
    d.mkdir()
    rec = {
        "host": "x.de",
        "main": {"url": "https://x.de/", "main_content": "Start"},
        "impressum": {"url": "https://x.de/impressum", "main_content": TEXT},
    }
    (d / "ic_fetch.jsonl").write_text(json.dumps(rec) + "\n")
    (tmp_path / "y.de").mkdir()
    (tmp_path / "y.de" / "ic_fetch.jsonl").write_text(
        json.dumps({"host": "y.de", "main": {"main_content": "x"}}) + "\n"
    )
    items = P.read_ic_fetch(tmp_path)
    by = {i["host"]: i for i in items}
    assert (
        by["x.de"]["imprint_text"].startswith("Muster GmbH")
        and by["y.de"]["imprint_text"] == ""
    )
    assert P.estimate(items)["calls"] == 1


def test_rel_path_outside_repo_keeps_datasets_part(tmp_path):
    p = (
        tmp_path
        / "other-checkout"
        / "datasets"
        / "E53"
        / "gold"
        / "prefill_topup.jsonl"
    )
    assert P._rel(p) == "datasets/E53/gold/prefill_topup.jsonl"
    assert P._rel(P.ROOT / "docs" / "x.csv") == "docs/x.csv"
