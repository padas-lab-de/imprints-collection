#!/usr/bin/env python3
"""E40 round 2: precision sample of the sites that only r2 drops, miss sample of kept sites, and a re-check of the
round-1 hand labels. Read-only on the inputs; writes the label sheets (column `label` empty) to --out.

Usage: sample_r2.py --r1-flagged R1/flagged_sites.tsv --r2-dir R2 --scan R2/scan/*.scan.tsv
                    --r1-labels E40/sample_labeled.tsv --out R2/labels [--seed 49] [--per-cat 20] [--n-miss 60]

R2 is the `parking_filter.py apply` output dir of round 2 (flagged_sites.tsv, flagged_site_hosts.tsv,
sample_found_hosts.tsv). Drop categories: sale, park, host (constr is kept).
"""

import argparse
import csv
import random
from pathlib import Path

DROP = ("sale", "park", "host")


def read_tsv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def load_rows(paths):
    """-> ({host: F row}, {host: S row}) from scan files (r2 F rows may carry r1_cat, r1_label, desc, clen, head)."""
    F, S = {}, {}
    for p in paths:
        with open(p, encoding="utf-8", newline="") as f:
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) >= 7 and c[1] == "F":
                    F[c[0]] = c
                elif len(c) >= 7 and c[1] == "S":
                    S[c[0]] = c
    return F, S


def excerpt(row):
    """judged text: title | ctx | desc | head (whatever the row has)."""
    parts = [row[5], row[6]] + (row[9:10] + row[11:12] if row[1] == "F" else row[7:8] + row[9:10])
    return " || ".join(p for p in parts if p)[:900]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r1-flagged", required=True)
    ap.add_argument("--r2-dir", required=True)
    ap.add_argument("--scan", nargs="+", required=True)
    ap.add_argument("--r1-labels", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=49)
    ap.add_argument("--per-cat", type=int, default=20)
    ap.add_argument("--n-miss", type=int, default=60)
    a = ap.parse_args()
    r2 = Path(a.r2_dir)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(a.seed)
    r1 = {r["site"]: r["category"] for r in read_tsv(a.r1_flagged)}
    r2f = {r["site"]: r["category"] for r in read_tsv(r2 / "flagged_sites.tsv")}
    hosts = {}
    for r in read_tsv(r2 / "flagged_site_hosts.tsv"):
        hosts.setdefault(r["site"], []).append(r)
    F, S = load_rows(a.scan)
    head = ["id", "group", "site", "host", "r2_category", "r2_label", "r1_category", "final_url", "content_len", "excerpt", "label", "note"]

    # 1) precision: sites dropped by r1+r2 but not by r1 alone, per r2 category
    only = {}
    for s, c in r2f.items():
        if c in DROP and r1.get(s) not in DROP:
            only.setdefault(c, []).append(s)
    rows = []
    for c in DROP:
        pool = sorted(only.get(c, []))
        for s in rnd.sample(pool, min(a.per_cat, len(pool))):
            hs = [h for h in hosts.get(s, []) if h["host_label"].startswith("r2_")] or hosts.get(s, [])
            h = hs[0]["host"] if hs else s
            fr = F.get(h)
            if fr:
                rows.append([s, h, c, fr[3], r1.get(s, ""), fr[4], fr[10] if len(fr) > 10 else "", excerpt(fr)])
            else:  # site flagged as a parking target (no text row)
                rows.append([s, h, c, "target", r1.get(s, ""), "", "", ""])
    with open(out / "precision_r2only.tsv", "w", encoding="utf-8") as f:
        f.write("\t".join(head) + "\n")
        for i, r in enumerate(rows):
            f.write("\t".join([str(i), "r2only_" + r[2], *r, "", ""]) + "\n")
    with open(out / "r2only_counts.tsv", "w") as f:
        f.write("category\tr2only_sites\tsampled\n")
        for c in DROP:
            f.write(f"{c}\t{len(only.get(c, []))}\t{min(a.per_cat, len(only.get(c, [])))}\n")

    # 2) misses: md5-sample found hosts whose site is kept (not dropped by r1+r2)
    pool = sorted((r["host"], r["site"], r["site_category"]) for r in read_tsv(r2 / "sample_found_hosts.tsv") if r["site_category"] not in DROP and r["host"] in S)
    seen, cand = set(), []
    for h, s, c in pool:  # one host per site
        if s not in seen:
            seen.add(s)
            cand.append((h, s, c))
    with open(out / "miss_kept.tsv", "w", encoding="utf-8") as f:
        f.write("\t".join(head) + "\n")
        for i, (h, s, c) in enumerate(rnd.sample(cand, min(a.n_miss, len(cand)))):
            sr = S[h]
            f.write("\t".join([str(i), "kept", s, h, c, sr[3], r1.get(s, ""), sr[4], sr[8] if len(sr) > 8 else "", excerpt(sr), "", ""]) + "\n")
    print(f"r2only {dict((c, len(v)) for c, v in only.items())} miss_pool {len(cand)}")

    # 3) round-1 hand labels: category under r1 and under r1+r2 (site rows: site category; host rows: host row)
    with open(out / "r1_labels_recheck.tsv", "w", encoding="utf-8") as f:
        f.write("id\tgroup\tsite_or_host\tr1_label\tr1_category\tr2_site_category\tr2_host_category\tr2_host_label\tchanged\n")
        for r in read_tsv(a.r1_labels):
            k = r["site_or_host"]
            sc = r2f.get(k, "")
            fr = F.get(k) or F.get("www." + k)
            hc, hl = (fr[2], fr[3]) if fr else ("", "")
            new = sc or hc
            changed = int((new in DROP) != (r["category"] in DROP) or (bool(new) != bool(r["category"])))
            f.write("\t".join([r["id"], r["group"], k, r["label"], r["category"], sc, hc, hl, str(changed)]) + "\n")


if __name__ == "__main__":
    main()
