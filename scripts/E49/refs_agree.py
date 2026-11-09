import json,glob,sys,collections
def load(p):
    d={}
    for f in sorted(glob.glob(f"datasets/E49/refs_raw/{p}/part*_*.jsonl")):
        for l in open(f):
            r=json.loads(l); d[(r["schema"],r["host"])]=r
    return d
A,B=load("A"),load("B")
assert A.keys()==B.keys(), (len(A),len(B))
for s in ("poi","wz"):
    keys=[k for k in A if k[0]==s]
    n=len(keys); lv=collections.Counter(); ex=len_=0; dis=[]
    for k in keys:
        a,b=A[k],B[k]
        pa,pb=a.get("path") or [],b.get("path") or []
        for i in range(max(len(pa),len(pb))):
            if i<len(pa) and i<len(pb) and pa[i]==pb[i]: lv[i+1]+=1
        if a["main"]==b["main"]: ex+=1
        elif a["main"] in (b.get("extra") or []) or b["main"] in (a.get("extra") or []): len_+=1
        else: dis.append(k[1])
    print(s,"n",n,"exact",ex,"lenient",ex+len_,"levels",dict(sorted(lv.items())),"hard disagree",len(dis))
