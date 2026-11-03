#!/usr/bin/env python3
"""Deduplicated imprint_found count over several crawl sources (E16, E19, E22 ...).

Usage: dedup_count.py --out OUT.tsv NAME=DIR[,DIR...] NAME=DIR ...   (sources in order, first = base)
Each DIR holds fetch_status_batch*.tsv (9 columns, header starts with `host`). Files are only read.

Per source: the status of a host is its LAST complete row (ic fetch resume rule; dirs of one source
in the given order, files sorted by name). A host counts as imprint_found if that last row says so.
"new" = imprint_found hosts of this source not imprint_found in any source above it.
Hosts are compared exactly (lowercased, stripped). The second set of columns applies the www collapse
(www.x.de = x.de) to every host before counting.
"""
import argparse
import sys
from pathlib import Path

NCOLS = 9


def strip_www(h):
    return h[4:] if h.startswith("www.") else h


def read_source(dirs):
    """(rows = unique hosts, found = set of hosts whose last row is imprint_found, files)."""
    found, seen, files = set(), set(), 0
    for d in dirs:
        for p in sorted(Path(d).glob("fetch_status_batch*.tsv")):
            files += 1
            with open(p, encoding="utf-8", newline="") as f:
                for line in f:
                    c = line.rstrip("\n").split("\t")
                    if len(c) != NCOLS or c[0] == "host":
                        continue
                    h = c[0].strip().lower()
                    seen.add(h)
                    if c[1] == "imprint_found":
                        found.add(h)
                    else:
                        found.discard(h)
    return len(seen), found, files


def combine(sources):
    """sources: [(name, rows, found_set, files)] -> list of dict rows (+ total row)."""
    cum, cum_w = set(), set()
    out = []
    for name, rows, found, files in sources:
        fw = {strip_www(h) for h in found}
        new, new_w = found - cum, fw - cum_w
        cum |= found
        cum_w |= fw
        out.append(
            dict(source=name, files=files, hosts=rows, imprint_found=len(found), new=len(new),
                 cumulative=len(cum), found_www=len(fw), new_www=len(new_w), cumulative_www=len(cum_w))
        )
    out.append(dict(source="TOTAL", files=sum(s[3] for s in sources), hosts=sum(s[1] for s in sources),
                    imprint_found=sum(len(s[2]) for s in sources), new=len(cum), cumulative=len(cum),
                    found_www="", new_www=len(cum_w), cumulative_www=len(cum_w)))
    return out


COLS = ["source", "files", "hosts", "imprint_found", "new", "cumulative", "found_www", "new_www", "cumulative_www"]


def format_tsv(rows):
    return "\n".join(["\t".join(COLS)] + ["\t".join(str(r[c]) for c in COLS) for r in rows]) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out")
    ap.add_argument("sources", nargs="+", help="NAME=DIR[,DIR...]")
    a = ap.parse_args(argv)
    srcs = []
    for s in a.sources:
        name, dirs = s.split("=", 1)
        rows, found, files = read_source(dirs.split(","))
        srcs.append((name, rows, found, files))
        print(f"{name}: {files} files, {rows} hosts, {len(found)} imprint_found", file=sys.stderr)
    text = format_tsv(combine(srcs))
    print(text, end="")
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    sys.exit(main())
