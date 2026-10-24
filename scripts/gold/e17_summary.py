"""Summarise datasets/gold/*/meta.json into counts, sizes and timing (prints Markdown)."""

import collections
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("IC_DATA_ROOT", "/home/dinzinger/GitHub/imprints-collection"))
OUT = ROOT / "datasets" / "gold"


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def main():
    metas = []
    for d in sorted(OUT.iterdir()):
        p = d / "meta.json"
        if p.exists():
            metas.append(json.loads(p.read_text()))
    deferred = [l for l in (OUT / "deferred_strato.txt").read_text().split() if l]
    c = collections.Counter(m["outcome"] for m in metas)
    fail = collections.Counter(m.get("failure_reason") for m in metas if m["outcome"] == "failed")
    status = collections.Counter(m["site_status_at_capture"] for m in metas)
    cross = collections.Counter((m["screening_site_status"], m["site_status_at_capture"]) for m in metas)
    banner = collections.Counter(b["action"] for m in metas for b in m["consent_banner"])
    via = collections.Counter((m["imprint"] or {}).get("via") for m in metas if m["outcome"] == "landing+imprint")
    pdfs = sum(1 for m in metas if (OUT / m["host"].replace("/", "_") / "imprint.pdf").exists())
    trunc = sum(1 for m in metas if (m["landing"] or {}).get("screenshot_truncated") or ((m["imprint"] or {}).get("screenshot_truncated")))
    nolanding_png = sum(1 for m in metas if m["outcome"] != "failed" and "landing.png" not in m["files"])
    size = collections.Counter()
    for dp, _dn, fn in os.walk(OUT):
        for f in fn:
            ext = f.split(".", 1)[1] if "." in f else f
            size[ext] += os.path.getsize(os.path.join(dp, f))
    total = sum(size.values())
    starts = [ts(m["capture_started"]) for m in metas]
    ends = [ts(m["capture_finished"]) for m in metas]
    wall = (max(ends) - min(starts)).total_seconds()
    per = sorted((ts(m["capture_finished"]) - ts(m["capture_started"])).total_seconds() for m in metas)
    print(f"items with meta.json: {len(metas)}; deferred Strato: {len(deferred)}")
    print("outcome", dict(c))
    print("failed by reason", dict(fail))
    print("site status at capture", dict(status))
    print("screening status -> status at capture", {f"{a}->{b}": n for (a, b), n in sorted(cross.items())})
    print("banner actions (per captured page)", dict(banner))
    print("imprint found via", dict(via))
    print("imprint.pdf files", pdfs, "| screenshots truncated at 20,000 px", trunc, "| captured items without landing.png", nolanding_png)
    print("total size MB", round(total / 1e6, 1), {k: round(v / 1e6, 1) for k, v in size.most_common()})
    print(f"wall time {wall:.0f}s from {min(starts)} to {max(ends)}; per-item median {per[len(per)//2]:.0f}s, p90 {per[int(len(per)*.9)]:.0f}s, max {per[-1]:.0f}s")
    errs = collections.Counter(m.get("render_error", "")[:40] for m in metas if m.get("render_error"))
    print("render errors", dict(errs))


if __name__ == "__main__":
    main()
