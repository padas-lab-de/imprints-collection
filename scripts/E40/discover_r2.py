#!/usr/bin/env python3
"""E40 round 2, pattern discovery. Read-only, stdlib only, local dirs only.

Usage: discover_r2.py --pairs DIR=HOSTS_TSV [...] --out OUT.tsv [--max-len 1500]

For each crawl dir, keep the last home-page record per host, restrict to imprint_found hosts of the paired
E31 host TSV (last-row rule), and write every found host that the current filter (r1, or r1+r2 when the
module has R2 patterns) does NOT flag and whose content_length <= --max-len:
host, content_length, title, desc, content head (600 chars). Analysis (title frequencies, random reading)
is done on that file.
"""

import argparse
import gzip
import importlib.util
import json
import zlib
from pathlib import Path

spec = importlib.util.spec_from_file_location("pf", Path(__file__).resolve().parent / "parking_filter.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)


def found_hosts(tsv):
    found = set()
    for line in open(tsv, encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) != 3:
            continue
        if c[1] == "imprint_found":
            found.add(c[0])
        else:
            found.discard(c[0])
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-len", type=int, default=1500)
    a = ap.parse_args()
    with open(a.out, "w", encoding="utf-8") as out:
        for pair in a.pairs:
            d, tsv = pair.split("=", 1)
            found = found_hosts(tsv)
            last = {}
            for p in sorted(Path(d).glob("imprints_batch*.jsonl.gz")):
                try:
                    with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            try:
                                r = json.loads(line)
                                h = str(r["host"]).strip().lower()
                                m = r.get("main") or {}
                            except (ValueError, KeyError, TypeError, AttributeError):
                                continue
                            if h not in found:
                                continue
                            c = m.get("main_content") or ""
                            try:
                                clen = int(m.get("content_length") or len(c))
                            except ValueError:
                                clen = len(c)
                            if clen > a.max_len:
                                last.pop(h, None)
                                continue
                            t, ds = m.get("title") or "", m.get("description") or ""
                            if pf.detect(t, ds, c, clen):
                                last.pop(h, None)
                                continue
                            last[h] = (str(clen), pf._flat(t, 120), pf._flat(ds, 150), pf._flat(c, 600))
                except (EOFError, zlib.error, OSError):
                    pass
            for h, v in last.items():
                out.write("\t".join([h, *v, Path(tsv).stem]) + "\n")
            print(d, len(found), len(last), flush=True)


if __name__ == "__main__":
    main()
