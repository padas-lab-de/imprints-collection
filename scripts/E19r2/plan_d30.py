import sys, hashlib, os
sys.path.insert(0, "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026/scripts/E19")
from collect import read_rows
M = os.path.expanduser("~/GitHub/imprints-collection/datasets/E19")
A = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/e19agent2"
D = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d30"
def origin(b):
    return "aspe" if b <= 106 else "lorbeer" if b <= 156 else "apfel" if b <= 213 else "mispel"
b = {}
with open(f"{M}/round2/recovery_hosts_all_causes.tsv") as f:
    next(f)
    for l in f:
        p = l.rstrip("\n").split("\t"); b[p[0]] = int(p[4])
rem = []
for v in ("akazie", "mispel"):
    shard = [l.strip() for l in open(f"{A}/round2b_{v}.txt") if l.strip()]
    rows = list(read_rows(f"{D}/{v}/fetch_status_batch000000.tsv"))
    done = {r["host"] for r in rows if r["status"] != "deferred"}
    found = {r["host"] for r in rows if r["status"] == "imprint_found"}
    left = [h for h in shard if h not in done]
    print(v, "shard", len(shard), "done", len(done & set(shard)), "found", len(found), "left", len(left), "done-not-in-shard", len(done - set(shard)))
    rem += left
assert len(rem) == len(set(rem))
VMS = ["abelie", "apfel"]
parts = {v: [] for v in VMS}
ka = len(rem) // 2 - sum(1 for h in rem if origin(b[h]) == "apfel")
for h in sorted(rem, key=lambda h: hashlib.sha1(h.encode()).hexdigest()):
    i = 1
    if VMS[i] == origin(b[h]): i = 0
    elif ka > 0: i = 0; ka -= 1
    assert VMS[i] != origin(b[h])
    parts[VMS[i]].append(h)
for v in VMS:
    open(f"{D}/round2c_{v}.txt", "w").write("".join(h + "\n" for h in parts[v]))
    print(v, len(parts[v]))
print("apfel-origin hosts (all to abelie)", sum(1 for h in rem if origin(b[h]) == "apfel"))
