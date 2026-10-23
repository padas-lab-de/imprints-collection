"""E11: run the E4 and the current discover_links on the same landing pages.

Usage: PYTHONPATH=src python scripts/E11/compare_discovery.py N OUT.json
Takes N random hosts of datasets/E4/random20k_seed_hosts.txt (seed 11), fetches each landing page
once with the current try_fetch (https, then http), and extracts external hosts with
(A) the E4 discover_links (git fe4963b), (B) E4 with links keyed by full URL instead of path,
(C) the current discover_links. Low concurrency (4 threads).
"""
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

from resiliparse.parse.html import HTMLTree

from ic.cli import fetch as cur
from ic.utils.filter_utils import check_url

R = "/home/dinzinger/GitHub/imprints-collection"
src = subprocess.run(
    ["git", "show", "fe4963b:src/ic/cli/fetch.py"], capture_output=True, text=True, check=True
).stdout
tmp = tempfile.NamedTemporaryFile("w", suffix="_e4fetch.py", delete=False)
tmp.write(src)
tmp.close()
spec = importlib.util.spec_from_file_location("e4fetch", tmp.name)
e4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e4)


def variant_b(body, base_url, base_host):
    """E4 logic, but keyed by absolute URL instead of URL path."""
    seen = {}
    for elem in body.get_elements_by_tag_name("a"):
        href = elem.getattr("href")
        if not href:
            continue
        abs_url = urljoin(base_url, href, allow_fragments=False)
        p = urlparse(abs_url)
        if not p.path:
            continue
        seen[abs_url] = p.netloc.lower()
    out = set()
    for h in seen.values():
        h = h.strip()
        if h and check_url(h, is_host=True) and h != base_host:
            out.add(h)
    return out


def one(host):
    for scheme in ("https://", "http://"):
        url, html = cur.try_fetch(scheme + host, retry=True)
        if url and html:
            tree = HTMLTree.parse(html)
            if not tree or not tree.body:
                return host, None
            a = e4.discover_links(tree.body, url, host)[1]
            b = variant_b(tree.body, url, host)
            c = cur.discover_links(tree.body, url, host, base_href=cur.get_base_href(tree))[1]
            n_a = len(tree.body.get_elements_by_tag_name("a"))
            return host, {"A": sorted(a), "B": sorted(b), "C": sorted(c), "n_a": n_a}
    return host, None


n, out = int(sys.argv[1]), sys.argv[2]
hosts = [l.strip() for l in open(f"{R}/datasets/E4/random20k_seed_hosts.txt") if l.strip()]
random.seed(11)
sample = random.sample(hosts, n)
with ThreadPoolExecutor(4) as ex:
    res = dict(ex.map(one, sample))
json.dump(res, open(out, "w"))
ok = {h: r for h, r in res.items() if r}
print("fetched", len(ok), "of", n)
for k in "ABC":
    print(k, "sum per-host", sum(len(r[k]) for r in ok.values()), "unique", len({x for r in ok.values() for x in r[k]}))
