"""E53 step 5: merge of ic fetch output with the capture, and the capture wrapper (no network, no browser)."""

import gzip
import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "E53"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load("merge_fetch")
CAP = _load("capture")
PREFILL = _load("prefill")


def _status(host, status, end, secs="2.0"):
    return "\t".join([host, status, "", "v4:1.2.3", "1", "3", "0", secs, str(end)]) + "\n"


def _write_fetch(d: Path, rows, recs, batch=0):
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"fetch_status_batch{batch}.tsv", "w") as f:
        f.writelines(rows)
    with gzip.open(d / f"imprints_batch{batch}.jsonl.gz", "wt") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


T0 = 1794560400  # 2026-11-13T09:00:00Z


def test_iso_and_fetch_class():
    assert M.iso(T0) == "2026-11-13T09:00:00Z"
    assert M.fetch_class("imprint_found") == "imprint_found"
    assert M.fetch_class("imprint_not_found") == "no_imprint"
    assert M.fetch_class("host_not_found") == "failed"
    assert M.fetch_class(None) == "failed"


def test_last_row_and_record_win_across_dirs(tmp_path):
    a, b = tmp_path / "main", tmp_path / "shop"
    _write_fetch(a, [_status("s.de", "skipped_provider", T0), _status("x.de", "imprint_found", T0), "cut\tline"], [{"host": "x.de", "v": 1}])
    _write_fetch(b, [_status("s.de", "imprint_found", T0 + 60)], [{"host": "s.de", "v": 2}])
    rows, recs = M.read_status([a, b]), M.read_records([a, b])
    assert rows["s.de"]["status"] == "imprint_found"
    assert set(rows) == {"s.de", "x.de"}
    assert recs["s.de"]["v"] == 2 and recs["x.de"]["v"] == 1


def test_merge_item_same_day_and_mismatch():
    row = {"status": "imprint_found", "detail": "", "seconds": "5.0", "end_time": str(T0)}
    rec = {"host": "x.de", "main": {"main_content": "a"}, "impressum": {"main_content": "Musterstr. 1"}}
    line, m = M.merge_item("x.de", row, rec, {"host": "x.de", "capture_started": "2026-11-13T10:00:00Z", "outcome": "landing+imprint"}, "aralie", "88b162a")
    assert line["fetch_status"] == "imprint_found" and line["fetched_at"] == "2026-11-13T09:00:00Z" and line["impressum"]
    assert m["ic_fetch"]["started_utc"] == "2026-11-13T08:59:55Z" and m["ic_fetch"]["has_record"]
    assert m["input_day_mismatch"] is False
    _, m2 = M.merge_item("x.de", row, rec, {"capture_started": "2026-11-14T00:01:00Z"}, "aralie", "t")
    assert m2["input_day_mismatch"] is True


def test_merge_item_no_record_no_capture():
    line, m = M.merge_item("y.de", {"status": "host_not_found", "detail": "https:dns", "seconds": "1", "end_time": str(T0)}, None, None, "aralie", "t")
    assert line == {"host": "y.de", "fetch_status": "host_not_found", "fetch_detail": "https:dns", "fetched_at": "2026-11-13T09:00:00Z", "fetch_vm": "aralie"}
    assert m["capture_missing"] and m["ic_fetch"]["class"] == "failed" and not m["ic_fetch"]["has_record"]
    assert m["input_day_mismatch"] is False
    _, m3 = M.merge_item("z.de", None, None, None, "aralie", "t")
    assert m3["ic_fetch"]["status"] == "not_fetched"


def test_main_writes_items_readable_by_prefill(tmp_path, monkeypatch):
    sample = tmp_path / "s.jsonl"
    sample.write_text("".join(json.dumps({"host": h}) + "\n" for h in ["x.de", "y.de"]))
    fd = tmp_path / "fetch"
    _write_fetch(fd, [_status("x.de", "imprint_found", T0), _status("y.de", "host_not_found", T0)],
                 [{"host": "x.de", "main": {"url": "https://x.de", "main_content": "Home"}, "impressum": {"url": "https://x.de/impressum", "main_content": "Firma X,\u2028Musterstr. 1,\x85 12345 Ort"}}])
    gold = tmp_path / "gold"
    (gold / "x.de").mkdir(parents=True)
    (gold / "x.de" / "meta.json").write_text(json.dumps({"host": "x.de", "capture_started": "2026-11-13T11:00:00Z", "outcome": "landing+imprint", "dns": {"strato": True}, "consent_banner": [{"page": "landing", "action": "rejected"}, {"page": "imprint", "action": "none"}]}))
    monkeypatch.setattr(sys, "argv", ["m", "--sample", str(sample), "--gold", str(gold), "--fetch-dir", str(fd), "--fetch-vm", "aralie", "--fetch-tree", "t", "--summary", str(tmp_path / "sum.json")])
    M.main()
    s = json.loads((tmp_path / "sum.json").read_text())
    assert s["counts"]["fetch:imprint_found"] == 1 and s["counts"]["fetch:failed"] == 1
    assert s["counts"]["banner:landing:rejected"] == 1 and s["counts"]["banner:imprint:none"] == 1
    assert s["counts"]["strato:capture:landing+imprint"] == 1 and s["counts"]["capture:missing"] == 1
    assert (gold / "manifest.sha256").read_text().count("\n") == s["manifest_files"] == 4
    items = PREFILL.read_ic_fetch(gold)
    assert [i["host"] for i in items] == ["x.de", "y.de"]
    assert "Musterstr" in items[0]["imprint_text"] and items[1]["imprint_text"] == ""
    # U+2028 / U+0085 in text must not break the one-line JSONL (str.splitlines splits on them)
    raw = (gold / "x.de" / "ic_fetch.jsonl").read_text(encoding="utf-8")
    assert raw.isascii() and len(raw.splitlines()) == 1


def test_capture_wrapper_meta(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(json.dumps({"host": "a.de", "core": True, "stratum": "x", "fold": 2, "weight": 3.5, "pi": 0.1}) + "\n")
    items = CAP.load_sample(p)
    assert items == [{"item": None, "host": "a.de", "e53": {"core": True, "stratum": "x", "fold": 2, "weight": 3.5}}]
    rec = CAP.add_e53_meta({"capture_started": "2026-11-13T09:25:11Z", "dns": {"strato": True}}, items[0], "akazie")
    assert rec["capture_ip_group"] == "akazie" and rec["capture_day_utc"] == "2026-11-13" and rec["strato"] is True
    assert rec["e53_sample"]["weight"] == 3.5
