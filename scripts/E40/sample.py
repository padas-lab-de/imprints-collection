#!/usr/bin/env python3
"""E40 precision/recall sample. Usage: sample.py --out OUTDIR --scan FILE... [--seed 40]

Reads OUTDIR/flagged_sites.tsv (from `parking_filter.py apply`) and the scan rows. Writes OUTDIR/sample_items.tsv:
  flagged_core  60 random flagged sites with category sale/park (seed), text from the F row of a host of the site
  flagged_ext   30 random flagged sites with category host/constr
  flagged_host  20 random flagged sites with category host (drawn last)
  unflagged     60 random hosts from the md5 sample rows (S) whose page is not text-flagged and whose
                www-collapsed name is not a flagged site
S hosts that are not imprint_found are ignored (the scan sees all records of a dir).
Columns: id, group, site_or_host, category, label_pattern, final_url, title, context_or_head, content_len, label, note
The columns label/note are filled by hand afterwards.
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parking_filter as pf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scan", nargs="+", required=True)
    ap.add_argument("--seed", type=int, default=40)
    ap.add_argument("--e31-in", required=True, help="E31 input dir (manifest.tsv + TSVs): the sample is restricted to imprint_found hosts")
    a = ap.parse_args()
    out = Path(a.out)
    flagged_hosts, samples, _ = pf.load_scan(a.scan)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E31"))
    import release_count as rc

    crawled, found = set(), {}
    for _, paths in rc.load_manifest(a.e31_in).items():
        found.update({h: t for h, t in rc.read_source(paths, crawled)[1].items() if h not in found})
    sites = [l.rstrip("\n").split("\t") for l in open(out / "flagged_sites.tsv")][1:]
    site_cat = {s[0]: s[1] for s in sites}
    by_site = {}
    for h, v in flagged_hosts.items():
        by_site.setdefault(pf.collapse(h), v)
        fh = pf.collapse(pf.urlsplit(v[2]).hostname or "")
        by_site.setdefault(fh, v)
    rng = random.Random(a.seed)
    rows = []

    def pick(group, cats, n):
        pool = sorted(s for s, c in site_cat.items() if c in cats)
        for s in rng.sample(pool, min(n, len(pool))):
            v = by_site.get(s)
            rows.append([group, s, site_cat[s], v[1] if v else "(target)", v[2] if v else "", v[3] if v else "", v[4] if v else ""] + [""])

    pick("flagged_core", ("sale", "park"), 60)
    pick("flagged_ext", ("host", "constr"), 30)
    pool = sorted(
        h for h, c in samples.items()
        if h in found and not c[2] and rc.canonical(h, found[h], crawled) not in site_cat and h not in flagged_hosts
    )
    stats = dict(s_found=sum(h in found for h in samples), s_found_flagged=sum(h in found and h in flagged_hosts for h in samples))
    print(stats)
    for h in rng.sample(pool, min(60, len(pool))):
        c = samples[h]
        rows.append(["unflagged", h, "", "", c[4], c[5], c[7] + " || " + c[9]] + [c[8]])
    pick("flagged_host", ("host",), 20)  # last, so the earlier groups keep their draws
    with open(out / "sample_items.tsv", "w") as f:
        f.write("id\tgroup\tsite_or_host\tcategory\tlabel_pattern\tfinal_url\ttitle\tcontext_or_head\tcontent_len\tlabel\tnote\n")
        for i, r in enumerate(rows):
            f.write("\t".join([str(i)] + r[:7] + [r[7], "", ""]) + "\n")
    print(len(rows), "items; unflagged pool", len(pool))


if __name__ == "__main__":
    main()
