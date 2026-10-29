# E22 TLD yield (read-only). usage: python3 scripts/E22/tld_yield.py DIR [MAXBATCHES] > VM.json
# Prints JSON: {tld: [hosts, imprint_found, host_not_found, deu, dach_postcode]} over status/imprint files in DIR.
import glob, gzip, json, re, sys, zlib
from collections import defaultdict

d = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 10**6
PLZ = re.compile(r"\b(?:D-|A-|CH-)?\d{4,5}\s+[A-ZÄÖÜ][a-zäöüß]+")
c = defaultdict(lambda: [0, 0, 0, 0, 0])
tld = lambda h: h.rsplit(".", 1)[-1].lower()
for f in sorted(glob.glob(f"{d}/fetch_status_batch*.tsv"))[:mx]:
    for line in open(f, errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) != 9 or p[0] == "host": continue
        r = c[tld(p[0])]; r[0] += 1
        r[1] += p[1] == "imprint_found"; r[2] += p[1] == "host_not_found"
    g = f.replace("fetch_status_batch", "imprints_batch").replace(".tsv", ".jsonl.gz")
    try:
        for line in gzip.open(g, "rt", errors="replace"):
            try: o = json.loads(line)
            except ValueError: continue
            i = o.get("impressum") or {}
            r = c[tld(o["host"])]
            r[3] += i.get("content_language") == "deu"
            r[4] += bool(PLZ.search(i.get("main_content") or ""))
    except (OSError, EOFError, zlib.error):
        pass  # batch still being written
print(json.dumps(c))
