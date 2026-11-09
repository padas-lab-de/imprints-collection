import glob, gzip, hashlib, json, os, random, sys
from collections import Counter
from pathlib import Path

W = os.environ.get("W", "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026")
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
O = T + "/E34"
sys.path.insert(0, W + "/src")
from ic.utils.filter_utils import check_url

e10 = Path(W + "/scripts/E10/candidates.py").read_text()
exec(e10[e10.index("PLATFORMS = {") : e10.index("def tld(h):")])


def rd(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f:
        for l in f:
            l = l.strip().lower()
            if l:
                yield l


known_files = [W + "/seed_hosts.txt.gz", T + "/e22_hosts.txt", T + "/d29/round2_frontier_rest.txt",
               T + "/round1_frontier_A.txt", T + "/E23/cc_german_candidates.txt", T + "/E25/cc43_dach_new.txt",
               T + "/E26/cc43_dach_rest.txt", T + "/E29/e29_rest.txt", T + "/E30/e30_rest.txt"]
known_files += sorted(glob.glob(T + "/E24/new_hosts_*.txt")) + sorted(glob.glob(T + "/E27/pool_p*.txt"))
known_files += sorted(glob.glob(T + "/E28/p*.txt")) + sorted(glob.glob(T + "/E33/pool_q*.txt"))
known = set()
kinfo = {}
for k in known_files:
    n0 = len(known)
    c = 0
    for h in rd(k):
        c += 1
        known.add(h[4:] if h.startswith("www.") else h)
    kinfo[os.path.basename(k)] = c
print("known files", json.dumps(kinfo, indent=1), "known (www-stripped)", len(known))

lines = 0
uniq = set()
per = {}
for p in sorted(glob.glob(O + "/snap/*.txt")):
    n = 0
    for h in rd(p):
        n += 1
        uniq.add(h)
    per[os.path.basename(p)] = n
    lines += n
print("lines", lines, "unique", len(uniq))
after_known = {h for h in uniq if (h[4:] if h.startswith("www.") else h) not in known}
print("known dropped", len(uniq) - len(after_known))
filt = Counter()
keep = set()
for h in after_known:
    if not check_url(h, is_host=True):
        filt["bad"] += 1
    elif platform(h):
        filt["platform"] += 1
    else:
        keep.add(h)
final = {h for h in keep if not (h.startswith("www.") and h[4:] in keep)}
print("filtered", dict(filt), "after filter", len(keep), "www dup", len(keep) - len(final), "final", len(final))
data = "".join(h + "\n" for h in sorted(final)).encode()
Path(O + "/frontier_new_seeds.txt").write_bytes(data)
dg = hashlib.sha256(data).hexdigest()
Path(O + "/frontier_new_seeds.txt.sha256").write_text(f"{dg}  frontier_new_seeds.txt\n")
print("sha256", dg)
tl = Counter(h.rsplit(".", 1)[-1] for h in final)
print("TLD top 20", [(t, n, round(100 * n / len(final), 1)) for t, n in tl.most_common(20)])
random.seed(34)
pil = random.sample(sorted(final), 5000)
Path(O + "/pilot.txt").write_text("".join(h + "\n" for h in pil))
print("pilot sha", hashlib.sha256(Path(O + "/pilot.txt").read_bytes()).hexdigest())
print("pilot TLD", Counter(h.rsplit(".", 1)[-1] for h in pil).most_common(10))
json.dump({"known": kinfo, "per_snapshot": per}, open(O + "/build_info.json", "w"), indent=1)
