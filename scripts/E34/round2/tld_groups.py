import csv, collections, math

import os  # D47: path constants below can be overridden by env
R = os.environ.get("R", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2/")
G = {"dach": {"de", "at", "ch", "li"}, "generic": {"com", "org", "net", "info", "eu", "io", "biz", "online", "shop", "app", "co", "me", "site", "xyz", "store", "tech"}}


def grp(h):
    t = h.rsplit(".", 1)[-1]
    for g, s in G.items():
        if t in s:
            return g
    return "cc_other"


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d * 100, (c + m) / d * 100


st = {r["host"]: r["status"] for r in csv.DictReader(open(R + "res/fetch_status_batch000000.tsv"), delimiter="\t")}
c = collections.defaultdict(collections.Counter)
for h, s in st.items():
    for k in (grp(h), "tld:" + h.rsplit(".", 1)[-1]):
        c[k]["n"] += 1
        c[k]["f"] += s == "imprint_found"
pil = set(st)
rest = collections.Counter(grp(h.strip()) for h in open(R + "frontier_r2.txt") if h.strip() not in pil)
for g in ("dach", "generic", "cc_other"):
    n, f = c[g]["n"], c[g]["f"]
    lo, hi = wilson(f, n)
    print(f"{g}: pilot {f}/{n} = {100*f/n:.1f}% (CI {lo:.1f}-{hi:.1f}); rest {rest[g]}; est. finds {rest[g]*f/n:.0f}")
for t in ("com", "org", "net", "info", "eu", "io", "shop", "online", "app"):
    k = c["tld:" + t]
    if k["n"]:
        print(f"  .{t}: {k['f']}/{k['n']} = {100*k['f']/k['n']:.1f}%")
