import glob, random, os

T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
allh = [l.strip() for l in open(f'{T}/E42/shopify_all.txt') if l.strip()]
ex = set(l.strip() for l in open(f'{T}/E42/pilot100.txt')) | set(l.strip() for l in open(f'{T}/d31/shopify_pilot.txt'))
pool = sorted(set(allh) - ex)
vm = {}
for f in glob.glob(f'{T}/E31/r3/in/*.tsv'):
    b = os.path.basename(f)
    if b == 'manifest.tsv':
        continue
    v = b.split('_')[0]
    if v not in ('mispel', 'apfel'):
        continue
    for l in open(f):
        h = l.split('\t')[0].strip()
        if h:
            vm.setdefault(h, set()).add(v)
random.seed(45)
random.shuffle(pool)
A = []
B = []
both = 0
for h in pool:
    if len(A) >= 100 and len(B) >= 100:
        break
    s = vm.get(h, set())
    if s == {'mispel', 'apfel'}:
        both += 1
        continue
    ok_a = 'mispel' not in s and len(A) < 100
    ok_b = 'apfel' not in s and len(B) < 100
    if ok_a and ok_b:
        (B if len(A) > len(B) else A).append(h)
    elif ok_a:
        A.append(h)
    elif ok_b:
        B.append(h)
print(len(pool), len(A), len(B), 'skipped both', both)
print('A on apfel', sum(1 for h in A if 'apfel' in vm.get(h, ())), 'B on mispel', sum(1 for h in B if 'mispel' in vm.get(h, ())),
      'A unknown', sum(1 for h in A if h not in vm), 'B unknown', sum(1 for h in B if h not in vm))
assert not set(A) & set(B)
open(f'{T}/E45/listA.txt', 'w').write('\n'.join(A) + '\n')
open(f'{T}/E45/listB.txt', 'w').write('\n'.join(B) + '\n')
