import gzip, json, sys, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "src")
from ic.cli import fetch

R = "/home/dinzinger/GitHub/imprints-collection/"
S = "/home/dinzinger/GitHub/imprints-collection/results/E6/"


def load(p):
    d = {}
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for l in f:
            r = json.loads(l)
            d[r["host"]] = r
    return d


old = load(R + "datasets/E4/random20k/imprints_batch000000.jsonl.gz")
new = load(R + "datasets/E6/random20k/imprints_batch000000.jsonl.gz")
sets = json.load(open(S + "sets.json"))
lost = sets["lost"]
extra = ["schuetzen-salzkotten.de", "www.bsv-heinsberg.de", "www.car-art-work.de"]


def dbg(h):
    out = {"host": h}
    o = old.get(h, {}).get("impressum")
    out["old_url"] = o and o["url"]
    out["old_main_url"] = old.get(h, {}).get("main", {}).get("url")
    oi = old.get(h, {}).get("impressum") or {"url": "x:", "main_content": "?"}
    out["old_is_landing_url"] = fetch.same_page(oi["url"], old[h]["main"]["url"]) if "impressum" in old[h] else None
    out["old_text_eq_landing"] = oi["main_content"].strip() == old[h]["main"].get("main_content", "").strip()
    out["old_text_none"] = oi["main_content"].strip() == "None"
    out["in_new"] = h in new
    out["new_main_url"] = new.get(h, {}).get("main", {}).get("url")
    # live landing
    for scheme in ["https://", "http://"]:
        u, html = fetch.try_fetch(scheme + h)
        if html:
            break
    out["live_landing"] = bool(html)
    if html:
        tree, pr = fetch.parse_html(html)
        kl, _ = fetch.discover_links(tree.body, u, h, base_href=fetch.get_base_href(tree))
        out["live_candidates"] = kl.get("impressum", [])[:5]
        out["old_url_in_cands"] = any(o and c[0] == o["url"] for c in kl.get("impressum", []))
        im = fetch.find_imprint(u, pr["main_content"], kl.get("impressum", []))
        out["live_found"] = im and (im["url"], im["found_by"])
    if o:
        su, sh = fetch.try_fetch(o["url"])
        out["old_url_now_fetch"] = bool(sh)
    return out


with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(dbg, lost + extra))
json.dump(res, open(S + "lossdebug.json", "w"), indent=1, ensure_ascii=False)
for r in res:
    print(json.dumps(r, ensure_ascii=False)[:600])
