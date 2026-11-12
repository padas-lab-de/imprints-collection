"""E53 step 3a: build the screen inputs for S1 from the stored crawl text (release package, read only).

    python3 -I scripts/E53/inputs.py [--hosts datasets/E53/phase1_hosts.txt] [--procs 8]

Scans every crawls/**/imprints_batch*.jsonl.gz of the release package once and keeps the records of S1 sites.
A record matches site s if the www-collapsed record host or the www-collapsed host of main.url (landing URL after
redirects; the D34 canonical rule) equals s. Choice among several records of a site: a record with an impressum
page first, then a match through main.url (canonical), then the earlier source (E31 manifest order), then the
later batch of the same dir (ic fetch resume rule: last record wins).

Input record = scripts/E51/build_sample.py record() (the E50 static-text form: clean_text, 6,000 chars per field,
title and description of the landing page). Writes datasets/E53/screen/inputs.jsonl (S1 order) and
datasets/E53/screen/inputs_missing.txt.
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
sys.path.insert(0, str(HERE.parent / "E51"))
from build_sample import record  # noqa: E402
from common import DATA, RELEASE, norm_host  # noqa: E402

FAST = re.compile(r'^\{"host": "((?:[^"\\]|\\.)*)"(?:, "main": \{"url": "((?:[^"\\]|\\.)*)")?')
ORDER = ["E16", "E19r1", "E19r2", "E22d1A", "E22d1B", "E22d2P", "E22d2R", "E25", "E26", "E27", "E28", "E29",
         "E30", "E33p", "E33", "E34", "E34r2", "E34r3", "E36", "E37", "E41/L4", "E41/L3", "E41/L1", "E41/L2", "E43",
         "E44", "E45", "E46", "E47"]

_WANT: set[str] = set()


def source_rank(rel: str) -> int:
    parts = rel.split("/")
    src = parts[0]
    if src == "E41":
        lvl = next((p.split("_")[0] for p in parts if re.match(r"L\d_", p)), "L9")
        src = f"E41/{lvl}"
    return ORDER.index(src) if src in ORDER else len(ORDER)


def batch_no(p: Path) -> int:
    m = re.search(r"imprints_batch(\d+)", p.name)
    return int(m.group(1)) if m else 0


def _init(want):
    global _WANT
    _WANT = want


def scan(path: str) -> tuple[str, dict, dict]:
    p = Path(path)
    rel = str(p.relative_to(RELEASE / "crawls"))
    srank, b = source_rank(rel), batch_no(p)
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
                        rec["meta"]["source"] = rel.split("/")[0]
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
    ap.add_argument("--hosts", default=str(DATA / "phase1_hosts.txt"))
    ap.add_argument("--out", default=str(DATA / "screen/inputs.jsonl"))
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    hosts = [l.strip() for l in open(a.hosts) if l.strip()]
    want = {norm_host(h) for h in hosts}
    files = sorted(str(p) for p in (RELEASE / "crawls").rglob("imprints_batch*.jsonl.gz"))
    print(f"{len(hosts)} sites, {len(files)} files", flush=True)
    best: dict = {}
    tot = {"lines": 0, "bad": 0, "truncated": 0}
    with Pool(a.procs, initializer=_init, initargs=(want,)) as pool:
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
