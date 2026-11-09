import collections
c = collections.Counter(); t = collections.Counter()
for l in open('/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E40/out/flagged_sites.tsv').read().splitlines()[1:]:
    s, cat, n, tg = l.split('\t'); c[cat] += 1
    if tg == '1': t[cat] += 1
print(c, t)
