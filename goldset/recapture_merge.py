"""Re-capture merge: merge a re-capture (for example of the Strato hosts, from a second capture machine) into
the gold data folder (datasets/goldset/gold).

For every host in the re-capture dir whose new capture is better than the current capture
(rank landing+imprint 2 > landing_only 1 > failed/missing 0; a tie at landing_only counts as better when the
new capture has imprint files and the old one has none):
- the current capture files move to <host>/capture_previous/ (ic_fetch.jsonl, prefill/assignment files stay),
- the new capture files are copied in,
- meta.json = new meta + "ic_fetch" of the old meta + "previous_capture" (old meta) + recomputed
  "input_day_mismatch" (capture day != ic fetch day, UTC).
ic_fetch.jsonl is never touched. Writes a manifest (all files below the item dirs, recursive) and a summary.

  python3 -I goldset/recapture_merge.py --sample S --gold datasets/goldset/gold --new datasets/goldset/recapture \
      [--summary out.json] [--dry-run]

A slow second re-capture of the items still without an imprint capture uses more options:
  --archive-name capture_previous2 old capture files go here instead of capture_previous/
  --only-imprint                   replace only when the new capture is landing+imprint
  --hosts H.txt                    the re-capture list; a host of it without a landing+imprint capture after the merge
                                   (not replaced, or not captured because the run stopped) gets meta.json
                                   "capture_problem": true + "capture_problem_reason" (item metadata; the labelling tool then shows the ic fetch imprint text)
  --problem-list P.txt             write those hosts, one per line
  --keep-old-manifest NAME         copy the old manifest.sha256 to <gold>/NAME before writing the new one
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

KEEP = {"ic_fetch.jsonl", "prefill.jsonl", "assignment.jsonl", "meta.json"}
RANK = {"landing+imprint": 2, "landing_only": 1}


def safe(host: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.\-]", "_", host)


def has_imprint(meta: dict | None) -> bool:
    return bool(meta) and any(f.startswith("imprint.") for f in meta.get("files") or [])


def is_better(old: dict | None, new: dict | None) -> bool:
    """Pure: is the new capture better than the old one."""
    if not new or new.get("capture_missing"):
        return False
    ro, rn = RANK.get((old or {}).get("outcome"), 0), RANK.get(new.get("outcome"), 0)
    if rn != ro:
        return rn > ro
    return rn == 1 and has_imprint(new) and not has_imprint(old)


def merge_meta(old: dict, new: dict) -> dict:
    """Pure: meta.json of the replaced item."""
    m = dict(new)
    m["ic_fetch"] = old.get("ic_fetch")
    m["previous_capture"] = dict(old)
    cap_day = (m.get("capture_started") or "")[:10]
    fetch_day = ((old.get("ic_fetch") or {}).get("finished_utc") or "")[:10]
    m["input_day_mismatch"] = bool(cap_day and fetch_day and cap_day != fetch_day)
    m.setdefault("capture_ip_group", "recapture")
    m["capture_day_utc"] = cap_day
    return m


def replace_item(
    gold_dir: Path, new_dir: Path, old: dict, new: dict, archive: str = "capture_previous"
) -> dict:
    arch = gold_dir / archive
    arch.mkdir(exist_ok=True)
    for p in sorted(gold_dir.iterdir()):
        if p.is_file() and p.name not in KEEP:
            shutil.move(str(p), arch / p.name)
    for p in sorted(new_dir.iterdir()):
        if p.is_file() and p.name not in KEEP:
            shutil.copy2(p, gold_dir / p.name)
    m = merge_meta(old, new)
    (gold_dir / "meta.json").write_text(
        json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return m


def needs_capture_problem(meta: dict | None) -> bool:
    """Pure: the item has no landing+imprint capture (fallback B: the labeller works from the ic fetch text)."""
    return (meta or {}).get("outcome") != "landing+imprint"


def flag_capture_problem(gold_dir: Path, reason: str) -> None:
    """Set capture_problem in meta.json (item metadata; prefill/assignment files stay untouched)."""
    mp = gold_dir / "meta.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    m["capture_problem"] = True
    m["capture_problem_reason"] = reason
    mp.write_text(
        json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8"
    )


def manifest(gold: Path, hosts: list[str]) -> str:
    lines = []
    for h in sorted(hosts):
        d = gold / safe(h)
        for p in sorted(x for x in d.rglob("*") if x.is_file()):
            lines.append(
                f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(gold)}"
            )
    return "\n".join(lines) + "\n"


def summarize(metas: list[dict]) -> dict:
    c: Counter = Counter()
    for m in metas:
        s = (
            "strato"
            if m.get("strato") or (m.get("dns") or {}).get("strato")
            else "other"
        )
        c[f"{s}:n"] += 1
        c[f"capture:{m.get('outcome', 'missing')}"] += 1
        c[f"{s}:capture:{m.get('outcome', 'missing')}"] += 1
        c["input_day_mismatch"] += bool(m.get("input_day_mismatch"))
        c["capture_problem"] += bool(m.get("capture_problem"))
        c["capture_ip_group:" + str(m.get("capture_ip_group"))] += 1
    return dict(sorted(c.items()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--summary")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--archive-name", default="capture_previous")
    ap.add_argument("--only-imprint", action="store_true")
    ap.add_argument("--hosts")
    ap.add_argument("--problem-list")
    ap.add_argument("--keep-old-manifest")
    ap.add_argument(
        "--problem-reason",
        default="no imprint capture after the re-capture (landing page ok, imprint not captured); label from the ic fetch text",
    )
    a = ap.parse_args()
    gold, new = Path(a.gold), Path(a.new)
    hosts = [
        json.loads(l)["host"] for l in open(a.sample, encoding="utf-8") if l.strip()
    ]
    replaced, kept = [], []
    for h in hosts:
        nd, gd = new / safe(h), gold / safe(h)
        if not (nd / "meta.json").exists():
            continue
        nm = json.loads((nd / "meta.json").read_text(encoding="utf-8"))
        om = json.loads((gd / "meta.json").read_text(encoding="utf-8"))
        if is_better(om, nm) and (
            nm.get("outcome") == "landing+imprint" or not a.only_imprint
        ):
            if not a.dry_run:
                replace_item(gd, nd, om, nm, a.archive_name)
            replaced.append(h)
        else:
            kept.append(h)
    out = {
        "replaced": len(replaced),
        "kept_old": len(kept),
        "replaced_hosts": replaced,
    }
    if a.hosts:
        todo = [l.strip() for l in open(a.hosts, encoding="utf-8") if l.strip()]
        problem = []
        for h in todo:
            mp = gold / safe(h) / "meta.json"
            if needs_capture_problem(json.loads(mp.read_text(encoding="utf-8"))):
                problem.append(h)
                if not a.dry_run:
                    flag_capture_problem(gold / safe(h), a.problem_reason)
        out["capture_problem"] = len(problem)
        if a.problem_list and not a.dry_run:
            Path(a.problem_list).write_text(
                "".join(h + "\n" for h in sorted(problem)), encoding="utf-8"
            )
    if a.dry_run:
        print(
            json.dumps(
                {k: v for k, v in out.items() if k != "replaced_hosts"}, indent=1
            )
        )
    else:
        write_summary(gold, a.summary, out, a.keep_old_manifest)


def write_summary(
    gold: Path, summary: str | None, out: dict, keep_old: str | None = None
) -> None:
    hosts = sorted(p.parent.name for p in gold.glob("*/meta.json"))
    metas = [
        json.loads((gold / h / "meta.json").read_text(encoding="utf-8")) for h in hosts
    ]
    man = manifest(gold, [m for m in hosts])
    if keep_old and (gold / "manifest.sha256").exists():
        shutil.copy2(gold / "manifest.sha256", gold / keep_old)
    (gold / "manifest.sha256").write_text(man)
    out.update(
        items=len(hosts),
        counts=summarize(metas),
        manifest_files=man.count("\n"),
        manifest_sha256=hashlib.sha256(man.encode()).hexdigest(),
    )
    if summary:
        Path(summary).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "replaced_hosts"}, indent=1))


if __name__ == "__main__":
    main()
