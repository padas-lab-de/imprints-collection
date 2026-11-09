import os, collections
M = os.path.expanduser("~/GitHub/imprints-collection/datasets/E19")
prov = {}
with open(f"{M}/round2/recovery_hosts_all_causes.tsv") as f:
    next(f)
    for l in f:
        p = l.rstrip("\n").split("\t"); prov[p[0]] = p[3]
r2 = [l.strip() for l in open(f"{M}/round2/recovery_round2.txt") if l.strip()]
c = collections.Counter(prov.get(h, "?") for h in r2)
print("round2 hosts", len(r2), "top providers:")
for k, v in c.most_common(6): print(" ", v, k)
