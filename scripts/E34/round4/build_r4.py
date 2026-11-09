"""E34 round 4 frontier: ALL TLDs, new hosts from outlinks of crawls finished since round 3. Method as round 3 (build_r3.py).
Memory-lean: exclusion sets are sorted uint64 blake2b-8 hash arrays (www-collapsed host); outlink uniques via `sort -u`.
Run: python3 build_r4.py   (after snap4.sh)"""
import glob, gzip, hashlib, json, os, random, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np

W = "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026"
T = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp"
E35 = "/home/dinzinger/GitHub/imprints-collection-e35/datasets"
O = T + "/E34/round4"
sys.path.insert(0, W + "/src")
from ic.utils.filter_utils import check_url

e10 = Path(W + "/scripts/E10/candidates.py").read_text()
exec(e10[e10.index("PLATFORMS = {") : e10.index("def tld(h):")])


def rd(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8", errors="replace") as f:
        for l in f:
            l = l.strip().lower()
            if l:
                yield l


def nw(h):
    return h[4:] if h.startswith("www.") else h


def H(s):
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little")


class HSet:
    def __init__(self):
        self.chunks = []
        self.buf = []
        self.arr = None

    def add(self, h):
        self.buf.append(H(nw(h)))
        if len(self.buf) >= 1_000_000:
            self.flush()

    def flush(self):
        if self.buf:
            self.chunks.append(np.array(self.buf, dtype=np.uint64))
            self.buf = []

    def freeze(self):
        self.flush()
        self.arr = np.unique(np.concatenate(self.chunks)) if self.chunks else np.zeros(0, np.uint64)
        self.chunks = []
        return self

    def has(self, h):
        x = np.uint64(H(nw(h)))
        i = np.searchsorted(self.arr, x)
        return i < len(self.arr) and self.arr[i] == x

    def __len__(self):
        return len(self.arr)


# exclusion files ---------------------------------------------------------
crawled = HSet()
excl_files = {}  # name -> (kind, lines)
nfiles = 0
for p in sorted(glob.glob(T + "/E31/final/in/*.tsv")):
    if p.endswith("manifest.tsv"):
        continue
    nfiles += 1
    with open(p, encoding="utf-8") as f:
        for l in f:
            h = l.split("\t", 1)[0].strip().lower()
            if h and h != "host":
                crawled.add(h)
# E31 r3 additions (E34r3 crawl inputs)
for p in sorted(glob.glob(E35 + "/E31/r3/E31_in_new/*.tsv")):
    if p.endswith("manifest.tsv"):
        continue
    nfiles += 1
    with open(p, encoding="utf-8") as f:
        for l in f:
            h = l.split("\t", 1)[0].strip().lower()
            if h and h != "host":
                crawled.add(h)
print("E31 in files", nfiles, flush=True)


def add_lists(hs, files, tag):
    for k in files:
        if not os.path.exists(k):
            print("MISSING exclusion file", k, flush=True)
            excl_files[k] = -1
            continue
        c = 0
        for h in rd(k):
            c += 1
            hs.add(h)
        excl_files[k] = c


# round 1/2/3 frontiers + lists, all treated as crawled-or-planned (round 3 put r1/r2 frontiers in "crawled")
fr_files = [T + "/E34/frontier_new_seeds.txt", T + "/E34/e34_rest.txt", T + "/E34/round2/frontier_r2.txt",
            T + "/E34/round2/pilot_r2.txt", T + "/E34/round2/e34r2_rest.txt",
            T + "/E34/round3/frontier_r3.txt", T + "/E34/round3/pilot_r3.txt", T + "/E34/round3/e34r3_rest.txt"]
add_lists(crawled, fr_files, "frontier")
crawled.freeze()
print("crawled (E31 inputs + r1/2/3 frontiers) hashed", len(crawled), flush=True)

known = HSet()
known_files = [W + "/seed_hosts.txt.gz", T + "/e22_hosts.txt", T + "/d29/round2_frontier_rest.txt",
               T + "/round1_frontier_A.txt", T + "/E23/cc_german_candidates.txt", T + "/E25/cc43_dach_new.txt",
               T + "/E26/cc43_dach_rest.txt", T + "/E29/e29_rest.txt", T + "/E30/e30_rest.txt"]
known_files += sorted(glob.glob(T + "/E24/new_hosts_*.txt")) + sorted(glob.glob(T + "/E27/pool_p*.txt"))
known_files += sorted(glob.glob(T + "/E28/p*.txt")) + sorted(glob.glob(T + "/E33/pool_q*.txt"))
known_files += [T + "/E33/e33_rest.txt", T + "/E37/e37_rest.txt"]
known_files += sorted(glob.glob(T + "/E33/q*_pilot.txt")) + sorted(glob.glob(T + "/E36/pilot/pilot.txt"))
n_old = len(known_files)
# NEW in round 4
new_files = []
new_files += sorted(glob.glob(E35 + "/E41/*/L[1-4]_*.txt"))
new_files += sorted(glob.glob(T + "/E41/L[1-4].txt"))
new_files += sorted(glob.glob(E35 + "/E43/pool_*.txt")) + sorted(glob.glob(E35 + "/E43/pilot_*.txt")) + sorted(glob.glob(E35 + "/E43/rest_*.txt"))
new_files += sorted(glob.glob(E35 + "/E44/pool_*.txt")) + sorted(glob.glob(E35 + "/E44/pilot_*.txt")) + sorted(glob.glob(E35 + "/E44/rest_*.txt"))
new_files += sorted(glob.glob(T + "/E43/pool_*.txt")) + sorted(glob.glob(T + "/E43/pilot_*.txt")) + sorted(glob.glob(T + "/E43/rest_*.txt"))
new_files += sorted(glob.glob(T + "/E44/pool_*.txt")) + sorted(glob.glob(T + "/E44/pilot_*.txt")) + sorted(glob.glob(T + "/E44/rest_*.txt"))
new_files += [T + "/E42/shopify_all.txt", "/home/dinzinger/E48-shopify/list_all.txt", T + "/E42/pilot100.txt"]
new_files += sorted(glob.glob("/home/dinzinger/E48-shopify/list_*.txt"))
new_files += [E35 + "/E45/listA.txt", E35 + "/E45/listB.txt", E35 + "/E46/list.txt", E35 + "/E47/list.txt"]
new_files += [T + "/E34/round3/pilot_new_d34_sites.txt"] if False else []
new_files = list(dict.fromkeys(new_files))
add_lists(known, known_files + new_files, "known")
known.freeze()
print("known hashed", len(known), "old files", n_old, "new files", len(new_files), flush=True)

# outlinks ----------------------------------------------------------------
snaps = sorted(glob.glob(O + "/snap/*.txt"))
per = {os.path.basename(p): sum(1 for _ in rd(p)) for p in snaps}
uniq_path = O + "/outlinks_uniq.tmp"
subprocess.run(
    "cat %s | tr 'A-Z' 'a-z' | sed 's/[[:space:]]*$//' | grep -v '^$' | LC_ALL=C sort -u -S 2G -T %s > %s"
    % (" ".join(snaps), O, uniq_path), shell=True, check=True)
st = Counter()
cand = set()
nuniq = 0
for h in rd(uniq_path):
    nuniq += 1
    if crawled.has(h):
        st["crawled"] += 1
    elif known.has(h):
        st["known_list"] += 1
    elif not check_url(h, is_host=True):
        st["bad"] += 1
    elif platform(h):
        st["platform"] += 1
    else:
        cand.add(h)
print("snap files", len(per), "lines", sum(per.values()), "unique", nuniq, flush=True)
print("dropped", dict(st), "kept", len(cand))
final = {h for h in cand if not (h.startswith("www.") and h[4:] in cand)}
www_dup = len(cand) - len(final)
print("www dup", www_dup, "final", len(final))
os.remove(uniq_path)
data = "".join(h + "\n" for h in sorted(final)).encode()
Path(O + "/frontier_r4.txt").write_bytes(data)
dg = hashlib.sha256(data).hexdigest()
Path(O + "/frontier_r4.txt.sha256").write_text(f"{dg}  frontier_r4.txt\n")
print("sha256", dg)
tld = lambda s: Counter(h.rsplit(".", 1)[-1] for h in s).most_common(15)
print("TLD top15", tld(final))
random.seed(344)
srt = sorted(final)
pil = random.sample(srt, 5000)
Path(O + "/pilot_r4.txt").write_text("".join(h + "\n" for h in pil))
psha = hashlib.sha256(Path(O + "/pilot_r4.txt").read_bytes()).hexdigest()
Path(O + "/pilot_r4.txt.sha256").write_text(f"{psha}  pilot_r4.txt\n")
ps = set(pil)
rest = [h for h in srt if h not in ps]
Path(O + "/rest_r4.txt").write_text("".join(h + "\n" for h in rest))
rsha = hashlib.sha256(Path(O + "/rest_r4.txt").read_bytes()).hexdigest()
Path(O + "/rest_r4.txt.sha256").write_text(f"{rsha}  rest_r4.txt\n")
print("pilot sha", psha, "rest sha", rsha, "rest", len(rest))
print("pilot TLD top15", tld(pil))
json.dump({"per_snapshot": per, "snapshot_lines_total": sum(per.values()), "unique_outlinks": nuniq,
           "dropped": st, "www_dup": www_dup, "frontier": len(final), "pilot": len(pil), "rest": len(rest),
           "sha256": {"frontier": dg, "pilot": psha, "rest": rsha},
           "exclusion_files_lines": excl_files, "crawled_hashed": len(crawled), "known_hashed": len(known),
           "tld_top15_frontier": tld(final), "tld_top15_pilot": tld(pil)},
          open(O + "/build_info.json", "w"), indent=1)
