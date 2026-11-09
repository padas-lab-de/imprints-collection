import random

import os  # D47: path constants below can be overridden by env
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
allh = [l.strip() for l in open(f'{T}/E42/shopify_all.txt') if l.strip()]
ex = set()
for f in ('E42/pilot100.txt', 'd31/shopify_pilot.txt', 'E45/listA.txt', 'E45/listB.txt'):
    ex |= set(l.strip() for l in open(f'{T}/{f}') if l.strip())
pool = sorted(set(allh) - ex)
random.seed(46)
L = random.sample(pool, 100)
assert not set(L) & ex and len(set(L)) == 100
open(f'{T}/E46/list.txt', 'w').write('\n'.join(L) + '\n')
print('pool', len(pool), 'excluded', len(ex), 'drawn', len(L))
