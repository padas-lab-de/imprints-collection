#!/usr/bin/env python3
"""E31 release count: unique imprint sites over all crawl sources with the D34 rule.

Usage: release_count.py --in INDIR --out OUTDIR      (INDIR from pull.py: manifest.tsv + <vm>_<source>_<sub>.tsv)

Per source (manifest order; files of a source in manifest order): the status of a host is its LAST
complete row (ic fetch resume rule, as scripts/E22/dedup_count.py). A host counts as imprint_found if its
last row says so; its redirect target is the target of that last row.

Three counts over the union of all sources:
  exact   distinct imprint_found hosts (lowercased)
  www     distinct hosts after www.x -> x (old method)
  d34     distinct canonical sites (D34): t = host of main.url after redirects. If www-collapsed t is a
          crawled host (any row of any source, www-collapsed), the site is collapse(t); else collapse(h).
"new" per source = items not present in any earlier source (same measure).

  d34f    variant of d34: a host folds into its redirect target only if the target (www-collapsed) is itself
          imprint_found in some source (canonical_sites_found_only.txt). d34 stays the primary count.

Writes OUTDIR/release_count.tsv, release_stats.tsv, canonical_sites.txt (sorted), redirect_cases.tsv.
"""

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path


def collapse(h):
    return h[4:] if h.startswith("www.") else h


def canonical(host, target, crawled_collapsed):
    """D34 canonical site of a found host. crawled_collapsed: set of www-collapsed crawled hosts.

    Variant (open doubt of E31): pass the set of www-collapsed imprint_found hosts instead; a host then
    folds into its redirect target only if the target is itself imprint_found."""
    if target:
        t = collapse(target)
        if t in crawled_collapsed:
            return t
    return collapse(host)


def read_source(paths, crawled_collapsed):
    """Last-row rule over files in order. Returns (n_hosts, {found host: target}); adds hosts to crawled_collapsed."""
    found, hosts = {}, set()
    for p in paths:
        with open(p, encoding="utf-8", newline="") as f:
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) != 3:
                    continue
                h, s, t = c
                hosts.add(h)
                if s == "imprint_found":
                    found[h] = t
                else:
                    found.pop(h, None)
    crawled_collapsed.update(collapse(h) for h in hosts)
    return len(hosts), found


def load_manifest(indir):
    rows = [l.rstrip("\n").split("\t") for l in open(Path(indir) / "manifest.tsv")]
    head, rows = rows[0], rows[1:]
    out = {}
    for r in rows:
        d = dict(zip(head, r))
        out.setdefault(d["source"], []).append(Path(indir) / d["file"])
    return out


def compute(sources):
    """sources: [(name, [paths])] -> (table rows, stats dict, canonical set, cases list)."""
    crawled, loaded = set(), []
    for name, paths in sources:  # first pass: all crawled hosts needed before any canonical form
        n, found = read_source(paths, crawled)
        loaded.append((name, len(paths), n, found))
    found_collapsed = {collapse(h) for _, _, _, f in loaded for h in f}
    cum = dict(exact=set(), www=set(), d34=set(), d34f=set())
    table, st, cases = [], Counter(), []
    first_seen = set()
    for name, nfiles, nhosts, found in loaded:
        ex = set(found)
        ww = {collapse(h) for h in ex}
        d3, d3f = set(), set()
        for h, t in found.items():
            c = canonical(h, t, crawled)
            d3.add(c)
            d3f.add(canonical(h, t, found_collapsed))
            if h in first_seen:
                continue
            first_seen.add(h)  # stats over distinct exact hosts, first source wins
            st["found_hosts"] += 1
            if not t:
                st["no_target"] += 1
                continue
            st["with_target"] += 1
            if t != h:
                st["target_differs_exact"] += 1
            if collapse(t) != collapse(h):
                st["target_differs_site"] += 1
                known = collapse(t) in crawled
                st["target_site_known"] += known
                st["target_site_unknown"] += not known
                if c != collapse(h):
                    st["changed_by_d34"] += 1
                cases.append((h, t, c, name, "known" if known else "unknown"))
        row = dict(
            source=name,
            files=nfiles,
            hosts=nhosts,
            imprint_found=len(ex),
            new_exact=len(ex - cum["exact"]),
            new_www=len(ww - cum["www"]),
            new_d34=len(d3 - cum["d34"]),
            new_d34f=len(d3f - cum["d34f"]),
        )
        cum["exact"] |= ex
        cum["www"] |= ww
        cum["d34"] |= d3
        cum["d34f"] |= d3f
        row.update(
            cum_exact=len(cum["exact"]), cum_www=len(cum["www"]), cum_d34=len(cum["d34"]), cum_d34f=len(cum["d34f"])
        )
        table.append(row)
    st["crawled_hosts_collapsed"] = len(crawled)
    total = dict(source="TOTAL", files=sum(r["files"] for r in table), hosts=sum(r["hosts"] for r in table))
    total.update(imprint_found=sum(r["imprint_found"] for r in table))
    for k in ("exact", "www", "d34", "d34f"):
        total["new_" + k] = total["cum_" + k] = len(cum[k])
    table.append(total)
    compute.d34f_sites = cum["d34f"]  # variant site set, written by main()
    return table, st, cum["d34"], cases


COLS = [
    "source",
    "files",
    "hosts",
    "imprint_found",
    "new_exact",
    "cum_exact",
    "new_www",
    "cum_www",
    "new_d34",
    "cum_d34",
    "new_d34f",
    "cum_d34f",
]


def pick(cases, n, key):
    return sorted(cases, key=lambda c: hashlib.md5((key + c[0]).encode()).hexdigest())[:n]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sources = list(load_manifest(a.indir).items())
    table, st, sites, cases = compute(sources)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    text = "\n".join(["\t".join(COLS)] + ["\t".join(str(r.get(c, "")) for c in COLS) for r in table]) + "\n"
    (out / "release_count.tsv").write_text(text)
    (out / "release_stats.tsv").write_text("".join(f"{k}\t{v}\n" for k, v in sorted(st.items())))
    (out / "canonical_sites.txt").write_text("".join(s + "\n" for s in sorted(sites)))
    (out / "canonical_sites_found_only.txt").write_text("".join(s + "\n" for s in sorted(compute.d34f_sites)))
    changed = [c for c in cases if c[2] != collapse(c[0])]
    keep = [c for c in cases if c[2] == collapse(c[0])]
    with open(out / "redirect_cases.tsv", "w") as f:
        f.write("kind\thost\ttarget\tcanonical\tsource\ttarget_site\n")
        for kind, cs in (("changed", pick(changed, 200, "c")), ("unchanged", pick(keep, 100, "u"))):
            for h, t, c, s, k in cs:
                f.write(f"{kind}\t{h}\t{t}\t{c}\t{s}\t{k}\n")
    print(text, end="")
    print("".join(f"{k}\t{v}\n" for k, v in sorted(st.items())), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
