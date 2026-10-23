"""E10: DACH-address yield of the E9 seed-list run (same strict detector as analyze.py), plus yield by in-degree in the expansion set.
Usage: PYTHONPATH=src python scripts/E10/seed_dach_yield.py
"""
import gzip
import json
import importlib.util
import sys
from collections import Counter

spec = importlib.util.spec_from_file_location("an", "scripts/E10/analyze_lib.py")
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)

R = "/home/dinzinger/GitHub/imprints-collection/"
tot = Counter()
with gzip.open(R + "datasets/E9/random20k/imprints_batch000000.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        g = an.grp(r["host"])
        tot["reach"] += 1
        i = r.get("impressum")
        if i:
            tot["found"] += 1
            if an.dach_country(i.get("main_content", "")):
                tot["dach"] += 1
                tot["dach_" + ("dachtld" if g in ("de", "at", "ch") else "other")] += 1
print("E9 seed run, 20,000 fetched:", dict(tot))
print(f"DACH-address imprints per 1,000 fetched: {1000*tot['dach']/20000:.0f}")

# Expansion: yield by number of seeds linking to the host
occ = {l.split("\t")[0]: int(l.split("\t")[1]) for l in open(R + "results/E10/e9_new_occurrences.tsv")}
c = {1: [0, 0, 0], 2: [0, 0, 0]}
with gzip.open(R + "datasets/E10/expansion/imprints_batch000000.jsonl.gz", "rt", encoding="utf-8") as f:
    seen = {}
    for line in f:
        r = json.loads(line)
        seen[r["host"]] = r
for h in (l.strip() for l in open(R + "datasets/E10/candidate_hosts.txt")):
    k = 1 if occ.get(h, 1) == 1 else 2
    c[k][0] += 1
    r = seen.get(h)
    if r and r.get("impressum"):
        c[k][1] += 1
        c[k][2] += an.dach_country(r["impressum"].get("main_content", "")) is not None
print("by in-degree (1 seed vs >=2 seeds; hosts only in E4 file count as 1): [fetched, found, dach]", c)
