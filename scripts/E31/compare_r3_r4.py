#!/usr/bin/env python3
"""E31 r4: check that every r3 D34 site is in r4 or explained, and write the site lists with sha256.

Usage: compare_r3_r4.py --in R4_INDIR --r3 R3_DIR --r4 R4_DIR --old-sources-file R3_MANIFEST
  R3_DIR / R4_DIR hold E31_out/canonical_sites.txt and E40_out/flagged_sites.tsv.
Re-computes the r3 host -> site map from the old sources of the r4 inputs (those named in R3_MANIFEST),
and checks that it reproduces r3/E31_out/canonical_sites.txt. For each r3 site missing in r4:
reason = the r4 site its found hosts moved to (target now a crawled host in a new source), counted by
whether that r4 site was an r3 site or is new. Writes R4_DIR/compare/{removed_sites.tsv, summary.tsv,
sha256.txt, canonical_sites_after_filter.txt}. Streams nothing clever: needs ~5 GB.
"""

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_count as rc


def sha(fn):
    h = hashlib.sha256()
    with open(fn, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def host_sites(sources):
    """{found host: canonical site} over the given sources (first source wins for a host seen twice, as the
    count does; hosts are not re-assigned), and the crawled set."""
    crawled, loaded = set(), []
    for name, paths in sources:
        loaded.append(rc.read_source(paths, crawled)[1])
    m = {}
    for found in loaded:
        for h, t in found.items():
            m.setdefault(h, set()).add(rc.canonical(h, t, crawled))
    return m


def flagged(fn, cats=("sale", "park", "host")):
    out = {}
    with open(fn) as f:
        next(f)
        for line in f:
            s, c = line.split("\t")[:2]
            if c in cats:
                out[s] = c
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--r3", required=True)
    ap.add_argument("--r4", required=True)
    ap.add_argument("--r3-manifest", required=True)
    a = ap.parse_args()
    r3, r4 = Path(a.r3), Path(a.r4)
    old = {l.split("\t")[0] for l in open(a.r3_manifest).read().splitlines()[1:]}
    allsrc = list(rc.load_manifest(a.indir).items())
    s3 = {l.rstrip("\n") for l in open(r3 / "E31_out/canonical_sites.txt")}
    s4 = {l.rstrip("\n") for l in open(r4 / "E31_out/canonical_sites.txt")}
    m3 = host_sites([x for x in allsrc if x[0] in old])
    rebuilt = {s for v in m3.values() for s in v}
    print("r3 reproduced from old sources:", rebuilt == s3, len(rebuilt), len(s3))
    m4 = host_sites(allsrc)
    removed = sorted(s3 - s4)
    added = s4 - s3
    reasons, rows = Counter(), []
    host_of3 = {}
    for h, v in m3.items():
        for s in v:
            host_of3.setdefault(s, []).append(h)
    for s in removed:
        dest = set()
        for h in host_of3.get(s, ()):
            dest |= m4.get(h, set())
        dest.discard(s)
        if not dest:
            r = "no_destination"
        elif dest <= s3:
            r = "folded_into_r3_site"
        elif dest & s4 and not (dest & s3):
            r = "folded_into_new_site"
        else:
            r = "folded_mixed"
        reasons[r] += 1
        rows.append((s, r, ",".join(sorted(dest))[:200]))
    out = r4 / "compare"
    out.mkdir(exist_ok=True)
    with open(out / "removed_sites.tsv", "w") as f:
        f.write("r3_site\treason\tr4_destination\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    # after-filter lists
    f3, f4 = flagged(r3 / "E40_out/flagged_sites.tsv"), flagged(r4 / "E40_out/flagged_sites.tsv")
    a3, a4 = s3 - set(f3), s4 - set(f4)
    with open(out / "canonical_sites_after_filter.txt", "w") as f:
        f.write("".join(s + "\n" for s in sorted(a4)))
    rm_f = sorted(a3 - a4)
    c2 = Counter()
    for s in rm_f:
        if s not in s4:
            c2["removed_from_sites(fold)"] += 1
        elif s in f4:
            c2["now_flagged:" + f4[s]] += 1
        else:
            c2["other"] += 1
    summ = [
        ("r3_sites", len(s3)), ("r4_sites", len(s4)), ("r3_sites_in_r4", len(s3 & s4)), ("r3_sites_not_in_r4", len(removed)),
        ("r4_sites_not_in_r3", len(added)),
    ]
    summ += [("removed:" + k, v) for k, v in sorted(reasons.items())]
    summ += [("r3_after_filter", len(a3)), ("r4_after_filter", len(a4)), ("r3_after_filter_not_in_r4_after_filter", len(rm_f))]
    summ += [("afterfilter_removed:" + k, v) for k, v in sorted(c2.items())]
    summ += [("r3_flagged_sale_park_host", len(f3)), ("r4_flagged_sale_park_host", len(f4))]
    with open(out / "summary.tsv", "w") as f:
        for k, v in summ:
            f.write(f"{k}\t{v}\n")
            print(k, v)
    with open(out / "sha256.txt", "w") as f:
        for fn in [r4 / "E31_out/canonical_sites.txt", out / "canonical_sites_after_filter.txt"]:
            f.write(f"{sha(fn)}  {fn.relative_to(r4)}  lines={sum(1 for _ in open(fn))}\n")
    print(open(out / "sha256.txt").read())


if __name__ == "__main__":
    main()
