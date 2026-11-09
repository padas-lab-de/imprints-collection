"""E34 round 3 frontier: DACH-only (de/at/ch/li) new hosts from outlinks. Method as round 2 (build_r2.py)."""
import glob, gzip, hashlib, json, os, random, sys
from collections import Counter
from pathlib import Path

W = os.environ.get("W", "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026")
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
O = T + "/E34/round3"
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


def nw(h):
    return h[4:] if h.startswith("www.") else h


# 1) crawled hosts: E31 inputs col 1 (www-collapsed)
crawled = set()
nfiles = 0
for p in sorted(glob.glob(T + "/E31/final/in/*.tsv")):
    if p.endswith("manifest.tsv"):
        continue
    nfiles += 1
    with open(p, encoding="utf-8") as f:
        for l in f:
            h = l.split("\t", 1)[0].strip().lower()
            if h:
                crawled.add(nw(h))
print("E31 in files", nfiles, "crawled www-collapsed", len(crawled))

# 2) round 1 + round 2 frontiers
fr = {}
for k in [T + "/E34/frontier_new_seeds.txt", T + "/E34/e34_rest.txt", T + "/E34/round2/frontier_r2.txt",
          T + "/E34/round2/pilot_r2.txt", T + "/E34/round2/e34r2_rest.txt"]:
    c = 0
    for h in rd(k):
        c += 1
        crawled.add(nw(h))
    fr[os.path.basename(k)] = c
print("round1/2 frontier files", fr, "crawled+frontiers", len(crawled))

# 3) round-2 "known" (planned/uncrawled candidate lists), same as round 2
known_files = [W + "/seed_hosts.txt.gz", T + "/e22_hosts.txt", T + "/d29/round2_frontier_rest.txt",
               T + "/round1_frontier_A.txt", T + "/E23/cc_german_candidates.txt", T + "/E25/cc43_dach_new.txt",
               T + "/E26/cc43_dach_rest.txt", T + "/E29/e29_rest.txt", T + "/E30/e30_rest.txt"]
known_files += sorted(glob.glob(T + "/E24/new_hosts_*.txt")) + sorted(glob.glob(T + "/E27/pool_p*.txt"))
known_files += sorted(glob.glob(T + "/E28/p*.txt")) + sorted(glob.glob(T + "/E33/pool_q*.txt"))
known_files += [T + "/E33/e33_rest.txt", T + "/E37/e37_rest.txt"]
known_files += sorted(glob.glob(T + "/E33/q*_pilot.txt")) + sorted(glob.glob(T + "/E36/pilot/pilot.txt"))
known = set()
for k in known_files:
    for h in rd(k):
        known.add(nw(h))
print("known (round-2 candidate lists) www-collapsed", len(known))

# 4) outlinks
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
print("snap files", len(per), "lines", lines, "unique", len(uniq))
st = Counter()
cand = set()
for h in uniq:
    if nw(h) in crawled:
        st["crawled"] += 1
    elif nw(h) in known:
        st["known_list"] += 1
    elif h.rsplit(".", 1)[-1] not in ("de", "at", "ch", "li"):
        st["tld"] += 1
    elif not check_url(h, is_host=True):
        st["bad"] += 1
    elif platform(h):
        st["platform"] += 1
    else:
        cand.add(h)
print("dropped", dict(st), "kept", len(cand))
final = {h for h in cand if not (h.startswith("www.") and h[4:] in cand)}
print("www dup", len(cand) - len(final), "final", len(final))
data = "".join(h + "\n" for h in sorted(final)).encode()
Path(O + "/frontier_r3.txt").write_bytes(data)
dg = hashlib.sha256(data).hexdigest()
Path(O + "/frontier_r3.txt.sha256").write_text(f"{dg}  frontier_r3.txt\n")
print("sha256", dg)
print("TLD", Counter(h.rsplit(".", 1)[-1] for h in final).most_common())
random.seed(343)
pil = random.sample(sorted(final), 5000)
Path(O + "/pilot_r3.txt").write_text("".join(h + "\n" for h in pil))
print("pilot sha", hashlib.sha256(Path(O + "/pilot_r3.txt").read_bytes()).hexdigest())
print("pilot TLD", Counter(h.rsplit(".", 1)[-1] for h in pil).most_common())
json.dump({"per_snapshot": per, "dropped": st, "round12": fr}, open(O + "/build_info.json", "w"), indent=1)
