"""E53 step 5: join the same-day `ic fetch` output (crawl VM) with the gold capture (capture VM).

For every host of the sample, in <gold>/<safe(host)>/:
- ic_fetch.jsonl: one line, the last `ic fetch` record of the host (main, kontakt, impressum, ...) plus
  "fetch_status", "fetch_detail", "fetched_at" (UTC), "fetch_vm". A host without a record (host_not_found,
  filtered, no_valid_html_tree, error) gets a line with these fields and no page data, so every item has a model input.
- meta.json: adds "ic_fetch" {status, detail, started_utc, finished_utc, vm, tree, has_record} and
  "input_day_mismatch" (UTC day of `ic fetch` != UTC day of the capture). A host without a capture gets a meta.json
  with "capture_missing": true.
Fetch dirs are read in the given order; within and across dirs the last complete status row and the last record of
a host win (ic fetch resume rule), so the Shopify pass overrides the "skipped_provider" rows of pass 1.
Writes <gold>/manifest.sha256 (sha256 and path of every file in the item dirs, sorted) and prints a JSON summary.

  python3 -I scripts/E53/merge_fetch.py --sample S --gold datasets/E53/gold --fetch-dir D1 [--fetch-dir D2] \
      --fetch-vm aralie --fetch-tree 88b162a [--summary out.json]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

STATUS_COLUMNS = ["host", "status", "detail", "provider", "attempts", "requests", "throttled", "seconds", "end_time"]
FAILED = ("host_not_found", "no_valid_html_tree", "filtered", "error", "skipped_provider")


def safe(host: str) -> str:  # as scripts/gold/e8_pilot.py safe()
    return re.sub(r"[^a-zA-Z0-9.\-]", "_", host)


def iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _batch_no(p: Path) -> int:
    m = re.search(r"batch(\d+)", p.name)
    return int(m.group(1)) if m else -1


def read_status(dirs: list[Path]) -> dict[str, dict]:
    """host -> last complete status row (dict with STATUS_COLUMNS) over the dirs in order."""
    out: dict[str, dict] = {}
    for d in dirs:
        for p in sorted(d.glob("fetch_status_batch*.tsv"), key=_batch_no):
            for line in p.open(encoding="utf-8", errors="replace"):
                if not line.endswith("\n"):
                    break
                f = line.rstrip("\n").split("\t")
                if len(f) == len(STATUS_COLUMNS) and f[0] != "host":
                    out[f[0]] = dict(zip(STATUS_COLUMNS, f))
    return out


def read_records(dirs: list[Path]) -> dict[str, dict]:
    """host -> last `ic fetch` record over the dirs in order (a cut-off gzip end is ignored)."""
    out: dict[str, dict] = {}
    for d in dirs:
        for p in sorted(d.glob("imprints_batch*.jsonl.gz"), key=_batch_no):
            try:
                with gzip.open(p, "rt", encoding="utf-8") as fh:
                    for line in fh:
                        if line.strip():
                            r = json.loads(line)
                            out[r["host"]] = r
            except (EOFError, OSError):
                pass
    return out


def fetch_class(status: str | None) -> str:
    if status == "imprint_found":
        return "imprint_found"
    if status == "imprint_not_found":
        return "no_imprint"
    return "failed"


def merge_item(host: str, row: dict | None, rec: dict | None, meta: dict | None, vm: str, tree: str) -> tuple[dict, dict]:
    """Pure: (ic_fetch line, updated meta) for one host."""
    status = row["status"] if row else "not_fetched"
    end = float(row["end_time"]) if row else None
    start = end - float(row["seconds"]) if row else None
    line = dict(rec) if rec else {"host": host}
    line.update(fetch_status=status, fetch_detail=row["detail"] if row else "", fetched_at=iso(end) if end else None, fetch_vm=vm)
    m = dict(meta) if meta else {"host": host, "capture_missing": True, "complete": False, "files": []}
    m["ic_fetch"] = {
        "status": status, "class": fetch_class(status if row else None), "detail": row["detail"] if row else "",
        "started_utc": iso(start) if start else None, "finished_utc": iso(end) if end else None,
        "vm": vm, "tree": tree, "has_record": rec is not None,
    }
    cap_day = (m.get("capture_started") or "")[:10]
    fetch_day = iso(end)[:10] if end else ""
    m["input_day_mismatch"] = bool(cap_day and fetch_day and cap_day != fetch_day)
    return line, m


def manifest(gold: Path, hosts: list[str]) -> str:
    lines = []
    for h in sorted(hosts):
        d = gold / safe(h)
        for p in sorted(d.iterdir()):
            if p.is_file():
                lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {d.name}/{p.name}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--fetch-dir", action="append", required=True)
    ap.add_argument("--fetch-vm", required=True)
    ap.add_argument("--fetch-tree", required=True)
    ap.add_argument("--summary")
    a = ap.parse_args()
    gold = Path(a.gold)
    hosts = [json.loads(l)["host"] for l in open(a.sample, encoding="utf-8") if l.strip()]
    dirs = [Path(d) for d in a.fetch_dir]
    rows, recs = read_status(dirs), read_records(dirs)
    c: Counter = Counter()
    for h in hosts:
        d = gold / safe(h)
        d.mkdir(parents=True, exist_ok=True)
        mp = d / "meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else None
        line, m = merge_item(h, rows.get(h), recs.get(h), meta, a.fetch_vm, a.fetch_tree)
        (d / "ic_fetch.jsonl").write_text(json.dumps(line) + "\n", encoding="utf-8")
        mp.write_text(json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        strato = "strato" if m.get("strato") or (m.get("dns") or {}).get("strato") else "other"
        c[f"fetch:{m['ic_fetch']['class']}"] += 1
        c[f"fetch_status:{m['ic_fetch']['status']}"] += 1
        c[f"capture:{m.get('outcome', 'missing')}"] += 1
        c[f"{strato}:fetch:{m['ic_fetch']['class']}"] += 1
        c[f"{strato}:capture:{m.get('outcome', 'missing')}"] += 1
        c[f"{strato}:n"] += 1
        c["input_day_mismatch"] += m["input_day_mismatch"]
        for b in m.get("consent_banner") or []:
            c[f"banner:{b.get('page')}:{b.get('action')}"] += 1
        c["has_record"] += m["ic_fetch"]["has_record"]
    man = manifest(gold, hosts)
    (gold / "manifest.sha256").write_text(man)
    out = {"items": len(hosts), "counts": dict(sorted(c.items())), "manifest_files": man.count("\n"),
           "manifest_sha256": hashlib.sha256(man.encode()).hexdigest(),
           "fetch_window_utc": [min((iso(float(r["end_time"]) - float(r["seconds"])) for r in rows.values()), default=None),
                                max((iso(float(r["end_time"])) for r in rows.values()), default=None)]}
    if a.summary:
        Path(a.summary).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
