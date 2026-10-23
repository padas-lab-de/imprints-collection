"""E11: summarise compare_discovery.py output (A = E4 code, B = E4 keyed by URL, C = current code)."""
import json
import random
import sys

r = {h: v for h, v in json.load(open(sys.argv[1])).items() if v}
print("hosts", len(r), "B==C sets:", sum(set(v["B"]) == set(v["C"]) for v in r.values()),
      "A subset of C:", sum(set(v["A"]) <= set(v["C"]) for v in r.values()))
print("hosts with loss A<C:", sum(len(v["A"]) < len(v["C"]) for v in r.values()),
      "hosts with any external C:", sum(bool(v["C"]) for v in r.values()))
sa = sum(len(v["A"]) for v in r.values())
sc = sum(len(v["C"]) for v in r.values())
print("A", sa, "C", sc, "ratio", sc / sa)
ua = {x for v in r.values() for x in v["A"]}
uc = {x for v in r.values() for x in v["C"]}
print("unique ratio", len(uc) / len(ua))
random.seed(1)
hs = list(r)
rs = []
for _ in range(2000):
    s = [random.choice(hs) for _ in hs]
    a = sum(len(r[h]["A"]) for h in s)
    c = sum(len(r[h]["C"]) for h in s)
    if a:
        rs.append(c / a)
rs.sort()
print("bootstrap 95% ratio", rs[50], rs[1950])
