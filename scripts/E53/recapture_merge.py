"""E53 step 5b (D62 C): merge the Strato re-capture from apfel into datasets/E53/gold.

For every host in the re-capture dir whose new capture is better than the akazie capture
(rank landing+imprint 2 > landing_only 1 > failed/missing 0; a tie at landing_only counts as better when the
new capture has imprint files and the old one has none):
- the akazie capture files move to <host>/capture_akazie/ (ic_fetch.jsonl, prefill/assignment files stay),
- the apfel capture files are copied in,
- meta.json = apfel meta + "ic_fetch" of the old meta + "previous_capture" (old meta) + recomputed
  "input_day_mismatch" (capture day != ic fetch day, UTC).
ic_fetch.jsonl is never touched. Writes a manifest (all files below the item dirs, recursive) and a summary.

  python3 -I scripts/E53/recapture_merge.py --sample S --gold datasets/E53/gold --new datasets/E53/recapture_apfel \
      [--summary out.json] [--dry-run]
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
    m["previous_capture"] = {k: v for k, v in old.items() if k != "previous_capture"}
    cap_day = (m.get("capture_started") or "")[:10]
    fetch_day = ((old.get("ic_fetch") or {}).get("finished_utc") or "")[:10]
    m["input_day_mismatch"] = bool(cap_day and fetch_day and cap_day != fetch_day)
    m["capture_ip_group"] = "apfel"
    m["capture_day_utc"] = cap_day
    return m


def replace_item(gold_dir: Path, new_dir: Path, old: dict, new: dict) -> dict:
    arch = gold_dir / "capture_akazie"
    arch.mkdir(exist_ok=True)
    for p in sorted(gold_dir.iterdir()):
        if p.is_file() and p.name not in KEEP:
            shutil.move(str(p), arch / p.name)
    for p in sorted(new_dir.iterdir()):
        if p.is_file() and p.name not in KEEP:
            shutil.copy2(p, gold_dir / p.name)
    m = merge_meta(old, new)
    (gold_dir / "meta.json").write_text(json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return m


def manifest(gold: Path, hosts: list[str]) -> str:
    lines = []
    for h in sorted(hosts):
        d = gold / safe(h)
        for p in sorted(x for x in d.rglob("*") if x.is_file()):
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(gold)}")
    return "\n".join(lines) + "\n"


def summarize(metas: list[dict]) -> dict:
    c: Counter = Counter()
    for m in metas:
        s = "strato" if m.get("strato") or (m.get("dns") or {}).get("strato") else "other"
        c[f"{s}:n"] += 1
        c[f"capture:{m.get('outcome', 'missing')}"] += 1
        c[f"{s}:capture:{m.get('outcome', 'missing')}"] += 1
        c["input_day_mismatch"] += bool(m.get("input_day_mismatch"))
        c["capture_ip_group:" + str(m.get("capture_ip_group"))] += 1
    return dict(sorted(c.items()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--summary")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    gold, new = Path(a.gold), Path(a.new)
    hosts = [json.loads(l)["host"] for l in open(a.sample, encoding="utf-8") if l.strip()]
    replaced, kept = [], []
    for h in hosts:
        nd, gd = new / safe(h), gold / safe(h)
        if not (nd / "meta.json").exists():
            continue
        nm = json.loads((nd / "meta.json").read_text(encoding="utf-8"))
        om = json.loads((gd / "meta.json").read_text(encoding="utf-8"))
        if is_better(om, nm):
            if not a.dry_run:
                replace_item(gd, nd, om, nm)
            replaced.append(h)
        else:
            kept.append(h)
    out = {"replaced": len(replaced), "kept_akazie": len(kept), "replaced_hosts": replaced}
    if a.dry_run:
        print(json.dumps({k: v for k, v in out.items() if k != "replaced_hosts"}, indent=1))
    else:
        write_summary(gold, a.summary, out)


def write_summary(gold: Path, summary: str | None, out: dict) -> None:
    hosts = sorted(p.parent.name for p in gold.glob("*/meta.json"))
    metas = [json.loads((gold / h / "meta.json").read_text(encoding="utf-8")) for h in hosts]
    man = manifest(gold, [m for m in hosts])
    (gold / "manifest.sha256").write_text(man)
    out.update(items=len(hosts), counts=summarize(metas), manifest_files=man.count("\n"),
               manifest_sha256=hashlib.sha256(man.encode()).hexdigest())
    if summary:
        Path(summary).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "replaced_hosts"}, indent=1))


if __name__ == "__main__":
    main()
