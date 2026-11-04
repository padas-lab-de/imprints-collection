#!/usr/bin/env python3
"""E31 extractor: compact (host, status, redirect target host) rows from one fetch output dir.

Stdlib only; read-only; streams one batch at a time (a few MB of memory).
Usage: python3 extract.py DIR > rows.tsv        (or: ssh VM nice -n 19 python3 - DIR < extract.py)

For every fetch_status_batchN.tsv in DIR (sorted by name, rows in file order, NO dedup here) one line
`host<TAB>status<TAB>target`. host is lowercased. target = lowercased host of `main.url` (the landing
URL after redirects, written by src/ic/cli/fetch.py) of the record in imprints_batchN.jsonl.gz, only
looked up for status imprint_found; empty if there is no record or no usable url. Rows with a wrong
column count (line being written) are skipped. A truncated gz (crawl running) keeps what was read.
Stats go to stderr as one `#stats` line (key=value).
"""

import gzip
import json
import re
import sys
import zlib
from pathlib import Path
from urllib.parse import urlsplit

NCOLS = 9
BATCH_RE = re.compile(r"fetch_status_batch(\d+)\.tsv$")
# json.dumps order: {"host": ..., "main": {"url": ...
FAST = re.compile(r'^\{"host": "((?:[^"\\]|\\.)*)", "main": \{"url": "((?:[^"\\]|\\.)*)"')


def host_of(url):
    try:
        h = urlsplit(url.strip()).hostname  # lowercased, port and userinfo removed
    except ValueError:
        return ""
    return (h or "").rstrip(".")


def unesc(s):
    return json.loads('"' + s + '"') if "\\" in s else s


def read_records(path, wanted, stats):
    """{host: main url} for hosts in `wanted` (a later record of a host wins)."""
    out = {}
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = FAST.match(line)
                if m:
                    h, u = unesc(m.group(1)).strip().lower(), unesc(m.group(2))
                else:
                    stats["slow"] += 1
                    try:
                        d = json.loads(line)
                        h, u = str(d["host"]).strip().lower(), str(d["main"]["url"])
                    except (ValueError, KeyError, TypeError):
                        stats["bad_record"] += 1
                        continue
                if h in wanted:
                    out[h] = u
    except (EOFError, zlib.error, OSError):
        stats["truncated_gz"] += 1
    return out


def main(d):
    stats = dict(files=0, rows=0, found=0, with_url=0, no_record=0, no_jsonl=0, slow=0, bad_record=0, truncated_gz=0)
    w = sys.stdout
    for p in sorted(Path(d).glob("fetch_status_batch*.tsv")):
        m = BATCH_RE.search(p.name)
        stats["files"] += 1
        rows = []
        with open(p, encoding="utf-8", newline="") as f:
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) != NCOLS or c[0] == "host":
                    continue
                rows.append((c[0].strip().lower(), c[1]))
        found = {h for h, s in rows if s == "imprint_found"}
        recs = {}
        jp = p.with_name(f"imprints_batch{m.group(1)}.jsonl.gz")
        if found:
            if jp.exists():
                recs = read_records(jp, found, stats)
            else:
                stats["no_jsonl"] += 1
        for h, s in rows:
            t = ""
            if s == "imprint_found":
                stats["found"] += 1
                u = recs.get(h)
                if u is None:
                    stats["no_record"] += 1
                else:
                    t = host_of(u)
                    stats["with_url"] += bool(t)
            stats["rows"] += 1
            w.write(f"{h}\t{s}\t{t}\n")
    print("#stats " + " ".join(f"{k}={v}" for k, v in stats.items()), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
