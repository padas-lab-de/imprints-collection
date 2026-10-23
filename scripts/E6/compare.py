import collections
import gzip
import json
import random
import sys
from urllib.parse import urlparse

R = "/home/dinzinger/GitHub/imprints-collection/"
OLD = R + "datasets/E4/random20k/imprints_batch000000.jsonl.gz"
NEW = R + "datasets/E6/random20k/imprints_batch000000.jsonl.gz"
S = "/home/dinzinger/GitHub/imprints-collection/results/E6/"


def load(p):
    d = {}
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for l in f:
            r = json.loads(l)
            d[r["host"]] = r
    return d


old, new = load(OLD), load(NEW)
is_de = lambda h: h.endswith(".de")


def yields(d, sel=lambda h: True):
    hosts = [h for h in d if sel(h)]
    found = [h for h in hosts if "impressum" in d[h]]
    return len(found), len(hosts)


out = {}
for name, sel in [("all", lambda h: True), ("de", is_de)]:
    fo, ro = yields(old, sel)
    fn, rn = yields(new, sel)
    out[name] = dict(old_found=fo, old_reach=ro, new_found=fn, new_reach=rn)
    print(name, f"old {fo}/{ro}={fo/ro:.1%}  new {fn}/{rn}={fn/rn:.1%}")

# on hosts reachable in both
both = set(old) & set(new)
print("reachable in both", len(both), "only old", len(set(old) - set(new)), "only new", len(set(new) - set(old)))
fo = sum("impressum" in old[h] for h in both)
fn = sum("impressum" in new[h] for h in both)
print("on both-reachable: old", fo, "new", fn)

gained = sorted(h for h in new if "impressum" in new[h] and not ("impressum" in old.get(h, {})))
lost = sorted(h for h in old if "impressum" in old[h] and not ("impressum" in new.get(h, {})))
changed = sorted(
    h
    for h in new
    if "impressum" in new[h]
    and "impressum" in old.get(h, {})
    and new[h]["impressum"]["url"] != old[h]["impressum"]["url"]
)
from urllib.parse import urldefrag, urlparse
def norm(u):
    a = urlparse(urldefrag(u)[0])
    n = a.netloc.lower()
    n = n[4:] if n.startswith("www.") else n
    return (n, a.path.rstrip("/"), a.query)
subst = [h for h in changed if norm(new[h]["impressum"]["url"]) != norm(old[h]["impressum"]["url"])]
print("changed total", len(changed), "substantive (not just scheme/www/fragment/slash)", len(subst))
print("substantive changed: new host differs from old imprint host:", sum(norm(new[h]["impressum"]["url"])[0] != norm(old[h]["impressum"]["url"])[0] for h in subst))
print("substantive: rank>0", sum(new[h]["impressum"]["candidate_rank"] > 0 for h in subst), "keyword", collections.Counter(new[h]["impressum"]["found_keyword"] for h in subst).most_common(6))
print("gained", len(gained), "lost", len(lost), "changed", len(changed))
g_in_old_reach = [h for h in gained if h in old]
print("gained, was reachable before (no imprint):", len(g_in_old_reach), "; newly reachable:", len(gained) - len(g_in_old_reach))
print("lost: unreachable now:", sum(h not in new for h in lost), "reachable but no imprint:", sum(h in new for h in lost))


def rule(r):
    i = r["impressum"]
    k = i["found_keyword"]
    s = f"{i['found_by']}:{k}"
    if i.get("fallback_extraction"):
        s += "+fullbody"
    return s


print("gains by found_by:")
c = collections.Counter(new[h]["impressum"]["found_by"] for h in gained)
print(c)
print(collections.Counter(rule(new[h]) for h in gained).most_common())
print("all new found_by:", collections.Counter(new[h]["impressum"]["found_by"] for h in new if "impressum" in new[h]))
print("candidate_rank>0 among gained:", sum(new[h]["impressum"]["candidate_rank"] > 0 for h in gained))
print("gained .de:", sum(is_de(h) for h in gained))
# gains also by "newly reachable"
json.dump(dict(gained=gained, lost=lost, changed=changed, subst=subst), open(S + "sets.json", "w"))

# E5 hosts
rows = [json.loads(l) for l in open(R + "results/E5/classifications.jsonl")]
tgt = [r for r in rows if r["category"] in ("rule_miss", "no_link_but_url_exists")]
print("E5 target hosts", len(tgt))
tab = collections.defaultdict(lambda: [0, 0, 0])
detail = []
for r in tgt:
    h = r["host"]
    fix = r["fix"] or "none(wrong_candidate)"
    tab[fix][0] += 1
    rec = new.get(h)
    ok = bool(rec and "impressum" in rec)
    tab[fix][1] += ok
    tab[fix][2] += rec is None
    detail.append((fix, h, ok, rule(rec) if ok else ("unreachable" if rec is None else "no imprint")))
for fix, (n, ok, un) in sorted(tab.items()):
    print(fix, "n", n, "found now", ok, "unreachable in new run", un)
print("total found", sum(v[1] for v in tab.values()), "of", len(tgt))
for d in sorted(detail):
    print(d)
# other E5 categories now found
oth = collections.Counter()
for r in rows:
    if r["category"] not in ("rule_miss", "no_link_but_url_exists"):
        rec = new.get(r["host"])
        if rec and "impressum" in rec:
            oth[r["category"]] += 1
print("other E5 categories now found:", oth)

# precision sample
random.seed(20261023)
sg = random.sample(gained, min(50, len(gained)))
sc = random.sample(subst, min(20, len(subst)))
sample = []
for kind, hs in (("gained", sg), ("changed", sc)):
    for h in hs:
        i = new[h]["impressum"]
        sample.append(
            dict(
                host=h,
                kind=kind,
                new_url=i["url"],
                old_url=old[h]["impressum"]["url"] if kind == "changed" else None,
                found_by=i["found_by"],
                found_keyword=i["found_keyword"],
                candidate_rank=i["candidate_rank"],
                fallback_extraction=i["fallback_extraction"],
                text_head=i["main_content"][:600],
                old_text_head=old[h]["impressum"]["main_content"][:300] if kind == "changed" else None,
            )
        )
json.dump(sample, open(S + "sample.json", "w"), ensure_ascii=False, indent=1)
