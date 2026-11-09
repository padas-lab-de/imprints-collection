#!/usr/bin/env python3
"""E40 r2: extra precision strata for the small r2 rules, which the random r2-only sample (dominated by the
kv-gmbh, united-domains and IONOS templates) does not reach. Per stratum: up to N random r2-only sites (seed 49)
whose deciding host row matches the stratum.

Strata: r2_name_for_sale, r2_park_phrase, r2_host_phrase, sale_template_other (r2_sale_template rows without
"am Kauf der Domain"), park_template_other (r2_park_template rows without "Kundenauftrag" and without "bereits ...
registriert").

Usage: sample_r2_strata.py --r1-flagged R1/flagged_sites.tsv --r2-dir R2 --scan R2/scan/*.scan.tsv --out OUT.tsv [--n 20]
"""

import argparse
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_r2 import DROP, excerpt, load_rows, read_tsv  # noqa: E402

KV = re.compile(r"am\s+kauf\s+der\s+domain", re.I)
PARK_BIG = re.compile(r"kundenauftrag|diese\s+domain\s+ist\s+bereits\s+(?:bei\s+\S+\s+)?registriert", re.I)


def stratum(row):
    lab = row[3]
    text = "\n".join([row[5], row[6]] + row[9:10] + row[11:12])
    if lab in ("r2_name_for_sale", "r2_park_phrase", "r2_host_phrase"):
        return lab
    if lab == "r2_sale_template" and not KV.search(text):
        return "sale_template_other"
    if lab == "r2_park_template" and not PARK_BIG.search(text):
        return "park_template_other"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r1-flagged", required=True)
    ap.add_argument("--r2-dir", required=True)
    ap.add_argument("--scan", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=49)
    a = ap.parse_args()
    r2 = Path(a.r2_dir)
    r1 = {r["site"]: r["category"] for r in read_tsv(a.r1_flagged)}
    F, _ = load_rows(a.scan)
    pools = {}
    for r in read_tsv(r2 / "flagged_site_hosts.tsv"):
        s = r["site"]
        if r["site_category"] not in DROP or r1.get(s) in DROP or not r["host_label"].startswith("r2_"):
            continue
        fr = F.get(r["host"])
        st = stratum(fr) if fr else None
        if st:
            pools.setdefault(st, {}).setdefault(s, (r["host"], r["site_category"], fr))
    rnd = random.Random(a.seed)
    head = ["id", "group", "site", "host", "r2_category", "r2_label", "r1_category", "final_url", "content_len", "excerpt", "label", "note"]
    i = 0
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\t".join(head) + "\n")
        for st in sorted(pools):
            sites = sorted(pools[st])
            print(st, len(sites))
            for s in rnd.sample(sites, min(a.n, len(sites))):
                h, c, fr = pools[st][s]
                f.write("\t".join([str(i), st, s, h, c, fr[3], r1.get(s, ""), fr[4], fr[10] if len(fr) > 10 else "", excerpt(fr), "", ""]) + "\n")
                i += 1


if __name__ == "__main__":
    main()
