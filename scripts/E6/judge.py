import json, os

S = "/home/dinzinger/GitHub/imprints-collection/results/E6/"
s = json.load(open(S + "sample.json"))
bad = {
    1: "full-body fallback returned only nav and footer; imprint text not on the page",
    4: "parked domain; legal notice of the registrar (Key-Systems/brandshelter), not of the site",
    7: "product page about 'imprint methods' (promotional products), matched keyword in URL",
    12: "/legal page is a portfolio listing, no legal notice content",
    28: "imprint page exists but holds only unfilled template placeholders",
    30: "legal notice of the web designer (dc-softs.de), not of the site",
    34: "contact/team page linked as 'Imprint', no legal-notice data in the extracted text",
    36: "page text is a Laravel course teaser, no legal-notice content",
    37: "privacy policy of the hosting provider (hetzner.com), matched 'rechtliches'",
    49: "product page 'custom imprinted hitchpin', matched keyword in URL",
    60: "wiki article about 'Impressumspflicht'; correct imprint was external (old URL), own-host-first ordering picked the article",
    63: "unrelated external car dealer site, 96 characters of text",
    67: "links page labelled 'Links & Partner Impressum' in the nav; shortest-URL tie-break chose it over impressum.html",
}
doubt = {
    10: "imprint/privacy text served by the Anubis bot-protection endpoint of the site",
    16: "legal-notices hub page with a Legal Notice tab",
    25: "imprint of another organisation (de-strippkes-trekker.de) linked from the site",
    45: "Fraunhofer HHI legal notice for a project site hosted there",
}
os.makedirs("/home/dinzinger/GitHub/imprints-collection/results/E6", exist_ok=True)
with open("/home/dinzinger/GitHub/imprints-collection/results/E6/precision_sample.jsonl", "w") as f:
    for i, x in enumerate(s):
        x = dict(x)
        x["idx"] = i
        x["judgement"] = "bad" if i in bad else "correct"
        x["reason"] = bad.get(i)
        x["note"] = doubt.get(i)
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
g = [i for i in range(len(s)) if s[i]["kind"] == "gained"]
c = [i for i in range(len(s)) if s[i]["kind"] == "changed"]
print(len(g), len(c), sum(i not in bad for i in g), sum(i not in bad for i in c))
