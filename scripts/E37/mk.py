import glob, hashlib, random
T = '/home/dinzinger/.claude/jobs/cfd8c2d0/tmp'
def col(h):
    h = h.lower().strip()
    return h[4:] if h.startswith('www.') else h
found = set(); cand = {}
for f in glob.glob(T + '/E31/in/*.tsv'):
    is16 = f.endswith('_E16_E16_seeds.tsv')
    for l in open(f):
        p = l.rstrip('\n').split('\t')
        if len(p) < 2 or p[0] == 'host': continue
        if p[1] == 'imprint_found': found.add(col(p[0]))
        if is16 and p[1] == 'imprint_not_found' and p[0].lower().rsplit('.', 1)[-1] in ('de', 'at', 'ch'): cand[p[0]] = 1
c2 = [h for h in cand if col(h) not in found]
aud = set(col(l.split('\t')[0]) for l in open(T + '/E32/sample.tsv') if not l.startswith('host'))
c3 = sorted(h for h in c2 if col(h) not in aud)
print('population', len(c3))
pilot = set(open(T + '/E36/pilot/pilot.txt').read().split())
assert pilot <= set(c3)
rest = [h for h in c3 if h not in pilot]
random.Random(37).shuffle(rest)
out = T + '/E37/e37_rest.txt'
open(out, 'w').write('\n'.join(rest) + '\n')
print('rest', len(rest), 'batches', -(-len(rest) // 25000))
print(hashlib.sha256(open(out, 'rb').read()).hexdigest())
