#!/usr/bin/env python3
"""E19 report: what the recovery pass (second IP) won back, by original E16 failure cause.

Inputs: E16 status TSVs (to classify each recovery host by its original cause with the rule of
collect.py) and the recovery status TSVs (fetch_status_batch*.tsv in the recovery output dir).
Outcome per recovered host (its row in the recovery TSV):
  imprint_found      status imprint_found
  imprint_not_found  host reachable, no imprint (imprint_not_found, no_valid_html_tree, filtered, ...)
  still_failing      status host_not_found again
Hosts of the recovery list without a recovery row are "not_retried" (pass unfinished).
Hosts not selected by the rule (the 48 Strato gold hosts if they were not failing with a retryable
cause) are reported as cause "other_listed". Recovery rows are read as they are (partial files ok).
"""
import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect import ROOT, BATCH_SIZE, PRIORITY, classify, read_rows  # noqa: E402

OUTCOMES = ["imprint_found", "imprint_not_found", "still_failing", "not_retried"]


def outcome(status):
    if status == "imprint_found":
        return "imprint_found"
    if status == "host_not_found":
        return "still_failing"
    return "imprint_not_found"


def load_dir(path):
    rows = []
    for p in sorted(Path(path).glob("fetch_status_batch*.tsv")):
        rows.extend(read_rows(p))
    return rows


def report(e16_rows, recovery_rows, listed_hosts=None, include_throttled=False):
    """{cause: Counter(outcome)} over the recovery hosts; listed_hosts adds hosts without a recovery row."""
    cause_of = {}
    for r in e16_rows:
        c = classify(r, include_throttled)
        if c:
            cause_of[r["host"]] = c[0]
    rec = {}
    for r in recovery_rows:
        rec[r["host"]] = r["status"]  # the last row of a host wins
    hosts = set(rec) | set(listed_hosts or [])
    table = defaultdict(Counter)
    for h in hosts:
        cause = cause_of.get(h, "other_listed")
        table[cause][outcome(rec[h]) if h in rec else "not_retried"] += 1
    return table


def format_table(table):
    order = [c for c in PRIORITY + ["throttled", "other_listed"] if c in table]
    lines = ["cause\thosts\t" + "\t".join(OUTCOMES) + "\trecovered_pct"]
    tot = Counter()
    for c in order + ["total"]:
        cnt = tot if c == "total" else table[c]
        if c != "total":
            tot.update(cnt)
        n = sum(cnt.values())
        tried = n - cnt["not_retried"]
        pct = f"{100 * cnt['imprint_found'] / tried:.1f}" if tried else "-"
        lines.append(f"{c}\t{n}\t" + "\t".join(str(cnt[o]) for o in OUTCOMES) + f"\t{pct}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--e16-dir", default=str(ROOT / "datasets/E16/seeds"))
    ap.add_argument("--recovery-dir", default=str(ROOT / "datasets/E19/recovery"))
    ap.add_argument("--list", help="recovery host list; its hosts without a recovery row count as not_retried")
    ap.add_argument("--include-throttled", action="store_true", help="classify as collect.py --include-throttled")
    ap.add_argument("--out", help="write the table to this TSV")
    a = ap.parse_args(argv)
    listed = None
    if a.list:
        listed = [l.strip() for l in open(a.list) if l.strip()]
    table = report(load_dir(a.e16_dir), load_dir(a.recovery_dir), listed, a.include_throttled)
    text = format_table(table)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
