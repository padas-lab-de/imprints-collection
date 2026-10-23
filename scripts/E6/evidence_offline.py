"""Evaluate the imprint-evidence check offline on the E6 output (no network).

Usage: python scripts/E6/evidence_offline.py [dataset.jsonl.gz]
"""

import collections
import gzip
import json
import sys

from ic.utils.imprint_utils import has_imprint_evidence

R = "/home/dinzinger/GitHub/imprints-collection/"
path = sys.argv[1] if len(sys.argv) > 1 else R + "datasets/E6/random20k/imprints_batch000000.jsonl.gz"
stats = collections.defaultdict(lambda: [0, 0])
verdict = {}
with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        i = r.get("impressum")
        if not i:
            continue
        ok = has_imprint_evidence(i["main_content"])
        route = f"{i['found_by']}:{'impressum' if i['found_keyword'] in ('impressum','/impressum','/impressum.html') else i['found_keyword']}{'+fullbody' if i['fallback_extraction'] else ''}"
        stats[route][0] += 1
        stats[route][1] += ok
        verdict[r["host"]] = ok
for k, (n, ok) in sorted(stats.items(), key=lambda kv: -kv[1][0]):
    print(f"{k:35} n={n:6} evidence={ok:6} ({ok/n:.1%})")

sample = R + "results/E6/precision_sample.jsonl"
try:
    rows = [json.loads(l) for l in open(sample)]
except FileNotFoundError:
    rows = []
bad = [r for r in rows if r["judgement"] == "bad"]
good = [r for r in rows if r["judgement"] != "bad"]
print("E6 bad hosts with evidence (would stay):", [r["host"] for r in bad if verdict.get(r["host"])])
print("E6 good hosts without evidence (would be lost):", [r["host"] for r in good if not verdict.get(r["host"], True)])
