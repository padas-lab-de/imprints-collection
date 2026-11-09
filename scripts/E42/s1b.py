import pickle, collections, os
os.chdir('/home/dinzinger/.claude/jobs/cfd8c2d0/tmp')
found, skip = pickle.load(open('E42/p.pkl', 'rb'))
base = 'E31/r3/in/'
src = {}
for l in list(open(base + 'manifest.tsv'))[1:]:
    p = l.split('\t')
    src[p[3]] = p[0]


def n(h):
    h = h.strip().lower().rstrip('.')
    return h[4:] if h.startswith('www.') else h


ps = collections.defaultdict(set)
for f, s in skip.items():
    ps[src[f]] |= s
others = set().union(*ps.values())
left = {n(l) for l in open('d31/shopify_left.txt') if l.strip()}
ps['E19r2_left(D31)'] = left
allu = set()
print('%-18s %9s %9s' % ('source', 'hosts', 'not_found'))
for s, v in sorted(ps.items()):
    print('%-18s %9d %9d' % (s, len(v), len(v - found)))
    allu |= v
print('union', len(allu), 'minus found', len(allu - found), 'overlap with found', len(allu & found))
print('skipped_provider union', len(others), 'minus found', len(others - found))
print('left found', len(left & found), 'left not in skipped', len(left - others))
u = sorted(allu - found)
open('E42/shopify_all.txt', 'w').write('\n'.join(u) + '\n')
