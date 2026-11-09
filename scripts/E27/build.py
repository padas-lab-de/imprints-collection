import sys, gzip, random, hashlib, duckdb
from collections import Counter
import os  # D47: path constants below can be overridden by env
R=os.environ.get("R", "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026")
sys.path.insert(0,R+"/src"); sys.path.insert(0,R+"/scripts/E22")
import frontier as F
T=os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/"); O=T+"E27/"
con=duckdb.connect(); con.execute("set memory_limit='1.5GB'; set threads=4")
known=set()
with gzip.open(R+"/seed_hosts.txt.gz","rt") as f:
    for l in f:
        l=l.strip().lower()
        if l: known.add(l)
for p in (T+"e22_hosts.txt",T+"d29/round2_frontier_rest.txt"): known.update(F.read_hosts(p))
print("known",len(known))
cc=set(F.read_hosts(T+"E25/cc43_dach_new.txt"))
def twin(h): return h[4:] if h.startswith("www.") else "www."+h
def ccx(h): return h in cc or twin(h) in cc
DACH=("de","at","ch")
src={}
src["p1"]=[(h,h.rsplit(".",1)[-1]) for h in F.read_hosts(T+"E24/new_hosts_hostindex_2025-18.txt")]
src["p2"]=con.execute(f"select host,tld from '{T}E24/fineweb2_deu_hosts_notknown.parquet' where tld in ('de','at','ch') and list_max(dumps)>='CC-MAIN-2023-'").fetchall()
src["p3"]=con.execute(f"select host,tld from '{T}E24/hplt_deu_sample_hosts.parquet' where tld in ('de','at','ch') and len(list_filter(dumps, x-> not (x like 'wide%' or x like 'survey%')))=0").fetchall()
pools={}; cache={}; assigned=set()
def w(path,hs):
    d="".join(h+"\n" for h in hs).encode(); open(path,"wb").write(d); s=hashlib.sha256(d).hexdigest()
    open(path+".sha256","w").write(f"{s}  {path.split('/')[-1]}\n"); print(path.split('/')[-1],len(hs),s)
for k in ("p1","p2","p3"):
    rows=[(h.strip().lower(),t) for h,t in src[k]]
    rows=[(h,t) for h,t in rows if t in DACH]
    print(k,"raw dach",len(rows))
    rows=list({h:t for h,t in rows}.items()); print(k,"unique",len(rows))
    rows=[(h,t) for h,t in rows if not ccx(h)]; print(k,"after cc43 excl",len(rows))
    c=Counter(); keep={}
    for h,t in rows:
        r=F.classify(h,known,cache); c[r]+=1
        if r=="new": keep[h]=t
    print(k,dict(c))
    keep={h:t for h,t in keep.items() if not (h.startswith("www.") and h[4:] in keep)}
    print(k,"after www collapse",len(keep))
    keep={h:t for h,t in keep.items() if h not in assigned and twin(h) not in assigned}
    print(k,"after disjoint",len(keep),dict(Counter(keep.values())))
    assigned|=set(keep); pools[k]=keep
    w(O+f"pool_{k}.txt",sorted(keep))
names={"p1":"p1_hostindex.txt","p2":"p2_fineweb2.txt","p3":"p3_hplt_ia.txt"}
for k in pools:
    random.seed(27)
    s=random.sample(sorted(pools[k]),5000)
    print(k,"pilot tld",dict(Counter(pools[k][h] for h in s)))
    w(O+names[k],s)
