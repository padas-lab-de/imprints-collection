import hashlib
T="/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/"
def c(h):
    s=h.strip().lower()
    return s[4:] if s.startswith("www.") else s
pilot=set()
for f in ["p1_hostindex","p2_fineweb2","p3_hplt_ia"]:
    pilot|={c(l) for l in open(T+f"E27/{f}.txt") if l.strip()}
seen=set();out=[];nb=0;np_=0;cnt={}
for s in ["p1","p2","p3"]:
    for l in open(T+f"E27/pool_{s}.txt"):
        if not l.strip(): continue
        h=l.strip(); k=c(h)
        if k in pilot: np_+=1; continue
        if k in("blog.de","blogspot.de") or k.endswith((".blogspot.de",".blog.de")): nb+=1; continue
        assert k not in seen,k
        seen.add(k); out.append((h,s)); cnt[s]=cnt.get(s,0)+1
open(T+"E29/e29_rest.txt","w").write("".join(h+"\n" for h,_ in out))
open(T+"E29/e29_rest_source.tsv","w").write("".join(f"{h}\t{s}\n" for h,s in out))
sha=hashlib.sha256(open(T+"E29/e29_rest.txt","rb").read()).hexdigest()
open(T+"E29/e29_rest.txt.sha256","w").write(sha+"  e29_rest.txt\n")
print(cnt,"pilot removed",np_,"blog removed",nb,"total",len(out),"batches",-(-len(out)//25000),sha)
