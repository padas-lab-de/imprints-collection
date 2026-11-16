#!/usr/bin/env python3
"""Write the final site list after the parking filter, a summary, comparison tables and SHA256SUMS.txt.

Usage: write_final_site_list.py --sites SITES_DIR/canonical_sites.txt --filter FILTER_DIR [--earlier EARLIER_DIR]
  FILTER_DIR: output of `filter_parking_domains.py apply` (flagged_sites.tsv, filter_by_source.tsv, ...).
  EARLIER_DIR: the same two files from the first version of the filter (in the data package). Used only
  for the comparison columns and tables; without it they compare with an empty earlier result.

Writes into FILTER_DIR: canonical_sites_after_filter.txt (canonical sites minus the sale, park and host
sites; sorted), release_count_after_filter.tsv, delta_by_category.tsv, delta_by_source.tsv, SHA256SUMS.txt.
In these files first_version = the earlier filter version and final = this filter.

Categories constr and sale_flag are kept (not in DROP). sale_flag rows are written only when such sites
exist.
"""

import argparse
import hashlib
import sys
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
    ap.add_argument("--filter", dest="filter_dir", required=True, help="output dir of filter_parking_domains.py apply")
    ap.add_argument("--earlier", help="output dir of the first filter version (for the comparison tables)")
    a = ap.parse_args()
    earlier_dir, out_dir = (Path(a.earlier) if a.earlier else None), Path(a.filter_dir)
    sites = [l.rstrip("\n") for l in open(a.sites)]
    f1 = flagged(earlier_dir / "flagged_sites.tsv") if earlier_dir else {}
    f2 = flagged(out_dir / "flagged_sites.tsv")
    drop1 = {s for s, c in f1.items() if c in DROP}
    drop2 = {s for s, c in f2.items() if c in DROP}
    after = sorted(set(sites) - drop2)
    with open(out_dir / "canonical_sites_after_filter.txt", "w") as f:
        f.write("".join(s + "\n" for s in after))
    after1 = len(set(sites) - drop1)
    c1, c2 = Counter(f1.values()), Counter(f2.values())
    # category changes per site: earlier filter -> this filter
    trans = Counter((f1.get(s, "-"), f2.get(s, "-")) for s in set(f1) | set(f2) if f1.get(s) != f2.get(s))
    with open(out_dir / "delta_by_category.tsv", "w") as f:
        f.write("category\tfirst_version_sites\tfinal_sites\tdelta\n")
        for c in CATS + tuple(c for c in KEPT_EXTRA if c1[c] or c2[c]):
            f.write(f"{c}\t{c1[c]}\t{c2[c]}\t{c2[c] - c1[c]}\n")
        f.write(f"drop_total(sale+park+host)\t{len(drop1)}\t{len(drop2)}\t{len(drop2) - len(drop1)}\n")
        f.write(f"sites_after_filter\t{after1}\t{len(after)}\t{len(after) - after1}\n")
        f.write(f"dropped_by_first_version_only\t{len(drop1 - drop2)}\t\t\n")
        f.write("\ntransition_first_version_to_final\tsites\n")
        for (x, y), n in sorted(trans.items(), key=lambda t: -t[1]):
            f.write(f"{x}->{y}\t{n}\n")
    s1 = by_source(earlier_dir / "filter_by_source.tsv") if earlier_dir else []
    s2 = by_source(out_dir / "filter_by_source.tsv")
    # This filter may have sources that the earlier one lacks, and new_sites of an older source can shift by a
    # few sites (a newly crawled host becomes a redirect target). Rows are matched by source name; a source
    # missing in the earlier result gets zeros; a new_sites mismatch is reported on stderr, not an error.
    s1 = {r["source"]: r for r in s1}
    zero = dict(new_sites="0", sale="0", park="0", host="0", constr="0")
    pairs = []
    for y in s2:
        x = s1.get(y["source"])
        if x is None:
            print(f"note: source {y['source']} not in the earlier filter result, its values = 0", file=sys.stderr)
            x = dict(zero, source=y["source"])
        elif x["new_sites"] != y["new_sites"]:
            print(f"note: {y['source']} new sites: earlier {x['new_sites']}, now {y['new_sites']}", file=sys.stderr)
        pairs.append((x, y))
    cols = ["new_sites", "flagged_all", "sale", "park", "host", "constr", "new_sites_after_all"]
    with open(out_dir / "delta_by_source.tsv", "w") as f:
        f.write("source\tnew_sites\tfirst_version_after_drop\tfinal_after_drop\tadded_drops\tadded_sale\tadded_park\tadded_host\tadded_constr\n")
        for x, y in pairs:
            d = {c: int(y[c]) - int(x[c]) for c in ("sale", "park", "host", "constr")}
            first_after = int(x["new_sites"]) - int(x["sale"]) - int(x["park"]) - int(x["host"])
            final_after = int(y["new_sites"]) - int(y["sale"]) - int(y["park"]) - int(y["host"])
            f.write("\t".join(map(str, [x["source"], x["new_sites"], first_after, final_after, first_after - final_after, d["sale"], d["park"], d["host"], d["constr"]])) + "\n")
    with open(out_dir / "release_count_after_filter.tsv", "w") as f:
        f.write("metric\tvalue\n")
        for k, v in [
            ("sites", len(sites)),
            ("flagged_sale", c2["sale"]),
            ("flagged_park", c2["park"]),
            ("flagged_host", c2["host"]),
            ("flagged_constr_kept", c2["constr"]),
            *([("flagged_sale_flag_kept", c2["sale_flag"])] if c2["sale_flag"] else []),
            ("dropped_sale_park_host", len(drop2)),
            ("sites_after_filter", len(after)),
            ("first_version_sites_after_filter", after1),
            ("delta_vs_first_version", len(after) - after1),
        ]:
            f.write(f"{k}\t{v}\n")
        print(open(out_dir / "release_count_after_filter.tsv").read())
    files = ["flagged_sites.tsv", "filter_by_source.tsv", "canonical_sites_after_filter.txt", "release_count_after_filter.tsv",
             "delta_by_category.tsv", "delta_by_source.tsv", "flagged_site_hosts.tsv", "sample_found_hosts.tsv"]
    with open(out_dir / "SHA256SUMS.txt", "w") as f:
        for fn in files:
            f.write(f"{sha(out_dir / fn)}  {fn}\n")
    print(open(out_dir / "SHA256SUMS.txt").read())


if __name__ == "__main__":
    main()
