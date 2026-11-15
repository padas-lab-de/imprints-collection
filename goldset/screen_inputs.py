"""Gold-set build, step 3a: screen inputs for S1 from the stored crawl text (read only).

    python3 -I goldset/screen_inputs.py --crawl-root CRAWLS --sources sources.tsv [--hosts <data>/phase1_hosts.txt] [--procs 8]

Scans every imprints_batch*.jsonl.gz below CRAWLS once and keeps the records of S1 sites. sources.tsv has the
columns ``source`` and ``dir`` (dir relative to CRAWLS), in the order in which the crawls were counted
(the format of collection/crawl_sources.example.tsv). A file belongs to the first row whose dir contains it.
A record matches site s if the www-collapsed record host or the www-collapsed host of main.url (landing URL after
redirects; the canonical-site rule of the site count) equals s. Choice among several records of a site: a record
with an impressum page first, then a match through main.url (canonical), then the earlier source (sources.tsv
order), then the later batch of the same dir (ic fetch resume rule: last record wins).

Input record = evaluation/page_text.py record() (clean_text, 6,000 chars per field, title and description of the
landing page). Writes <data>/screen/inputs.jsonl (S1 order) and <data>/screen/inputs_missing.txt.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "evaluation"))
from common import DATA, norm_host  # noqa
from page_text import record  # noqa

FAST = re.compile(r'^\{"host": "((?:[^"\\]|\\.)*)"(?:, "main": \{"url": "((?:[^"\\]|\\.)*)")?')
_WANT: set[str] = set()
_ROOT = Path(".")
_SOURCES: list[tuple[str, str]] = []  # (source, dir relative to the crawl root), in count order


def read_sources(path: Path) -> list[tuple[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        p = line.split("\t")
        if p[0] == "source" and len(p) > 1 and p[1] == "dir":
            continue
        rows.append((p[0], p[1].strip("/")))
    return rows


def source_of(rel: str) -> tuple[int, str]:
    """(rank, source label) of a file path relative to the crawl root."""
    for i, (src, d) in enumerate(_SOURCES):
        if rel == d or rel.startswith(d + "/"):
            return i, src
    return len(_SOURCES), rel.split("/")[0]


def batch_no(p: Path) -> int:
    m = re.search(r"imprints_batch(\d+)", p.name)
    return int(m.group(1)) if m else 0


def _init(want, root, sources):
    global _WANT, _ROOT, _SOURCES
    _WANT, _ROOT, _SOURCES = want, root, sources


def scan(path: str) -> tuple[str, dict, dict]:
    p = Path(path)
    rel = str(p.relative_to(_ROOT))
    (srank, src), b = source_of(rel), batch_no(p)
    found: dict = {}
    st = {"lines": 0, "bad": 0, "truncated": 0}
    try:
        with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                st["lines"] += 1
                m = FAST.match(line)
                if not m:
                    continue
                hk = norm_host(m.group(1))
                tk = norm_host(m.group(2) or "")
                if hk not in _WANT and tk not in _WANT:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    st["bad"] += 1
                    continue
                tk = norm_host((r.get("main") or {}).get("url") or "")
                for k, via in ((tk, "target"), (hk, "host")):
                    if k not in _WANT:
                        continue
                    score = (0 if r.get("impressum") else 1, 0 if via == "target" else 1, srank, -b)
                    if k not in found or score < found[k][0]:
                        rec = record(r, rel)
                        rec["host"] = k
                        rec["meta"]["source"] = src
                        rec["meta"]["crawl_host"] = r.get("host")
                        rec["meta"]["match"] = via
                        rec["meta"]["has_impressum_page"] = bool(r.get("impressum"))
                        rec["meta"]["kontakt_url"] = (r.get("kontakt") or {}).get("url")
                        found[k] = (score, rec)
    except (EOFError, OSError, zlib.error):
        st["truncated"] = 1
    return rel, found, st


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crawl-root", required=True, help="folder with the ic fetch output dirs of all crawls")
    ap.add_argument("--sources", required=True, help="TSV source<TAB>dir, in count order")
    ap.add_argument("--hosts", default=str(DATA / "phase1_hosts.txt"))
    ap.add_argument("--out", default=str(DATA / "screen/inputs.jsonl"))
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    hosts = [l.strip() for l in open(a.hosts) if l.strip()]
    want = {norm_host(h) for h in hosts}
    root = Path(a.crawl_root)
    sources = read_sources(Path(a.sources))
    files = sorted(str(p) for p in root.rglob("imprints_batch*.jsonl.gz"))
    print(f"{len(hosts)} sites, {len(files)} files", flush=True)
    best: dict = {}
    tot = {"lines": 0, "bad": 0, "truncated": 0}
    with Pool(a.procs, initializer=_init, initargs=(want, root, sources)) as pool:
        for i, (rel, found, st) in enumerate(pool.imap_unordered(scan, files, chunksize=1)):
            for k, v in st.items():
                tot[k] += v
            if st["truncated"]:
                print(f"truncated: {rel}", flush=True)
            for k, (score, rec) in found.items():
                if k not in best or score < best[k][0]:
                    best[k] = (score, rec)
            if (i + 1) % 50 == 0:
                print(f"{i + 1}/{len(files)} files, {len(best)} sites found", flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    missing = []
    with out.open("w", encoding="utf-8") as f:
        for h in hosts:
            k = norm_host(h)
            if k in best:
                rec = best[k][1]
                rec["host"] = h
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            else:
                missing.append(h)
    (out.parent / "inputs_missing.txt").write_text("".join(h + "\n" for h in missing))
    n = len(hosts) - len(missing)
    noimp = sum(1 for _, r in best.values() if not r["imprint_text"])
    print(json.dumps({"sites": len(hosts), "found": n, "missing": len(missing), "empty_imprint_text": noimp, **tot}))


if __name__ == "__main__":
    main()
