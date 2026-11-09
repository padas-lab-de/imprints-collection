import glob,random,hashlib,os
T=os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
def col(h): 
    h=h.lower().strip()
    return h[4:] if h.startswith('www.') else h
found=set();cand={}
for f in glob.glob(T+'/E31/in/*.tsv'):
    is16=f.endswith('_E16_E16_seeds.tsv')
    for l in open(f):
        p=l.rstrip('\n').split('\t')
        if len(p)<2 or p[0]=='host': continue
        if p[1]=='imprint_found': found.add(col(p[0]))
        if is16 and p[1]=='imprint_not_found' and p[0].lower().rsplit('.',1)[-1] in('de','at','ch'): cand[p[0]]=1
print('candidates',len(cand))
c2=[h for h in cand if col(h) not in found]; print('after found excl',len(c2))
aud=set(col(l.split('\t')[0]) for l in open(T+'/E32/sample.tsv') if not l.startswith('host'))
c3=sorted(h for h in c2 if col(h) not in aud); print('after audit excl',len(c3))
s=random.Random(36).sample(c3,5000)
open('pilot.txt','w').write('\n'.join(s)+'\n')
print(hashlib.sha256(open('pilot.txt','rb').read()).hexdigest())
