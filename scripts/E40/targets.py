#!/usr/bin/env python3
"""E40 step 1: redirect targets with many found hosts. Usage: targets.py --in E31_INDIR --out OUT.tsv [--min 100]"""
import argparse, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E31"))
import release_count as rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min", type=int, default=100)
    a = ap.parse_args()
    crawled, cnt, seen = set(), Counter(), set()
    loaded = []
    for name, paths in rc.load_manifest(a.indir).items():
        loaded.append(rc.read_source(paths, crawled)[1])
    for found in loaded:
        for h, t in found.items():
            if h in seen:
                continue
            seen.add(h)
            if t and rc.collapse(t) != rc.collapse(h):
                cnt[rc.collapse(t)] += 1
    with open(a.out, "w") as f:
        f.write("target\thosts\tcrawled\n")
        for t, n in cnt.most_common():
            if n >= a.min:
                f.write(f"{t}\t{n}\t{int(t in crawled)}\n")
    print(sum(cnt.values()), "redirecting hosts;", sum(1 for n in cnt.values() if n >= a.min), "targets >=", a.min)

main()
