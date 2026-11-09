import duckdb, random, glob, hashlib, os
T = '/home/dinzinger/.claude/jobs/cfd8c2d0/tmp'
O = T + '/E28'
col = lambda h: (h.strip().lower()[4:] if h.strip().lower().startswith('www.') else h.strip().lower())
excl25 = {col(l) for l in open(T + '/E25/cc43_dach_new.txt') if l.strip()}
e27 = {}
for f in sorted(glob.glob(T + '/E27/p[123]_*.txt')):
    e27[f] = {col(l) for l in open(f) if l.strip()}
excl27 = set().union(*e27.values())
pools = set()
for f in glob.glob(T + '/E27/pool_p*.txt'):
    pools |= {col(l) for l in open(f) if l.strip()}
print('excl25', len(excl25), 'excl27', len(excl27), [os.path.basename(f) for f in e27])
c = duckdb.connect(); c.execute("SET memory_limit='1.5GB'")
rows = c.sql(f"select host,tld,n_crawls,pages200,pages_deu,dach from '{T}/E23/cc_german_candidates.parquet'").fetchall()
txt = [l.strip() for l in open(T + '/E23/cc_german_candidates.txt') if l.strip()]
print('parquet rows', len(rows), 'txt', len(txt), 'same set', {r[0] for r in rows} == set(txt))
seen = {}
for r in rows:
    seen.setdefault(col(r[0]), r)
print('distinct collapsed', len(seen))
ok = lambda k: k not in excl25 and k not in excl27
p1pool = sorted(k for k, r in seen.items() if r[1] not in ('de', 'at', 'ch') and ok(k))
p2pool = sorted(k for k, r in seen.items() if r[1] in ('de', 'at', 'ch') and ok(k))
print('dach flag vs tld mismatch', sum(1 for r in rows if r[5] != (r[1] in ('de', 'at', 'ch'))))
print('pool sizes', len(p1pool), len(p2pool))
random.seed(28)
p1 = random.sample(p1pool, 5000)
s1 = set(p1)
p2 = random.sample([k for k in p2pool if k not in s1], 5000)
for n, L in (('p1_other_tld', p1), ('p2_old_dach', p2)):
    with open(f'{O}/{n}.txt', 'w') as f:
        f.write('\n'.join(seen[k][0] for k in L) + '\n')
    d = open(f'{O}/{n}.txt', 'rb').read()
    open(f'{O}/{n}.txt.sha256', 'w').write(hashlib.sha256(d).hexdigest() + '  ' + n + '.txt\n')
    print(n, len(L), hashlib.sha256(d).hexdigest(), len(d), 'in e27 pools', sum(1 for h in L if h in pools))
with open(f'{O}/pilot_meta.tsv', 'w') as f:
    f.write('host\tpilot\ttld\tpages_deu\tpages200\tn_crawls\n')
    for n, L in (('P1', p1), ('P2', p2)):
        for h in L:
            r = seen[h]
            f.write(f'{seen[h][0]}\t{n}\t{r[1]}\t{int(r[4])}\t{int(r[3])}\t{r[2]}\n')
print('overlap', len(set(p1) & set(p2)))
