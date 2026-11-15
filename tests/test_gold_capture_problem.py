"""Fallback for capture problems: items with meta.json capture_problem show the ic fetch imprint text (no network)."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from ic.gold.annotate.server import make_handler
from ic.gold.annotate.store import Store, read_ic_imprint

IC_TEXT = "Impressum\nMusterfirma GmbH\nMusterweg 1\n12345 Musterstadt Zeile"


def make(tmp_path, problem=True):
    d = tmp_path / "gold"
    (d / "a.de").mkdir(parents=True)
    (d / "b.de").mkdir(parents=True)
    rows = [
        {"item": i, "host": h, "labeller": "L1", "role": "primary", "order": i}
        for i, h in ((1, "a.de"), (2, "b.de"))
    ]
    (d / "assignment.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    meta = {
        "capture_started": "2026-11-14T22:50:00Z",
        "ic_fetch": {"finished_utc": "2026-11-13T09:30:00Z"},
    }
    if problem:
        meta.update(capture_problem=True, capture_problem_reason="503")
    (d / "a.de" / "meta.json").write_text(json.dumps(meta))
    (d / "a.de" / "landing.txt").write_text("landing text")
    rec = {"host": "a.de", "impressum": {"main_content": IC_TEXT}}
    (d / "a.de" / "ic_fetch.jsonl").write_text(
        json.dumps({"host": "a.de"}) + "\n" + json.dumps(rec, ensure_ascii=False) + "\n"
    )
    (d / "b.de" / "meta.json").write_text(
        json.dumps({"capture_started": "2026-11-13T10:00:00Z"})
    )
    (d / "b.de" / "imprint.txt").write_text("real imprint")
    (d / "b.de" / "ic_fetch.jsonl").write_text(
        json.dumps({"host": "b.de", "impressum": {"main_content": "other"}}) + "\n"
    )
    return Store(d, "L1")


def test_read_ic_imprint_last_line_and_missing(tmp_path):
    st = make(tmp_path)
    assert (
        read_ic_imprint(st.data_dir / "a.de") == IC_TEXT
    )  # U+2028 does not split lines
    assert read_ic_imprint(st.data_dir / "nope") == ""


def test_capture_problem_item_gets_ic_text_and_label(tmp_path):
    cap = make(tmp_path).capture("a.de")
    assert (
        cap["texts"]["imprint"] == IC_TEXT and cap["texts"]["landing"] == "landing text"
    )
    assert cap["images"]["imprint"] is None
    assert cap["capture_problem"] == {
        "reason": "503",
        "ic_text": True,
        "label": "ic fetch text, 2026-11-13, no screenshot",
    }


def test_normal_item_unchanged(tmp_path):
    st = make(tmp_path)
    cap = st.capture("b.de")
    assert cap["texts"] == {"imprint": "real imprint"} and "capture_problem" not in cap
    assert "capture_problem" not in make(tmp_path / "x", problem=False).capture(
        "a.de"
    )  # flag off: ic text unused


def test_api_item_shows_flag_but_not_meta(tmp_path):
    st = make(tmp_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(st))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}/api/item?host=a.de"
        d = json.loads(urllib.request.urlopen(url).read())
    finally:
        httpd.shutdown()
    assert "meta" not in d["capture"] and d["capture"]["texts"]["imprint"] == IC_TEXT
    assert d["capture"]["capture_problem"]["ic_text"] is True
    assert d["label"] is None and d["prefill"] is None
