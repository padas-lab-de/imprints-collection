import duckdb, glob, hashlib
T = '/home/dinzinger/.claude/jobs/cfd8c2d0/tmp'
O = T + '/E30'
col = lambda h: (h.strip().lower()[4:] if h.strip().lower().startswith('www.') else h.strip().lower())
excl25 = {col(l) for l in open(T + '/E25/cc43_dach_new.txt') if l.strip()}
excl27 = set()
for f in sorted(glob.glob(T + '/E27/p[123]_*.txt')):
    excl27 |= {col(l) for l in open(f) if l.strip()}
c = duckdb.connect(); c.execute("SET memory_limit='1.5GB'")
rows = c.sql(f"select host,tld,n_crawls,pages200,pages_deu,dach from '{T}/E23/cc_german_candidates.parquet'").fetchall()
seen = {}
for r in rows: seen.setdefault(col(r[0]), r)
ok = lambda k: k not in excl25 and k not in excl27
p1pool = sorted(k for k, r in seen.items() if r[1] not in ('de','at','ch') and ok(k))
p2pool = sorted(k for k, r in seen.items() if r[1] in ('de','at','ch') and ok(k))
print('pools', len(p1pool), len(p2pool))
assert (len(p1pool), len(p2pool)) == (1051969, 515649)
rd = lambda f: {col(l) for l in open(f) if l.strip()}
pil = rd(T+'/E28/p1_other_tld.txt') | rd(T+'/E28/p2_old_dach.txt'); assert len(pil)==10000
e27 = rd(T+'/E27/pool_p1.txt')|rd(T+'/E27/pool_p2.txt')|rd(T+'/E27/pool_p3.txt')
e29 = rd(T+'/E29/e29_rest.txt')
blog = lambda k: k in ('blog.de','blogspot.de') or k.endswith(('.blogspot.de','.blog.de'))
cnt={}; rem={'pilot':0,'e27pool':0,'e29rest':0,'blog':0}; out=[]; s=set()
for src, pool in (('p2',p2pool),('p1',p1pool)):
    for k in pool:
        if k in pil: rem['pilot']+=1; continue
        if k in e27: rem['e27pool']+=1; continue
        if k in e29: rem['e29rest']+=1; continue
        if blog(k): rem['blog']+=1; continue
        assert k not in s; s.add(k); out.append((seen[k][0], src, seen[k][1])); cnt[src]=cnt.get(src,0)+1
open(O+'/e30_rest.txt','w').write(''.join(h+'\n' for h,_,_ in out))
open(O+'/e30_rest_source.tsv','w').write('host\tsource\ttld\n'+''.join(f'{h}\t{s_}\t{t}\n' for h,s_,t in out))
sha = hashlib.sha256(open(O+'/e30_rest.txt','rb').read()).hexdigest()
open(O+'/e30_rest.txt.sha256','w').write(sha+'  e30_rest.txt\n')
print(cnt, rem, 'total', len(out), 'batches', -(-len(out)//25000), sha)
