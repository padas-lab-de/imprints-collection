"""E14: per-parent frontier. The fetcher's discovered_external_hosts.txt has no parent tag, so
re-fetch the landing page of a random sample of reachable hosts of one round (4 threads) and count
the new candidate hosts (candidates.py rules) per parent, by parent group (.de/.at/.ch vs other)
and child group.

Usage: PYTHONPATH=src python scripts/E14/frontier_sample.py ROUND_JSONL FETCHED_LIST EARLIER_LIST... --n N --out OUT.json
EARLIER_LIST files: hosts fetched in this and earlier rounds (round-0 seeds are covered by seed list).
"""
import argparse
import gzip
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from resiliparse.parse.html import HTMLTree

from ic.cli import fetch as cur

R = Path("/home/dinzinger/GitHub/imprints-collection")
src = (Path(__file__).resolve().parent.parent / "E10/candidates.py").read_text()
exec(src[src.index("PLATFORMS = {"):src.index("def tld(h):")])

ap = argparse.ArgumentParser()
ap.add_argument("jsonl")
ap.add_argument("--earlier", nargs="*", default=[])
ap.add_argument("--n", type=int, default=600)
ap.add_argument("--out", required=True)
a = ap.parse_args()


def variants(h):
    return {h[4:]} if h.startswith("www.") else {"www." + h}


def g(h):
    return "cc" if h.rsplit(".", 1)[-1] in ("de", "at", "ch") else "other"


with gzip.open(R / "seed_hosts.txt.gz", "rt", encoding="utf-8") as f:
    seeds = {l.strip().lower() for l in f if l.strip()}
earlier = set()
for p in a.earlier:
    earlier |= {l.strip().lower() for l in open(p) if l.strip()}
hosts = []
for fp in sorted(Path(a.jsonl).parent.glob("imprints_batch*.jsonl.gz")):
    with gzip.open(fp, "rt", encoding="utf-8") as f:
        for line in f:
            hosts.append(json.loads(line)["host"])
earlier |= set(hosts)
random.seed(20261023)
sample = random.sample(hosts, min(a.n, len(hosts)))


def one(h):
    for scheme in ("https://", "http://"):
        url, html = cur.try_fetch(scheme + h, retry=True)
        if url and html:
            tree = HTMLTree.parse(html)
            if not tree or not tree.body:
                return h, None
            ext = cur.discover_links(tree.body, url, h, base_href=cur.get_base_href(tree))[1]
            new = [
                x for x in ext
                if x.lower() not in seeds and not (variants(x.lower()) & seeds)
                and x.lower() not in earlier and not (variants(x.lower()) & earlier)
                and not platform(x.lower())
            ]
            return h, {"ext": len(ext), "new": sorted(new)}
    return h, None


with ThreadPoolExecutor(4) as ex:
    res = dict(ex.map(one, sample))
ok = {h: r for h, r in res.items() if r}
json.dump(res, open(a.out, "w"))
print("sampled", len(sample), "landing page ok", len(ok))
for pg in ("cc", "other", "all"):
    rs = [r for h, r in ok.items() if pg == "all" or g(h) == pg]
    if not rs:
        continue
    n = len(rs)
    new = sum(len(r["new"]) for r in rs)
    newcc = sum(1 for r in rs for x in r["new"] if g(x) == "cc")
    print(f"parents {pg}: {n}; external/parent {sum(r['ext'] for r in rs)/n:.2f}; new/parent {new/n:.3f}; new cc children/parent {newcc/n:.3f}")
