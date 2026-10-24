"""Pure-function tests for scripts/gold/e17_capture.py (no network, no browser)."""

import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "e17_capture", Path(__file__).resolve().parents[1] / "scripts" / "gold" / "e17_capture.py"
)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)


def test_reject_labels_match():
    for t in ["Alle ablehnen", "  Nur notwendige  ", "Nur notwendige Cookies akzeptieren", "REJECT ALL", "Ablehnen ✕", "Only necessary"]:
        assert C.is_reject_label(t), t


def test_accept_labels_do_not_match():
    for t in ["Alle akzeptieren", "Akzeptieren", "Einstellungen", "Mehr erfahren", "Ich stimme zu", "Alle Cookies zulassen", ""]:
        assert not C.is_reject_label(t), t


def test_pick_reject_first_match():
    assert C.pick_reject(["Akzeptieren", "Einstellungen", "Ablehnen", "Reject"]) == 2
    assert C.pick_reject(["Akzeptieren"]) is None


def test_strato_filter():
    assert C.in_strato(["81.169.145.20"])
    assert C.in_strato(["2001:db8::1", "81.169.145.255"])
    assert not C.in_strato(["81.169.146.1", "2a01:238::1"])
    assert not C.in_strato([])


def test_provider_key():
    assert C.provider_key(["81.169.145.20"]) == "81.169.145.0/24"
    assert C.provider_key(["2001:db8:1:2::1"]) == "2001:db8:1::/48"


def _write_meta(d: Path, **kw):
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(kw))


def test_resume_check(tmp_path):
    d = tmp_path / "a.de"
    assert not C.is_complete(d)  # no dir
    _write_meta(d, complete=False, files=[])
    assert not C.is_complete(d)
    _write_meta(d, complete=True, files=["landing.png"])
    assert not C.is_complete(d)  # listed file missing
    (d / "landing.png").write_bytes(b"x")
    assert C.is_complete(d)
    (d / "meta.json").write_text("{broken")
    assert not C.is_complete(d)


def test_resume_retry_failed(tmp_path):
    d = tmp_path / "b.de"
    _write_meta(d, complete=True, files=[], outcome="failed", failure_reason="no_dns")
    assert C.is_complete(d)
    assert not C.is_complete(d, retry_failed=True)


def test_scheduler_caps_per_group():
    groups = {"a1": "g", "a2": "g", "a3": "g", "b1": "h", "n1": None}
    s = C.GroupScheduler(list(groups), groups, cap=2, gap=0.0)
    got = [s.pick(now=0.0) for _ in range(5)]
    assert sum(1 for h in got if h and groups[h] == "g") == 2  # third host of group g waits
    assert "b1" in got and "n1" in got
    assert s.pick(now=0.0) is None
    s.release("a1" if "a1" in got else got[0])
    assert s.pick(now=1.0) is not None


def test_scheduler_gap():
    groups = {"a1": "g", "a2": "g"}
    s = C.GroupScheduler(["a1", "a2"], groups, cap=2, gap=5.0)
    assert s.pick(now=0.0) is not None
    assert s.pick(now=1.0) is None
    assert s.pick(now=6.0) is not None


def test_failure_reason():
    assert C.failure_reason("x.de", {"x.de": {"error": "gaierror"}}, None, {}) == "no_dns"
    assert C.failure_reason("x.de", {}, None, {"goto_error": "Error:Page.goto: net::ERR_CONNECTION_REFUSED at"}) == "err_connection_refused"
    assert C.failure_reason("x.de", {}, "TimeoutError", {}) == "item_timeout"
    assert C.failure_reason("x.de", {}, None, {"static": {"error": "SSLError"}}) == "SSLError"


def test_host_dir_safe():
    assert C.host_dir("www.a-b.de", Path("/o")).name == "www.a-b.de"
    assert "/" not in C.host_dir("a/b", Path("/o")).name
