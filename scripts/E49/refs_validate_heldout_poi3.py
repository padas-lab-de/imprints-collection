"""Validate results/E49/heldout/refs/poi_v3.jsonl against topics/poi_v3.jsonl. Usage: python3 -I refs_validate_heldout_poi3.py [ROOT]"""
import json, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
par = {d['id']: d['parent'] for d in map(json.loads, open(f'{ROOT}/topics/poi_v3.jsonl'))}
def path(n):
    p = [n]
    while par[p[-1]] != p[-1]: p.append(par[p[-1]])
    return p[::-1]
hosts = {l.strip() for l in open(f'{ROOT}/results/E49/heldout/hosts.txt') if l.strip()}
FIELDS = {'host', 'schema', 'main', 'extra', 'path', 'confidence', 'note', 'agree_ab', 'online_only'}
errs = []
rows = [json.loads(l) for l in open(f'{ROOT}/results/E49/heldout/refs/poi_v3.jsonl')]
seen = [r['host'] for r in rows]
if len(seen) != len(set(seen)): errs.append('duplicate hosts')
if set(seen) != hosts: errs.append(f'host set != hosts.txt ({len(set(seen) ^ hosts)} differ)')
for r in rows:
    h = r['host']
    if set(r) != FIELDS: errs.append(f'{h}: fields {sorted(set(r) ^ FIELDS)}')
    if r['schema'] != 'poi3': errs.append(f'{h}: schema')
    if r['confidence'] not in ('high', 'medium', 'low'): errs.append(f'{h}: confidence')
    if not isinstance(r['agree_ab'], bool) or not isinstance(r['online_only'], bool): errs.append(f'{h}: bool fields')
    m = r['main']
    if m is None:
        if r['path'] != [] or r['extra']: errs.append(f'{h}: null main needs path [] and no extras')
        continue
    if m not in par: errs.append(f'{h}: unknown main {m}'); continue
    if r['path'] != path(m): errs.append(f'{h}: path {r["path"]} != {path(m)}')
    ex = r['extra']
    if len(ex) > 2 or len(ex) != len(set(ex)): errs.append(f'{h}: extras count/duplicates')
    for e in ex:
        if e not in par: errs.append(f'{h}: unknown extra {e}')
        elif e in set(path(m)): errs.append(f'{h}: R5 extra {e} is main or ancestor')
    if not r['agree_ab'] and not r['note'].startswith('adjudicated:'): errs.append(f'{h}: adjudication note')
print(f'{len(rows)} lines, agree_ab true={sum(r["agree_ab"] for r in rows)}, main null={sum(r["main"] is None for r in rows)}, online_only true={sum(r["online_only"] for r in rows)}')
print('\n'.join(errs) if errs else 'OK: 0 errors')
sys.exit(1 if errs else 0)
