#!/usr/bin/env python3
"""Scan the home pages of every crawl dir in a tables manifest for parking, for-sale and placeholder text.

Usage: scan_crawl_pages.py --manifest TABLES_DIR/manifest.tsv --crawl-root DIR --targets redirect_targets.tsv
                           --out SCANS_DIR [--workers 3]

For every manifest row (from build_crawl_tables.py) it runs `filter_parking_domains.py scan DIR TARGET...`
on the crawl dir (relative to --crawl-root, or absolute) and writes SCANS_DIR/<table name>.scan.tsv, plus
SCANS_DIR/coverage.tsv (one status line per dir). Finished scan files are kept, so the script can resume.
The crawl dirs are only read.
"""

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent


def scan(d, fn, targets):
    cmd = [sys.executable, str(HERE / "filter_parking_domains.py"), "scan", str(d), *targets]
    tmp = fn.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
    err = r.stderr.decode(errors="replace").strip().splitlines()
    stats = next((l[7:] for l in err if l.startswith("#stats ")), "")
    if r.returncode != 0 or not stats:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{d} rc={r.returncode}: {' | '.join(err[-3:])}")
    tmp.rename(fn)
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--crawl-root", default=".", help="base dir for relative crawl dirs (default: .)")
    ap.add_argument("--targets", required=True, help="classified redirect targets (redirect_targets.tsv)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    targets = [l.split("\t")[0] for l in open(a.targets, encoding="utf-8").read().splitlines()[1:]]
    lines = open(a.manifest, encoding="utf-8").read().splitlines()
    head = lines[0].split("\t")
    rows = [dict(zip(head, l.split("\t"))) for l in lines[1:] if l]

    def run(r):
        fn = out / (Path(r["file"]).stem + ".scan.tsv")
        if fn.exists():
            return r, "reused", None
        d = Path(r["dir"]) if Path(r["dir"]).is_absolute() else Path(a.crawl_root) / r["dir"]
        try:
            return r, scan(d, fn, targets), None
        except Exception as e:
            return r, "", e

    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        results = list(ex.map(run, rows))
    for r, st, e in results:
        print("FAIL" if e else "ok", r["dir"], e or st, file=sys.stderr, flush=True)
    failed = [r["dir"] for r, _, e in results if e]
    with open(out / "coverage.tsv", "w", encoding="utf-8") as f:
        f.write("source\tdir\tfile\tstatus\tstats\n")
        for r, st, e in results:
            f.write("\t".join([r["source"], r["dir"], r["file"], "FAILED" if e else "ok", str(e or st)]) + "\n")
    print(f"{len(results)} dirs, {len(failed)} failed", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
