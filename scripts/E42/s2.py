import os, glob, random
os.chdir('/home/dinzinger/.claude/jobs/cfd8c2d0/tmp')


def n(h):
    h = h.strip().lower().rstrip('.')
    return h[4:] if h.startswith('www.') else h


u = [l.strip() for l in open('E42/shopify_all.txt') if l.strip()]
mis = set()
for f in glob.glob('E31/r3/in/mispel_*.tsv'):
    for l in open(f):
        p = l.rstrip('\n').split('\t')
        if len(p) > 1 and p[1] != 'skipped_provider':
            mis.add(n(p[0]))
pil = {n(l) for l in open('d31/shopify_pilot.txt') if l.strip()}
cand = sorted(h for h in u if h not in mis and h not in pil)
print(len(u), len(mis), len(pil), len(cand))
random.seed(42)
s = random.sample(cand, 100)
open('E42/pilot100.txt', 'w').write('\n'.join(s) + '\n')
