"""Validate results/E49/refs/{poi,wz}.jsonl. Usage: python3 -I validate.py [ROOT]"""
import json, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else '/home/dinzinger/GitLab/fim/imprints-collection'
def load(fn, key):
    return {d[key]: d['parent'] for d in map(json.loads, open(fn))}
SCH = {'poi': load(f'{ROOT}/topics/poi_v2.jsonl', 'name'), 'wz': load(f'{ROOT}/topics/wz2025.jsonl', 'code')}
def path(par, n):
    p = [n]
    while par[p[-1]] is not None and par[p[-1]] != p[-1]: p.append(par[p[-1]])
    return p[::-1]
hosts = {l.strip() for l in open(f'{ROOT}/results/E49/dev_hosts.txt') if l.strip()}
FIELDS = {'host', 'schema', 'main', 'extra', 'path', 'confidence', 'note', 'agree_ab'}
errs = []
for s, par in SCH.items():
    rows = [json.loads(l) for l in open(f'{ROOT}/results/E49/refs/{s}.jsonl')]
    seen = [r['host'] for r in rows]
    if len(seen) != len(set(seen)): errs.append(f'{s}: duplicate hosts')
    if set(seen) != hosts: errs.append(f'{s}: host set != dev_hosts ({len(set(seen) ^ hosts)} differ)')
    ch = {}
    for k, v in par.items():
        if v is not None and v != k: ch.setdefault(v, []).append(k)
    for r in rows:
        h = r['host']; want = FIELDS | ({'online_only'} if s == 'poi' else set())
        if set(r) != want: errs.append(f'{s} {h}: fields {sorted(set(r) ^ want)}')
        if r['schema'] != s: errs.append(f'{s} {h}: schema field')
        if r['confidence'] not in ('high', 'medium', 'low'): errs.append(f'{s} {h}: confidence')
        if not isinstance(r['agree_ab'], bool): errs.append(f'{s} {h}: agree_ab not bool')
        if s == 'poi' and not isinstance(r.get('online_only'), bool): errs.append(f'{s} {h}: online_only not bool')
        m = r['main']
        if m is None:
            if r['path'] != [] or r['extra']: errs.append(f'{s} {h}: null main needs path [] and no extras')
            continue
        if m not in par: errs.append(f'{s} {h}: unknown main {m}'); continue
        if r['path'] != path(par, m): errs.append(f'{s} {h}: path {r["path"]} != {path(par, m)}')
        if s == 'wz' and m in ch and len(ch[m]) == 1: errs.append(f'{s} {h}: R6 single-child klasse {m}')
        ex = r['extra']
        if len(ex) > 2 or len(ex) != len(set(ex)): errs.append(f'{s} {h}: extras count/duplicates')
        anc = set(path(par, m))
        for e in ex:
            if e not in par: errs.append(f'{s} {h}: unknown extra {e}')
            elif e in anc: errs.append(f'{s} {h}: R5 extra {e} is main or ancestor')
    print(f'{s}: {len(rows)} lines, agree_ab true={sum(r["agree_ab"] for r in rows)}, main null={sum(r["main"] is None for r in rows)}'
          + (f', online_only true={sum(r["online_only"] for r in rows)}' if s == 'poi' else ''))
print('\n'.join(errs) if errs else 'OK: 0 errors')
sys.exit(1 if errs else 0)
