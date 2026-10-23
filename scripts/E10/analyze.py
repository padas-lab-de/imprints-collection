"""E10 analysis: yield per TLD, DACH address share, filter comparison, full-round estimate.

Usage: python scripts/E10/analyze.py > results/E10/analysis.txt
Reads datasets/E10/expansion/imprints_batch000000.jsonl.gz and the candidate files under
results/E10/. Needs PYTHONPATH=src (imports ic.utils.imprint_utils).
"""
import gzip
import json
import math
import random
import re
from collections import Counter, defaultdict

from ic.utils.imprint_utils import _POSTCODE_RE, has_imprint_evidence

R = "/home/dinzinger/GitHub/imprints-collection/"
OUT = R + "datasets/E10/expansion/imprints_batch000000.jsonl.gz"
cands = [l.strip() for l in open(R + "datasets/E10/candidate_hosts.txt") if l.strip()]

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_lib import dach_country, wilson, grp

recs = {}
with gzip.open(OUT, "rt", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        recs[r["host"]] = r
print(f"candidates {len(cands)}, reachable records {len(recs)} ({len(recs)/len(cands):.1%})")
print("hosts in output not in candidates:", len(set(recs) - set(cands)))

rows = []
for h in cands:
    r = recs.get(h)
    imp = r.get("impressum") if r else None
    text = imp.get("main_content", "") if imp else ""
    rows.append({
        "host": h, "g": grp(h), "tld": h.rsplit(".", 1)[-1],
        "reach": r is not None, "imp": imp is not None,
        "loose": bool(imp) and bool(_POSTCODE_RE.search(text)),
        "dach": dach_country(text) if imp else None,
        "len": len(text),
    })

order = ["de", "at", "ch", "eu", "com", "net", "org", "other"]
print("\n== Per TLD group ==")
print("| TLD | fetched | reachable | imprint found | found/reachable | found/fetched | loose postcode+town | strict DACH address | strict/found |")
print("|---|---|---|---|---|---|---|---|---|")
def line(label, rs):
    n = len(rs); re_ = sum(x["reach"] for x in rs); f = sum(x["imp"] for x in rs)
    lo = sum(x["loose"] for x in rs); st = sum(x["dach"] is not None for x in rs)
    if n == 0:
        return
    print(f"| {label} | {n} | {re_} ({re_/n:.1%}) | {f} | {f/max(re_,1):.1%} | {f/n:.1%} | {lo} ({lo/max(f,1):.1%}) | {st} | {st/max(f,1):.1%} |")
for g in order:
    line("." + g if g != "other" else "other", [x for x in rows if x["g"] == g])
line("**all**", rows)
dach_tld = [x for x in rows if x["g"] in ("de", "at", "ch")]
non_dach = [x for x in rows if x["g"] not in ("de", "at", "ch")]
line("de/at/ch", dach_tld)
line("not de/at/ch", non_dach)

print("\nStrict DACH country split of found imprints by group:")
for g in order:
    c = Counter(x["dach"] for x in rows if x["g"] == g and x["imp"])
    print(g, dict(c))

print("\nTop 'other' TLDs: found/reachable/fetched")
t = defaultdict(lambda: [0, 0, 0, 0])
for x in rows:
    if x["g"] == "other":
        a = t[x["tld"]]; a[0] += 1; a[1] += x["reach"]; a[2] += x["imp"]; a[3] += x["dach"] is not None
for k, v in sorted(t.items(), key=lambda kv: -kv[1][0])[:15]:
    print(f"  .{k}: fetched {v[0]} reachable {v[1]} found {v[2]} strict-DACH {v[3]}")

print("\n== Filter comparison (yield per 1,000 fetched hosts) ==")
n_all = len(rows)
dach_all = sum(x["dach"] is not None for x in rows)
dach_in_tld = sum(x["dach"] is not None for x in dach_tld)
found_in_tld = sum(x["imp"] for x in dach_tld)
dach_outside = dach_all - dach_in_tld
def y(k, n):
    lo, hi = wilson(k, n)
    return f"{1000*k/n:.0f} (CI {1000*lo:.0f}-{1000*hi:.0f})"
print("| Filter | hosts fetched | imprints found | DACH-address imprints | DACH imprints / 1,000 fetched | share of all DACH-address imprints captured |")
print("|---|---|---|---|---|---|")
print(f"| (a) ccTLD .de/.at/.ch only (fetch only these) | {len(dach_tld)} | {found_in_tld} | {dach_in_tld} | {y(dach_in_tld, len(dach_tld))} | {dach_in_tld/dach_all:.1%} |")
print(f"| (b) any TLD, keep imprints with DACH address (must fetch all) | {n_all} | {sum(x['imp'] for x in rows)} | {dach_all} | {y(dach_all, n_all)} | 100% |")
print(f"| (c) = (a) as fetch filter + (b) as keep filter on the rest (fetch all, keep ccTLD or DACH address) | {n_all} | | {dach_all} | {y(dach_all, n_all)} | 100% |")
tld_imp_nonaddr = sum(1 for x in dach_tld if x["imp"] and x["dach"] is None)
print(f"\nDACH-ccTLD imprints without strict DACH address: {tld_imp_nonaddr} of {found_in_tld}")
print(f"Non-DACH-ccTLD hosts: fetched {len(non_dach)}, strict-DACH imprints {dach_outside} -> {y(dach_outside, len(non_dach))} per 1,000")
print(f"Marginal: fetching the non-DACH-TLD hosts adds {dach_outside} DACH-address imprints ({dach_outside/dach_all:.1%} of all) for {len(non_dach)/n_all:.1%} of fetch cost")
print("Strict-DACH imprints outside de/at/ch by TLD:", Counter(x["tld"] for x in non_dach if x["dach"]).most_common(12))

# Per-1,000 for pre-fetch variants: by TLD group (which groups pay off)
print("\nDACH imprints per 1,000 fetched by group:")
for g in order:
    rs = [x for x in rows if x["g"] == g]
    k = sum(x["dach"] is not None for x in rs)
    print(f"  .{g}: {k}/{len(rs)} -> {y(k, len(rs))}")

# Sample of non-DACH-TLD strict positives for manual precision check
random.seed(20261023)
pos = sorted(x["host"] for x in non_dach if x["dach"])
smp = random.sample(pos, min(30, len(pos)))
with open(R + "results/E10/nondach_tld_dach_sample.jsonl", "w") as f:
    for h in smp:
        i = recs[h]["impressum"]
        f.write(json.dumps({"host": h, "url": i["url"], "country": dach_country(i["main_content"]),
                            "text": i["main_content"][:600]}, ensure_ascii=False) + "\n")
random.seed(20261023)
pos2 = sorted(x["host"] for x in dach_tld if x["imp"] and x["dach"] is None)
smp2 = random.sample(pos2, min(30, len(pos2)))
with open(R + "results/E10/dachtld_noaddr_sample.jsonl", "w") as f:
    for h in smp2:
        i = recs[h]["impressum"]
        f.write(json.dumps({"host": h, "url": i["url"], "text": i["main_content"][:600]}, ensure_ascii=False) + "\n")

# Seed-list comparison (E9)
print("\n== Seed list (E9, 20k random seeds) ==")
print("imprint found / reachable: 10,246 / 16,129 = 63.5%; .de 7,444 / 8,904 = 83.6%; found / fetched = 51.2%")
f_all = sum(x["imp"] for x in rows); re_all = sum(x["reach"] for x in rows)
print(f"expansion: found / reachable = {f_all}/{re_all} = {f_all/re_all:.1%}; found / fetched = {f_all/n_all:.1%}")
de = [x for x in rows if x["g"] == "de"]
print(f".de expansion: {sum(x['imp'] for x in de)}/{sum(x['reach'] for x in de)} = {sum(x['imp'] for x in de)/max(sum(x['reach'] for x in de),1):.1%}")

# Full-round estimate
print("\n== Full-round estimate ==")
occ = [(l.split("\t")[0], int(l.split("\t")[1])) for l in open(R + "results/E10/e9_new_occurrences.tsv")]
n_new = len(occ)
SEEDS_SAMPLE, SEEDS_ALL = 20000, 6_560_119
print(f"E9 new non-platform hosts: {n_new} from {SEEDS_SAMPLE} seeds = {n_new/SEEDS_SAMPLE:.4f} per seed (linear upper scale-up {n_new/SEEDS_SAMPLE*SEEDS_ALL:,.0f})")
cnt = Counter(c for _, c in occ)
singles = cnt[1]; doubles = cnt[2]
chao1 = n_new + singles * singles / (2 * max(doubles, 1))
print(f"occurrence counts: singletons {singles}, doubletons {doubles}, >=3 {n_new-singles-doubles}; Chao1 total new hosts reachable from these links ~{chao1:,.0f} (lower bound of the new-host pool at this seed size)")
# rarefaction over occurrences
lines = [h for h, c in occ for _ in range(c)]
random.seed(1)
random.shuffle(lines)
pts = []
for frac in (0.0625, 0.125, 0.25, 0.5, 1.0):
    m = int(len(lines) * frac)
    pts.append((SEEDS_SAMPLE * frac, len(set(lines[:m]))))
print("rarefaction (seeds, unique new hosts):", [(int(a), b) for a, b in pts])
xs = [math.log(a) for a, _ in pts]; ys = [math.log(b) for _, b in pts]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
beta = sum((x - mx) * (y_ - my) for x, y_ in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
k = math.exp(my - beta * mx)
print(f"Heaps fit U = {k:.3f} * N^{beta:.3f}")
u_heaps = k * SEEDS_ALL ** beta
print(f"Heaps extrapolation to {SEEDS_ALL:,} seeds: {u_heaps:,.0f} unique new hosts")
print(f"Occurrence-weighted total (linear in occurrences): {sum(c for _, c in occ)/SEEDS_SAMPLE*SEEDS_ALL:,.0f} link occurrences to new hosts")
dach_rate = dach_all / n_all
lo, hi = wilson(dach_all, n_all)
print(f"DACH-address imprint yield per fetched candidate: {dach_all}/{n_all} = {dach_rate:.4f} (CI {lo:.4f}-{hi:.4f})")
print(f"(a) yield {dach_in_tld}/{len(dach_tld)} = {dach_in_tld/len(dach_tld):.4f}; share of new hosts in de/at/ch: {len(dach_tld)/n_all:.3f}")
for label, U in (("Heaps", u_heaps), ("linear", n_new / SEEDS_SAMPLE * SEEDS_ALL)):
    print(f"{label}: new hosts {U:,.0f}; DACH imprints (b/c) {U*dach_rate:,.0f} (CI {U*lo:,.0f}-{U*hi:,.0f}); (a) fetch {U*len(dach_tld)/n_all:,.0f} hosts -> {U*dach_in_tld/n_all:,.0f}")
