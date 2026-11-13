#!/usr/bin/env python3
"""E40 round 2: after-filter site list, summary, r1 vs r2 deltas per category and per source, SHA256SUMS.

Usage: finalize_r2.py --sites E31_OUT/canonical_sites.txt --r1 R1_E40_OUT --r2 R2_DIR
  R1_E40_OUT / R2_DIR hold flagged_sites.tsv and filter_by_source.tsv (`parking_filter.py apply` output).
Writes into R2_DIR: canonical_sites_after_filter.txt (D34 sites minus sale, park and host sites; sorted, as in
E31/compare_r3_r4.py), release_count_after_filter.tsv, delta_by_category.tsv, delta_by_source.tsv, SHA256SUMS.txt.

Category sale_flag (from `parking_filter.py apply --name-for-sale-flag-only`) is kept, like constr: it is not in
DROP, so no option is needed here. Its rows are written only when such sites exist, so round-2 output is unchanged.
"""

import argparse
import hashlib
from collections import Counter
from pathlib import Path

DROP = ("sale", "park", "host")
CATS = ("sale", "park", "host", "constr")
KEPT_EXTRA = ("sale_flag",)  # written only if present


def sha(fn):
    h = hashlib.sha256()
    with open(fn, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def flagged(fn):
    out = {}
    with open(fn) as f:
        next(f)
        for line in f:
            s, c = line.split("\t")[:2]
            out[s] = c
    return out


def by_source(fn):
    with open(fn) as f:
        head = f.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True)
    ap.add_argument("--r1", required=True)
    ap.add_argument("--r2", required=True)
    a = ap.parse_args()
    r1d, r2d = Path(a.r1), Path(a.r2)
    sites = [l.rstrip("\n") for l in open(a.sites)]
    f1, f2 = flagged(r1d / "flagged_sites.tsv"), flagged(r2d / "flagged_sites.tsv")
    drop1 = {s for s, c in f1.items() if c in DROP}
    drop2 = {s for s, c in f2.items() if c in DROP}
    after = sorted(set(sites) - drop2)
    with open(r2d / "canonical_sites_after_filter.txt", "w") as f:
        f.write("".join(s + "\n" for s in after))
    after1 = len(set(sites) - drop1)
    c1, c2 = Counter(f1.values()), Counter(f2.values())
    # transitions r1 -> r2 per site
    trans = Counter((f1.get(s, "-"), f2.get(s, "-")) for s in set(f1) | set(f2) if f1.get(s) != f2.get(s))
    with open(r2d / "delta_by_category.tsv", "w") as f:
        f.write("category\tr1_sites\tr2_sites\tdelta\n")
        for c in CATS + tuple(c for c in KEPT_EXTRA if c1[c] or c2[c]):
            f.write(f"{c}\t{c1[c]}\t{c2[c]}\t{c2[c] - c1[c]}\n")
        f.write(f"drop_total(sale+park+host)\t{len(drop1)}\t{len(drop2)}\t{len(drop2) - len(drop1)}\n")
        f.write(f"sites_after_filter\t{after1}\t{len(after)}\t{len(after) - after1}\n")
        f.write(f"r1_dropped_not_dropped_by_r2\t{len(drop1 - drop2)}\t\t\n")
        f.write("\ntransition_r1_to_r2\tsites\n")
        for (x, y), n in sorted(trans.items(), key=lambda t: -t[1]):
            f.write(f"{x}->{y}\t{n}\n")
    s1, s2 = by_source(r1d / "filter_by_source.tsv"), by_source(r2d / "filter_by_source.tsv")
    # r5 patch: R2 may have sources that R1 lacks (E48, E34r4) and new_d34 of an older source can shift by a few
    # sites (a newly crawled host becomes a redirect target). Match rows by source name; a source missing in R1
    # gets zeros; a new_d34 mismatch is reported on stderr instead of failing.
    import sys
    s1 = {r["source"]: r for r in s1}
    zero = dict(new_d34="0", sale="0", park="0", host="0", constr="0")
    pairs = []
    for y in s2:
        x = s1.get(y["source"])
        if x is None:
            print(f"r5: source {y['source']} not in r1, r1 values = 0", file=sys.stderr)
            x = dict(zero, source=y["source"])
        elif x["new_d34"] != y["new_d34"]:
            print(f"r5: {y['source']} new_d34 r1 {x['new_d34']} r2 {y['new_d34']}", file=sys.stderr)
        pairs.append((x, y))
    cols = ["new_d34", "flagged_all", "sale", "park", "host", "constr", "new_d34_after_all"]
    with open(r2d / "delta_by_source.tsv", "w") as f:
        f.write("source\tnew_d34\tr1_after_drop\tr2_after_drop\tadded_drops\tadded_sale\tadded_park\tadded_host\tadded_constr\n")
        for x, y in pairs:
            d = {c: int(y[c]) - int(x[c]) for c in ("sale", "park", "host", "constr")}
            r1a = int(x["new_d34"]) - int(x["sale"]) - int(x["park"]) - int(x["host"])
            r2a = int(y["new_d34"]) - int(y["sale"]) - int(y["park"]) - int(y["host"])
            f.write("\t".join(map(str, [x["source"], x["new_d34"], r1a, r2a, r1a - r2a, d["sale"], d["park"], d["host"], d["constr"]])) + "\n")
    with open(r2d / "release_count_after_filter.tsv", "w") as f:
        f.write("metric\tvalue\n")
        for k, v in [
            ("d34_sites", len(sites)),
            ("flagged_sale", c2["sale"]),
            ("flagged_park", c2["park"]),
            ("flagged_host", c2["host"]),
            ("flagged_constr_kept", c2["constr"]),
            *([("flagged_sale_flag_kept", c2["sale_flag"])] if c2["sale_flag"] else []),
            ("dropped_sale_park_host", len(drop2)),
            ("d34_sites_after_filter", len(after)),
            ("r1_d34_sites_after_filter", after1),
            ("delta_vs_r1", len(after) - after1),
        ]:
            f.write(f"{k}\t{v}\n")
        print(open(r2d / "release_count_after_filter.tsv").read())
    files = ["flagged_sites.tsv", "filter_by_source.tsv", "canonical_sites_after_filter.txt", "release_count_after_filter.tsv",
             "delta_by_category.tsv", "delta_by_source.tsv", "flagged_site_hosts.tsv", "sample_found_hosts.tsv"]
    with open(r2d / "SHA256SUMS.txt", "w") as f:
        for fn in files:
            f.write(f"{sha(r2d / fn)}  {fn}\n")
    print(open(r2d / "SHA256SUMS.txt").read())


if __name__ == "__main__":
    main()
