import sys, hashlib, os, random, glob
sys.path.insert(0, "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026/scripts/E19")
from collect import read_rows
M = os.path.expanduser("~/GitHub/imprints-collection/datasets/E19")
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
D = f"{T}/d31"
SHOP = "v4:23.227.38"
def origin(b):
    return "aspe" if b <= 106 else "lorbeer" if b <= 156 else "apfel" if b <= 213 else "mispel"
prov, bat = {}, {}
with open(f"{M}/round2/recovery_hosts_all_causes.tsv") as f:
    next(f)
    for l in f:
        p = l.rstrip("\n").split("\t"); prov[p[0]] = p[3]; bat[p[0]] = int(p[4])
allh = [l.strip() for l in open(f"{M}/round2/recovery_round2.txt") if l.strip()]
assert len(allh) == len(set(allh)) and all(h in bat for h in allh)
src = {"round2_s0": f"{T}/e19agent2/s0", "round2_s1": f"{T}/e19agent2/s1",
       "round2b_akazie": f"{T}/d30/akazie", "round2b_mispel": f"{T}/d30/mispel",
       "round2b_aralie": f"{D}/status/aralie", "round2b_aspe": f"{D}/status/aspe",
       "round2b_lorbeer": f"{D}/status/lorbeer", "round2c_abelie": f"{D}/status/abelie",
       "round2c_apfel": f"{D}/status/apfel"}
done, found = set(), set()
for k, d in src.items():
    rows = [r for p in sorted(glob.glob(f"{d}/fetch_status_batch*.tsv")) for r in read_rows(p)]
    dn = {r["host"] for r in rows if r["status"] != "deferred"}
    fd = {r["host"] for r in rows if r["status"] == "imprint_found"}
    print(f"{k}\tdone {len(dn)}\tfound {len(fd)}")
    done |= dn; found |= fd
print("total done", len(done), "found", len(found), "done outside list", len(done - set(allh)))
rem = [h for h in allh if h not in done]
shop = [h for h in rem if prov.get(h) == SHOP]
other = [h for h in rem if prov.get(h) != SHOP]
print("left", len(rem), "shopify", len(shop), "other", len(other))
VMS = ["aspe", "lorbeer", "apfel", "mispel", "akazie", "aralie", "abelie"]
parts = {v: [] for v in VMS}
for h in sorted(other, key=lambda h: hashlib.sha1(h.encode()).hexdigest()):
    v = min((v for v in VMS if v != origin(bat[h])), key=lambda v: len(parts[v]))
    parts[v].append(h)
for v in VMS:
    assert all(origin(bat[h]) != v for h in parts[v])
    open(f"{D}/round2d_{v}.txt", "w").write("".join(h + "\n" for h in parts[v]))
    print("round2d", v, len(parts[v]))
open(f"{D}/shopify_left.txt", "w").write("".join(h + "\n" for h in shop))
cand = sorted(h for h in shop if origin(bat[h]) != "mispel")
pilot = random.Random(31).sample(cand, 500)
open(f"{D}/shopify_pilot.txt", "w").write("".join(h + "\n" for h in pilot))
print("shopify by origin", {v: sum(1 for h in shop if origin(bat[h]) == v) for v in VMS[:4]})
print("pilot", len(pilot), "(non-mispel-origin candidates", len(cand), ")")
