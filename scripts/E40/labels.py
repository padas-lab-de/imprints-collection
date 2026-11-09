import glob, random, collections
fl = {}; S = {}
for fn in glob.glob('/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E40/scan/*.scan.tsv'):
    for line in open(fn, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) < 7: continue
        if c[1] == 'F': fl[c[0]] = c
        elif c[1] == 'S': S[c[0]] = c
cnt = collections.Counter((c[2], c[3]) for c in fl.values())
print('flagged hosts', len(fl), 'S hosts', len(S))
for k, v in cnt.most_common(): print(v, k)
rng = random.Random(5)
for lab in ['domain_kaufen', 'parked', 'registrar_placeholder', 'broker_brand', 'domain_investment', 'for_sale_title', 'make_offer', 'domain_zum_verkauf']:
    rows = [c for c in fl.values() if c[3] == lab]
    print('==', lab, len(rows))
    for c in rng.sample(rows, min(10, len(rows))):
        print('  ', c[0], '|', c[5][:50], '|', c[6][:110])
sflag = sum(1 for h in S if h in fl)
print('S flagged', sflag, 'S core flagged', sum(1 for h in S if h in fl and fl[h][2] in ('sale', 'park')))
