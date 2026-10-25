import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "E19"))

import collect  # noqa: E402
import merge_report  # noqa: E402

HEADER = "\t".join(collect.COLUMNS)


def row(host, status="host_not_found", detail="", provider="v4:1.2.3", throttled="0"):
    return {"host": host, "status": status, "detail": detail, "provider": provider,
            "attempts": "1", "requests": "2", "throttled": throttled, "seconds": "1.0", "end_time": "1"}


def write_tsv(path, rows, partial_line=None):
    lines = [HEADER] + ["\t".join(r[c] for c in collect.COLUMNS) for r in rows]
    text = "\n".join(lines) + "\n"
    if partial_line:
        text += partial_line
    Path(path).write_text(text)


@pytest.mark.parametrize(
    "detail,expected",
    [
        ("https:http403;http:http403", "403"),
        ("https:dns;http:dns", None),
        ("https:ssl;http:ssl", None),
        ("https:http404;http:http404", None),
        ("https:http500;http:http500", None),
        ("https:ssl;http:timeout", "timeout"),  # retryable on one scheme is enough
        ("https:dns;http:conn", "conn_refused"),
        ("https:refused;http:refused", "conn_refused"),
        ("https:http429;http:http403", "throttle"),  # priority throttle > 403
        ("https:http503;http:timeout", "throttle"),
        ("https:timeout;http:refused", "timeout"),
        ("https:empty;http:redirects", None),
    ],
)
def test_classify_host_not_found(detail, expected):
    c = collect.classify(row("a.de", detail=detail))
    assert (c[0] if c else None) == expected


def test_other_status_not_selected_unless_throttled_flag():
    r = row("a.de", status="imprint_not_found", detail="", throttled="3")
    assert collect.classify(r) is None
    assert collect.classify(r, include_throttled=True)[0] == "throttled"
    found = row("b.de", status="imprint_found", throttled="3")
    assert collect.classify(found, include_throttled=True) is None
    # a non-throttled imprint_not_found stays out
    assert collect.classify(row("c.de", status="imprint_not_found"), include_throttled=True) is None


def test_completeness(tmp_path):
    assert collect.is_complete([0] * 25000, 3)
    assert not collect.is_complete([0] * 24999, 3)
    # last batch: remainder of the seed list
    assert collect.expected_rows(2, total_hosts=60_000, batch_size=25_000) == 10_000
    assert collect.is_complete([0] * 10_000, 2, total_hosts=60_000)
    assert not collect.is_complete([0] * 25_000, 2, total_hosts=60_000)


def test_complete_batches_skips_incomplete_and_partial_line(tmp_path):
    write_tsv(tmp_path / "fetch_status_batch000000.tsv", [row(f"h{i}.de") for i in range(5)])
    write_tsv(tmp_path / "fetch_status_batch000001.tsv", [row(f"g{i}.de") for i in range(3)])
    # batch 2 is the last (total 13 hosts, batch size 5 -> 3 rows) and has a half-written line
    write_tsv(tmp_path / "fetch_status_batch000002.tsv", [row(f"k{i}.de") for i in range(3)], "half\tline")
    done, skipped = collect.complete_batches(tmp_path, total_hosts=13, batch_size=5)
    assert sorted(done) == [0, 2]
    assert skipped == [(1, 3, 5)]


def test_select_and_main(tmp_path):
    seeds, out = tmp_path / "seeds", tmp_path / "out"
    seeds.mkdir()
    rows = [
        row("ok.de", status="imprint_found"),
        row("dns.de", detail="https:dns;http:dns"),
        row("forbidden.de", detail="https:http403;http:http403", provider="v4:5.5.5"),
        row("slow.de", detail="https:timeout;http:timeout", provider="v4:5.5.5"),
        row("rate.de", detail="https:http429;http:http429"),
    ]
    write_tsv(seeds / "fetch_status_batch000000.tsv", rows)
    deferred = tmp_path / "deferred.txt"
    deferred.write_text("strato1.de\nrate.de\n")
    collect.main(["--seeds-dir", str(seeds), "--out-dir", str(out), "--deferred", str(deferred),
                  "--total-hosts", "5", "--batch-size", "5"])
    assert (out / "recovery_hosts.txt").read_text().split() == ["forbidden.de", "slow.de", "rate.de"]
    assert (out / "deferred_strato_hosts.txt").read_text().split() == ["strato1.de", "rate.de"]
    assert (out / "recovery_all.txt").read_text().split() == ["forbidden.de", "slow.de", "rate.de", "strato1.de"]
    counts = dict(l.split("\t") for l in (out / "counts_by_cause.tsv").read_text().split("\n")[1:] if l)
    assert counts == {"403": "1", "timeout": "1", "throttle": "1", "total": "3"}
    prov = (out / "counts_by_provider.tsv").read_text()
    assert "v4:5.5.5\t0\t1\t1\t2" in prov


def test_merge_report(tmp_path):
    e16 = [
        row("f1.de", detail="https:http403;http:http403"),
        row("f2.de", detail="https:http403;http:http403"),
        row("f3.de", detail="https:http403;http:http403"),
        row("t1.de", detail="https:timeout;http:timeout"),
        row("t2.de", detail="https:timeout;http:timeout"),
        row("fine.de", status="imprint_found"),
    ]
    rec = [
        row("f1.de", status="imprint_found"),
        row("f2.de", status="imprint_not_found"),
        row("f3.de"),
        row("t1.de", status="host_not_found"),
        row("strato1.de", status="imprint_found"),
    ]
    table = merge_report.report(e16, rec, listed_hosts=["t2.de", "f1.de"])
    assert table["403"]["imprint_found"] == 1
    assert table["403"]["imprint_not_found"] == 1
    assert table["403"]["still_failing"] == 1
    assert table["timeout"]["still_failing"] == 1
    assert table["timeout"]["not_retried"] == 1
    assert table["other_listed"]["imprint_found"] == 1
    text = merge_report.format_table(table)
    lines = {l.split("\t")[0]: l.split("\t") for l in text.split("\n")}
    assert lines["403"][1:] == ["3", "1", "1", "1", "0", "33.3"]
    assert lines["total"][1] == "6"


def test_merge_report_cli(tmp_path):
    e16, rec = tmp_path / "e16", tmp_path / "rec"
    e16.mkdir()
    rec.mkdir()
    write_tsv(e16 / "fetch_status_batch000000.tsv", [row("a.de", detail="https:http503;http:http503")])
    write_tsv(rec / "fetch_status_batch000000.tsv", [row("a.de", status="imprint_found")])
    out = tmp_path / "table.tsv"
    merge_report.main(["--e16-dir", str(e16), "--recovery-dir", str(rec), "--out", str(out)])
    assert "throttle\t1\t1\t0\t0\t0\t100.0" in out.read_text()
