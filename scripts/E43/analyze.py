"""Pilot yield. Usage: analyze.py X(E43|E44)   reads ~/GitHub/imprints-collection-e43/datasets/X/pilot."""
import glob, json, subprocess, sys
from collections import Counter

X = sys.argv[1]
T = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp"
D = f"/home/dinzinger/GitHub/imprints-collection-e43/datasets/{X}/pilot"
DACH = ("de", "at", "ch", "li")
EX = T + "/E41/R/scripts/E31/extract.py"
rows = subprocess.run(["python3", EX, D], capture_output=True, text=True, check=True).stdout.splitlines()
last = {}
for l in rows:  # last row per host
    c = l.split("\t")
    if len(c) == 3:
        last[c[0]] = (c[1], c[2])
pilot = [l.strip() for l in open(f"{T}/{X}/pilot_{X}.txt") if l.strip()]
tld = lambda h: h.rsplit(".", 1)[-1]
res = {"pilot_hosts": len(pilot), "hosts_with_status": len(last), "not_in_pilot": len(set(last) - set(pilot))}
res["status_counts"] = dict(Counter(s for s, _ in last.values()).most_common())
f = [h for h, (s, _) in last.items() if s == "imprint_found"]
res["imprint_found"] = len(f)
res["imprint_found_pct"] = round(100 * len(f) / max(1, len(last)), 2)
for nm, sel in (("dach", lambda h: tld(h) in DACH), ("other", lambda h: tld(h) not in DACH)):
    a = [h for h in last if sel(h)]
    b = [h for h in f if sel(h)]
    res[f"{nm}_hosts"] = len(a)
    res[f"{nm}_found"] = len(b)
    res[f"{nm}_found_pct"] = round(100 * len(b) / max(1, len(a)), 2)
# D34 canonical sites
import duckdb
con = duckdb.connect(T + "/E41/e41.duckdb", read_only=True)
crawled = {r[0] for r in con.execute("select h from crawled").fetchall()}
col = lambda h: h[4:] if h.startswith("www.") else h
crawled |= {col(h) for h in last}
base = set(l.strip() for l in open(T + "/E31/r3/out/canonical_sites.txt"))
sites = set()
for h in f:
    t = last[h][1]
    c = col(h)
    if t and col(t) in crawled:
        c = col(t)
    sites.add(c)
res["d34_sites_in_pilot"] = len(sites)
res["d34_new_vs_r3_inputs"] = len(sites - base)
res["d34_already_in_r3"] = len(sites & base)
res["d34_new_pct_of_hosts"] = round(100 * len(sites - base) / max(1, len(last)), 2)
# Shopify: hosts logged skipped_provider; status files list no per-IP info, so check logs
res["skipped_provider_rows"] = res["status_counts"].get("skipped_provider", 0)
rq = hosts_sh = 0
for p in glob.glob(D + "/fetch_status_batch*.tsv"):
    for l in open(p, encoding="utf-8"):
        c = l.rstrip("\n").split("\t")
        if len(c) >= 6 and c[3] == "v4:23.227.38":
            hosts_sh += 1
            rq += int(c[5]) if c[5].isdigit() else 0
res["shopify_group_hosts"] = hosts_sh
res["shopify_group_requests_sum"] = rq
json.dump(res, open(f"{T}/{X}/yield_{X}.json", "w"), indent=1)
print(json.dumps(res, indent=1))
