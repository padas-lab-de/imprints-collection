import sys, random, hashlib, json, os, duckdb
from collections import Counter
R = os.environ.get("R", "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026")
sys.path.insert(0, R + "/src"); sys.path.insert(0, R + "/scripts/E22")
import frontier as F
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/"); O = T + "E33/"
q = sys.argv[1]  # q1..q4
ORDER = ["q3", "q4", "q1", "q2"]
con = duckdb.connect(O + "excl.duckdb", read_only=False)
con.execute("set memory_limit='1500MB'; set threads=4; set temp_directory='" + O + "tmpdb'")
DACH = "('de','at','ch')"
FW = T + "E24/fineweb2_deu_hosts_notknown.parquet"
if q == "q1":
    src = f"select host h, tld from '{FW}' where tld in {DACH} and list_max(dumps) < 'CC-MAIN-2023-'"
    desc = "FineWeb-2 deu_Latn, DACH TLD, last seen dump < CC-MAIN-2023 (E24 not-known table)"
elif q == "q2":
    src = f"select host h, tld from '{FW}' where tld not in {DACH}"
    desc = "FineWeb-2 deu_Latn, non-DACH TLD (E24 not-known table)"
elif q == "q3":
    src = f"select h, tld from read_parquet('{O}q3raw_distinct.parquet')"
    desc = "CC host index (host-index-testing-v2) crawls 2025-13, 2025-08, 2025-05, 2024-51, 2024-46; DACH TLD, fetch_200>0"
elif q == "q4":
    src = (f"select host h, regexp_extract(host,'([^.]+)$',1) tld from (select host, bool_or(dump='oth') anyoth from "
           f"(select regexp_replace(host,'^www\\.','') host, dump from read_parquet('{O}shards/hplt_*')"
           f" where host<>'' and regexp_matches(host,'^[a-z0-9._-]+$')) group by 1) where not anyoth"
           f" and regexp_extract(host,'([^.]+)$',1) in {DACH}")
    desc = "HPLT v2 deu_Latn, shards idx%4==0 minus E24 sample (951 shards), DACH TLD, Internet-Archive-only (collections wide*/survey* only)"
counts = {"source": desc}
con.execute(f"create or replace table cand as select distinct lower(trim(h)) h, any_value(tld) tld from ({src}) group by 1")
counts["raw_distinct_hosts_www_collapsed_or_as_given"] = con.execute("select count(*) from cand").fetchone()[0]
con.execute("create or replace table cand2 as select h,tld from cand where h not in (select h from exh)")
counts["after_exclusion_lists"] = con.execute("select count(*) from cand2").fetchone()[0]
con.execute("drop table cand")
cur = con.execute("select h,tld from cand2"); cache = {}; c = Counter(); keep = {}
while True:
    rows = cur.fetchmany(200000)
    if not rows: break
    for h, t in rows:
        r = F.classify(h, set(), cache); c[r] += 1
        if r == "new": keep[h] = t
    cache.clear()
counts["classify"] = dict(c)
counts["after_classify"] = len(keep)
keep = {h: t for h, t in keep.items() if not (h.endswith(".blogspot.de") or h.endswith(".blog.de"))}
counts["after_blog_drop"] = len(keep)
prev = set()
for p in ORDER[:ORDER.index(q)]:
    fn = O + f"pool_{p}.txt"
    if os.path.exists(fn):
        prev |= {l.strip() for l in open(fn) if l.strip()}
    else:
        print("WARNING: earlier pool missing", p)
keep = {h: t for h, t in keep.items() if h not in prev}
counts["after_disjoint_from_earlier_pools"] = len(keep)
counts["tld_mix"] = dict(Counter(keep.values()).most_common(12))
def w(path, hs):
    d = "".join(h + "\n" for h in hs).encode(); open(path, "wb").write(d); s = hashlib.sha256(d).hexdigest()
    open(path + ".sha256", "w").write(f"{s}  {path.split('/')[-1]}\n"); return s
pool = sorted(keep)
counts["pool_size"] = len(pool); counts["pool_sha256"] = w(O + f"pool_{q}.txt", pool)
random.seed(33)
s = random.sample(pool, 5000)
counts["pilot_tld_mix"] = dict(Counter(keep[h] for h in s).most_common(6))
counts["pilot_sha256"] = w(O + f"{q}_pilot.txt", s)
json.dump(counts, open(O + f"counts_{q}.json", "w"), indent=1)
print(json.dumps(counts, indent=1))
