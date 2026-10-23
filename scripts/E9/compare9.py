"""E9 comparison: yield vs E4 and E6, E6 precision-sample hosts, E5 recovery, new sample.

Usage: python scripts/E9/compare9.py   (writes results/E9/sample.json)
"""

import collections
import gzip
import json
import random

R = "/home/dinzinger/GitHub/imprints-collection/"
P = "datasets/%s/random20k/imprints_batch000000.jsonl.gz"


def load(p):
    d = {}
    with gzip.open(R + p, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            d[r["host"]] = r
    return d


e4, e6, e9 = load(P % "E4"), load(P % "E6"), load(P % "E9")
is_de = lambda h: h.endswith(".de")
found = lambda d, h: h in d and "impressum" in d[h]


def yield_(d, sel):
    hs = [h for h in d if sel(h)]
    return sum("impressum" in d[h] for h in hs), len(hs)


for name, d in (("E4", e4), ("E6", e6), ("E9", e9)):
    for label, sel in (("all", lambda h: True), (".de", is_de)):
        f, n = yield_(d, sel)
        print(f"{name} {label}: {f}/{n} = {f/n:.1%}")

gained4 = sorted(h for h in e9 if found(e9, h) and not found(e4, h))
lost4 = sorted(h for h in e4 if found(e4, h) and not found(e9, h))
print("E9 vs E4: gained", len(gained4), "(.de", sum(map(is_de, gained4)), ") lost", len(lost4))
gained6 = sorted(h for h in e9 if found(e9, h) and not found(e6, h))
lost6 = sorted(h for h in e6 if found(e6, h) and not found(e9, h))
print("E9 vs E6: gained", len(gained6), "lost", len(lost6), "(of which unreachable in E9:", sum(h not in e9 for h in lost6), ")")


def route(r):
    i = r["impressum"]
    return f"{i['found_by']}:{i['found_keyword']}{'+fullbody' if i['fallback_extraction'] else ''}"


print("E9 routes:", collections.Counter(route(e9[h]) for h in e9 if found(e9, h)).most_common())
print("E6 routes:", collections.Counter(route(e6[h]) for h in e6 if found(e6, h)).most_common())
print("E9 gained vs E4 by route:", collections.Counter(route(e9[h]) for h in gained4).most_common())

# E6 precision-sample hosts
rows = [json.loads(l) for l in open(R + "results/E6/precision_sample.jsonl")]
bad = [r for r in rows if r["judgement"] == "bad"]
good = [r for r in rows if r["judgement"] != "bad"]
print(f"E6 bad hosts: {len(bad)}")
for r in bad:
    h = r["host"]
    if not found(e9, h):
        st = "rejected" if h in e9 else "unreachable in E9"
    elif e9[h]["impressum"]["url"] == e6[h]["impressum"]["url"]:
        st = "STILL SAME URL"
    else:
        st = "changed URL -> " + e9[h]["impressum"]["url"]
    print("   ", h, st)
still_good = [r for r in good if found(e9, r["host"])]
print(f"E6 good hosts: {len(good)}; still found {len(still_good)}; same URL "
      f"{sum(e9[r['host']]['impressum']['url'] == e6[r['host']]['impressum']['url'] for r in still_good)}")
for r in good:
    h = r["host"]
    if not found(e9, h):
        print("    lost good:", h, "unreachable" if h not in e9 else "no imprint", r["new_url"])
    elif e9[h]["impressum"]["url"] != e6[h]["impressum"]["url"]:
        print("    good, url changed:", h, e6[h]["impressum"]["url"], "->", e9[h]["impressum"]["url"])

# E5 recovery
e5 = [json.loads(l) for l in open(R + "results/E5/classifications.jsonl")]
tgt = [r for r in e5 if r["category"] in ("rule_miss", "no_link_but_url_exists")]
tab = collections.defaultdict(lambda: [0, 0, 0])
for r in tgt:
    fix = r["fix"] or "none"
    tab[fix][0] += 1
    tab[fix][1] += found(e9, r["host"])
    tab[fix][2] += found(e6, r["host"])
for k, (n, a, b) in sorted(tab.items()):
    print("E5", k, "n", n, "E9 found", a, "E6 found", b)
print("E5 total", len(tgt), "E9", sum(v[1] for v in tab.values()), "E6", sum(v[2] for v in tab.values()))
for r in tgt:
    if not found(e9, r["host"]):
        print("   E5 missing in E9:", r["host"], r["fix"], "E6 found" if found(e6, r["host"]) else "")

# new sample: hosts gained vs E4
random.seed(20261023)
sg = random.sample(gained4, 50)
sample = []
for h in sg:
    i = e9[h]["impressum"]
    sample.append(
        dict(
            host=h,
            kind="gained_vs_E4",
            new_url=i["url"],
            found_by=i["found_by"],
            found_keyword=i["found_keyword"],
            candidate_rank=i["candidate_rank"],
            fallback_extraction=i["fallback_extraction"],
            in_e6=found(e6, h),
            text_head=i["main_content"][:600],
        )
    )
import os

os.makedirs(R + "results/E9", exist_ok=True)
json.dump(sample, open(R + "results/E9/sample.json", "w"), ensure_ascii=False, indent=1)
json.dump(dict(gained4=gained4, lost4=lost4, gained6=gained6, lost6=lost6), open(R + "results/E9/sets.json", "w"))
print("sample hosts also in E6 precision sample:", sum(r["host"] in {x["host"] for x in rows} for r in sample))
