"""E53 step 5b: merge of the apfel re-capture into the gold dir (no network)."""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "E53"
spec = importlib.util.spec_from_file_location("recapture_merge", SCRIPTS / "recapture_merge.py")
R = importlib.util.module_from_spec(spec)
sys.modules["recapture_merge"] = R
spec.loader.exec_module(R)


def meta(outcome, files=(), day="2026-11-13", **kw):
    m = {"host": "h.de", "outcome": outcome, "files": list(files), "capture_started": f"{day}T10:00:00Z", "strato": True}
    m.update(kw)
    return m


LAND = ["landing.png", "landing.txt"]
BOTH = LAND + ["imprint.png", "imprint.txt"]


def test_is_better():
    assert R.is_better(meta("landing_only", LAND), meta("landing+imprint", BOTH))
    assert R.is_better(meta("failed"), meta("landing_only", LAND))
    assert not R.is_better(meta("landing+imprint", BOTH), meta("landing_only", LAND))
    assert not R.is_better(meta("landing+imprint", BOTH), meta("landing+imprint", BOTH))
    assert not R.is_better(meta("landing_only", LAND), meta("landing_only", LAND))
    assert R.is_better(meta("landing_only", LAND), meta("landing_only", LAND + ["imprint.txt"]))
    assert not R.is_better(meta("landing_only", LAND), {"capture_missing": True})


def test_merge_meta_day_mismatch():
    old = meta("landing_only", LAND, ic_fetch={"finished_utc": "2026-11-13T09:30:00Z"}, capture_ip_group="akazie")
    same = R.merge_meta(old, meta("landing+imprint", BOTH, capture_ip_group="apfel"))
    assert same["input_day_mismatch"] is False and same["capture_ip_group"] == "apfel"
    assert same["ic_fetch"] == old["ic_fetch"] and same["previous_capture"]["capture_ip_group"] == "akazie"
    other = R.merge_meta(old, meta("landing+imprint", BOTH, day="2026-11-14"))
    assert other["input_day_mismatch"] is True and other["capture_day_utc"] == "2026-11-14"


def test_replace_item_and_manifest(tmp_path):
    gold, new = tmp_path / "gold" / "h.de", tmp_path / "new"
    gold.mkdir(parents=True)
    new.mkdir()
    old = meta("landing_only", LAND, ic_fetch={"finished_utc": "2026-11-13T09:30:00Z"})
    (gold / "meta.json").write_text(json.dumps(old))
    (gold / "ic_fetch.jsonl").write_text('{"host": "h.de"}\n')
    (gold / "landing.txt").write_text("old")
    nm = meta("landing+imprint", BOTH)
    (new / "meta.json").write_text(json.dumps(nm))
    for f in BOTH:
        (new / f).write_text("new " + f)
    m = R.replace_item(gold, new, old, nm)
    assert (gold / "capture_akazie" / "landing.txt").read_text() == "old"
    assert (gold / "landing.txt").read_text() == "new landing.txt" and (gold / "imprint.txt").exists()
    assert (gold / "ic_fetch.jsonl").read_text() == '{"host": "h.de"}\n'
    assert m["previous_capture"]["outcome"] == "landing_only"
    man = R.manifest(tmp_path / "gold", ["h.de"])
    assert "h.de/capture_akazie/landing.txt" in man and "h.de/imprint.txt" in man
    s = R.summarize([m])
    assert s["strato:capture:landing+imprint"] == 1 and s["input_day_mismatch"] == 0
