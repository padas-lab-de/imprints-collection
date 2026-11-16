"""Slow re-capture (host delay in capture.py) and the extra options of recapture_merge.py (no network)."""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "goldset"


def _load(name):
    spec = importlib.util.spec_from_file_location(name + "_opts", SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name + "_opts"] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("recapture_merge")
CAP = _load("capture")

LAND = ["landing.png", "landing.txt"]
BOTH = LAND + ["imprint.png", "imprint.txt"]


def meta(outcome, files=(), day="2026-11-13", **kw):
    m = {
        "host": "h.de",
        "outcome": outcome,
        "files": list(files),
        "capture_started": f"{day}T10:00:00Z",
        "strato": True,
    }
    m.update(kw)
    return m


class _Base:
    def __init__(self):
        self.pending = ["a", "b", "c"]
        self.released = []

    def pick(self, now=None):
        return self.pending.pop(0) if self.pending else None

    def release(self, h):
        self.released.append(h)


def test_delayed_scheduler_rests_between_hosts():
    t = [0.0]
    sched = CAP.delayed_scheduler(_Base, 60, clock=lambda: t[0])()
    assert sched.pick() == "a"  # first host: no wait
    sched.release("a")  # ends at t=0
    t[0] = 59.9
    assert sched.pick() is None
    t[0] = 60.0
    assert sched.pick() == "b"
    t[0] = 200.0  # a long item: the rest counts from its end
    sched.release("b")
    t[0] = 259.0
    assert sched.pick() is None
    t[0] = 260.0
    assert sched.pick() == "c"


def test_delayed_scheduler_stops_after_block():
    state = {}
    sched = CAP.delayed_scheduler(_Base, 60, state, clock=lambda: 0.0)()
    assert sched.pick() == "a"
    state["stop"] = {"host": "a"}
    assert (
        sched.pick() is None and sched.pending == []
    )  # the worker loop ends, no waiting


def test_flag_capture_problem_and_rule(tmp_path):
    d = tmp_path / "h.de"
    d.mkdir()
    (d / "meta.json").write_text(json.dumps(meta("landing_only", LAND)))
    assert R.needs_capture_problem(meta("landing_only", LAND))
    assert not R.needs_capture_problem(meta("landing+imprint", BOTH))
    R.flag_capture_problem(d, "503")
    m = json.loads((d / "meta.json").read_text())
    assert m["capture_problem"] is True and m["capture_problem_reason"] == "503"


def test_main_only_imprint_archive_and_flags(tmp_path, monkeypatch):
    gold, new = tmp_path / "gold", tmp_path / "new"
    sample = tmp_path / "s.jsonl"
    sample.write_text(
        "".join(json.dumps({"host": h}) + "\n" for h in ("a.de", "b.de", "c.de"))
    )
    ic = {"finished_utc": "2026-11-13T09:30:00Z"}
    for h in ("a.de", "b.de", "c.de"):
        (gold / h).mkdir(parents=True)
        (gold / h / "meta.json").write_text(
            json.dumps(meta("landing_only", LAND, host=h, ic_fetch=ic))
        )
        (gold / h / "landing.txt").write_text("old")
        (gold / h / "prefill.jsonl").write_text("p")
    (gold / "manifest.sha256").write_text("old manifest\n")
    # a.de: new landing+imprint; b.de: new landing_only with imprint.txt (better, but not accepted); c.de: not captured
    newcaps = (
        (
            "a.de",
            meta(
                "landing+imprint",
                BOTH,
                day="2026-11-14",
                host="a.de",
                capture_ip_group="capture1",
            ),
            BOTH,
        ),
        (
            "b.de",
            meta("landing_only", LAND + ["imprint.txt"], day="2026-11-14", host="b.de"),
            LAND + ["imprint.txt"],
        ),
    )
    for h, m, files in newcaps:
        (new / h).mkdir(parents=True)
        (new / h / "meta.json").write_text(json.dumps(m))
        for f in files:
            (new / h / f).write_text("new")
    hosts = tmp_path / "hosts.txt"
    hosts.write_text("a.de\nb.de\nc.de\n")
    argv = [
        "x", "--sample", str(sample), "--gold", str(gold), "--new", str(new),
        "--archive-name", "capture_previous2", "--only-imprint", "--hosts", str(hosts),
        "--problem-list", str(tmp_path / "p.txt"), "--keep-old-manifest", "manifest_pre_d63.sha256",
        "--summary", str(tmp_path / "sum.json"),
    ]  # fmt: skip
    monkeypatch.setattr(sys, "argv", argv)
    R.main()
    ma = json.loads((gold / "a.de" / "meta.json").read_text())
    assert (
        ma["outcome"] == "landing+imprint"
        and ma["input_day_mismatch"] is True
        and ma["capture_ip_group"] == "capture1"
    )
    assert (gold / "a.de" / "capture_previous2" / "landing.txt").read_text() == "old"
    assert (
        gold / "a.de" / "prefill.jsonl"
    ).read_text() == "p" and "capture_problem" not in ma
    for h in ("b.de", "c.de"):
        m = json.loads((gold / h / "meta.json").read_text())
        assert m["capture_problem"] is True and m["outcome"] == "landing_only"
        assert (
            not (gold / h / "capture_previous2").exists()
            and (gold / h / "landing.txt").read_text() == "old"
        )
    assert (tmp_path / "p.txt").read_text() == "b.de\nc.de\n"
    assert (gold / "manifest_pre_d63.sha256").read_text() == "old manifest\n"
    s = json.loads((tmp_path / "sum.json").read_text())
    assert (
        s["replaced"] == 1
        and s["capture_problem"] == 2
        and s["counts"]["capture_problem"] == 2
    )
