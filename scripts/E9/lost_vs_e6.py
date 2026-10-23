"""Which E6 routes lost their imprint in E9 (and how many hosts were just unreachable)."""

import collections
import gzip
import json

R = "/home/dinzinger/GitHub/imprints-collection/"


def load(p):
    return {json.loads(l)["host"]: json.loads(l) for l in gzip.open(R + p, "rt")}


e6 = load("datasets/E6/random20k/imprints_batch000000.jsonl.gz")
e9 = load("datasets/E9/random20k/imprints_batch000000.jsonl.gz")
c = collections.Counter()
for h in e6:
    if "impressum" in e6[h] and "impressum" not in e9.get(h, {}):
        if h not in e9:
            c["unreachable in E9"] += 1
            continue
        i = e6[h]["impressum"]
        c[f"{i['found_by']}:{i['found_keyword']}{'+fullbody' if i['fallback_extraction'] else ''}"] += 1
for k, v in c.most_common():
    print(v, k)
print(sum(c.values()))
