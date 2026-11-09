"""E48-shopify-full-crawl (D45): all Shopify hosts not fetched yet, split into 5 parts, one per VM."""
import random

import os  # D47: path constants below can be overridden by env
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
W = os.environ.get("W", "/home/dinzinger/E48-shopify")
VMS = ['apfel', 'aspe', 'abelie', 'mispel', 'lorbeer']
allh = [l.strip() for l in open(f'{T}/E42/shopify_all.txt') if l.strip()]
ex = set()
for f in ('E42/pilot100.txt', 'd31/shopify_pilot.txt', 'E45/listA.txt', 'E45/listB.txt', 'E46/list.txt', 'E47/list.txt'):
    ex |= set(l.strip() for l in open(f'{T}/{f}') if l.strip())
pool = sorted(set(allh) - ex)
random.seed(48)
random.shuffle(pool)
parts = {vm: pool[i::len(VMS)] for i, vm in enumerate(VMS)}
assert sum(len(p) for p in parts.values()) == len(pool)
for vm, p in parts.items():
    open(f'{W}/list_{vm}.txt', 'w').write('\n'.join(p) + '\n')
    print(vm, len(p))
open(f'{W}/list_all.txt', 'w').write('\n'.join(sorted(pool)) + '\n')
print('all', len(set(allh)), 'excluded', len(ex & set(allh)), 'pool', len(pool))
