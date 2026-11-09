#!/usr/bin/env python3
"""E40 r2: the round-1 view of a round-2 scan. Reads r2 scan files and writes one TSV with the F rows that
round 1 alone gives (r2-decided rows fall back to their r1_cat / r1_label columns, or are dropped).
Running `parking_filter.py apply` on this file must reproduce the round-1 count; this separates pattern
effects from data changes.

Usage: r1_view.py OUT.tsv SCAN.tsv [SCAN.tsv ...]
"""

import sys

out, n_r1, n_fb, n_drop = open(sys.argv[1], "w", encoding="utf-8"), 0, 0, 0
for p in sys.argv[2:]:
    for line in open(p, encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) < 7 or c[1] != "F":
            continue
        if not c[3].startswith("r2_"):
            out.write("\t".join(c[:7]) + "\n")
            n_r1 += 1
        elif len(c) > 8 and c[7]:
            out.write("\t".join(c[:2] + [c[7], c[8]] + c[4:7]) + "\n")
            n_fb += 1
        else:
            n_drop += 1
print(f"r1_rows {n_r1} r1_fallback {n_fb} r2_only_dropped {n_drop}")
