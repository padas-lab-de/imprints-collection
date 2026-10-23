import json, collections

r = json.load(open("/home/dinzinger/GitHub/imprints-collection/results/E6/lossdebug.json"))
L = r[:-3]
cat = collections.Counter()
ex = collections.defaultdict(list)
for x in L:
    if x["old_text_none"]:
        c = "1 old imprint was a PDF/binary decoded as the text 'None'"
    elif x["old_is_landing_url"]:
        c = "2 old imprint = landing page itself (fragment/self link)"
    elif x["old_text_eq_landing"]:
        c = "3 old imprint text identical to landing text (shell/SPA)"
    elif not x["in_new"] and not x["live_landing"]:
        c = "4 host unreachable in E6 run and when re-checked"
    elif not x["in_new"] and x.get("live_found"):
        c = "5 host unreachable in E6 run, imprint found when re-checked (transient)"
    elif x["in_new"] and x.get("live_found"):
        c = "6 host reachable, no imprint in E6 run, found when re-checked (transient)"
    else:
        c = "7 other (site down/403/changed when re-checked)"
    cat[c] += 1
    ex[c].append(x["host"])
for k in sorted(cat):
    print(cat[k], k, ex[k][:5])
print(sum(cat.values()))
