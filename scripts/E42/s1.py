import csv,collections,sys,glob,os
base='E31/r3/in/'
man=[l.rstrip('\n').split('\t') for l in open(base+'manifest.tsv')]
print(man[0])
def n(h):
    h=h.strip().lower().rstrip('.')
    return h[4:] if h.startswith('www.') else h
# map file -> source: use prefix of manifest cols
found=set(); skip=collections.defaultdict(set); ssrc=collections.defaultdict(set)
for f in sorted(glob.glob(base+'*.tsv')):
    if f.endswith('manifest.tsv'): continue
    for l in open(f):
        p=l.rstrip('\n').split('\t')
        if len(p)<2: continue
        h=n(p[0])
        if p[1]=='imprint_found': found.add(h)
        elif p[1]=='skipped_provider': skip[os.path.basename(f)].add(h)
import pickle;pickle.dump((found,dict(skip)),open('E42/p.pkl','wb'))
print(len(found),len(skip))
