#!/usr/bin/env python3
"""Build the crawl tables that count_sites.py reads: one compact table per crawl dir plus manifest.tsv.

Usage: build_crawl_tables.py --sources SOURCES.tsv --crawl-root DIR --out TABLES_DIR [--workers 4]

SOURCES.tsv has the columns `source` and `dir` (see crawl_sources.example.tsv). `source` is a free label
that names the crawl in the count tables. `dir` is an `ic fetch` output dir, relative to --crawl-root
(or absolute). The row order matters: count_sites.py processes the sources in this order, and within a
source the last row of a host wins.

For every row the script runs extract_crawl_table.py on the dir and writes
TABLES_DIR/<source>_<dir with "/" replaced by "_">.tsv. TABLES_DIR/manifest.tsv lists them in the
order of SOURCES.tsv (columns source, dir, file, rows, sha256, stats). Existing tables are kept, so a
second run only adds the missing ones. The crawl dirs are only read.
"""

import argparse
import hashlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent


def stats_from_table(fn):
    """Stats recomputed from a finished table (used when the table already exists)."""
    rows = found = with_url = 0
    with open(fn, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            rows += 1
            if c[1] == "imprint_found":
                found += 1
                with_url += bool(c[2])
    return f"files=? rows={rows} found={found} with_url={with_url} no_record={found - with_url} reused=1"


def extract(d, fn):
    """Run extract_crawl_table.py on dir d, write fn. Returns the #stats text."""
    cmd = [sys.executable, str(HERE / "extract_crawl_table.py"), str(d)]
    tmp = fn.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
    err = r.stderr.decode(errors="replace").strip().splitlines()
    stats = next((l[7:] for l in err if l.startswith("#stats ")), "")
    if r.returncode != 0 or not stats:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{d} failed rc={r.returncode}: {' | '.join(err[-3:])}")
    tmp.rename(fn)
    return stats


def table_name(source, rel):
    return f"{source}_{rel.strip('/').replace('/', '_')}.tsv"


def run_one(source, rel, root, out):
    d = Path(rel) if Path(rel).is_absolute() else Path(root) / rel
    if not d.is_dir():
        raise RuntimeError(f"{d} is not a directory")
    fn = out / table_name(source, rel)
    stats = stats_from_table(fn) if fn.exists() else extract(d, fn)
    h = hashlib.sha256()
    n = 0
    with open(fn, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += chunk.count(b"\n")
    return [source, rel, fn.name, str(n), h.hexdigest(), stats]


def read_sources(path):
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    rows = [dict(zip(head, l.split("\t"))) for l in lines[1:]]
    return [(r["source"], r["dir"]) for r in rows]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", required=True, help="TSV with the columns source, dir")
    ap.add_argument("--crawl-root", default=".", help="base dir for relative crawl dirs (default: .)")
    ap.add_argument("--out", required=True, help="output dir for the tables and manifest.tsv")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = read_sources(a.sources)

    def work(r):
        try:
            res = run_one(r[0], r[1], a.crawl_root, out)
            print("ok", r[0], r[1], res[3], "rows", file=sys.stderr, flush=True)
            return res
        except Exception as e:  # keep going; reported at the end
            print("FAIL", r[0], r[1], e, file=sys.stderr, flush=True)
            return e

    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        results = list(ex.map(work, rows))
    lines = ["source\tdir\tfile\trows\tsha256\tstats"]
    lines += ["\t".join(r) for r in results if not isinstance(r, Exception)]
    failed = sum(isinstance(r, Exception) for r in results)
    mf = out / "manifest.tsv"
    mf.write_text("\n".join(lines) + "\n")
    print(f"manifest {mf}: {len(lines) - 1} dirs, {failed} failed", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
