import sys, gzip, random, hashlib, duckdb
from collections import Counter
import os  # D47: path constants below can be overridden by env
R=os.environ.get("R", "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026")
sys.path.insert(0,R+"/src"); sys.path.insert(0,R+"/scripts/E22")
import frontier as F
T=os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/")
O=T+"E25/"
known=set()
with gzip.open(R+"/seed_hosts.txt.gz","rt") as f:
    for l in f:
        l=l.strip().lower()
        if l: known.add(l)
n0=len(known)
for p in (T+"e22_hosts.txt",T+"d29/round2_frontier_rest.txt"): known.update(F.read_hosts(p))
print("known",n0,len(known))
rows=duckdb.sql(f"select h,tld from '{T}research/cc43_dach_hosts.parquet' where deu_page").fetchall()
print("deu_page",len(rows))
cache={}; cnt=Counter(); new={}
for h,t in rows:
    h=h.strip().lower()
    c=F.classify(h,known,cache); cnt[c]+=1
    if c=="new": new[h]=t
print(cnt)
final={h:t for h,t in new.items() if not (h.startswith("www.") and h[4:] in new)}
print("new",len(new),"after www collapse",len(final),Counter(final.values()))
def w(name,hs):
    d="".join(h+"\n" for h in sorted(hs)).encode(); open(O+name,"wb").write(d)
    s=hashlib.sha256(d).hexdigest(); open(O+name+".sha256","w").write(f"{s}  {name}\n"); print(name,len(hs),s)
w("cc43_dach_new.txt",final)
random.seed(25)
pilot=[]
for t in ("de","at","ch"):
    hs=sorted(h for h,x in final.items() if x==t)
    k=round(20000*len(hs)/len(final)); pilot+=random.sample(hs,k)
    print(t,len(hs),k)
print(len(pilot))
w("pilot20k.txt",pilot)
