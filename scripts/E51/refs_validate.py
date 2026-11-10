"""Validate the E51 reference files (topics and addresses).

    python3 -I scripts/E51/refs_validate.py
Topics: ids exist, path = schema path, R5 extras, fields, adjudication notes, one line per host.
Addresses: fields, roles, main index, no_address_reason, and every non-empty field verbatim in the
input imprint_text (white space collapsed) unless the line has the flag not_verbatim.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_part import check_addr  # noqa: E402
from refs_common import hosts, inputs, parents, path  # noqa: E402

TOPIC_FILES = [("poi", "poi_v3", "dev2"), ("poi", "poi_v3", "heldout2"), ("wz", "wz", "dev2"), ("wz", "wz", "heldout2")]
ADDR_FILES = ["dev2", "heldout2", "e49"]


def check_topics(task, name, s, errs):
    par = parents(task)
    fields = {"host", "schema", "main", "extra", "path", "confidence", "note", "agree_ab"} | (
        {"online_only"} if task == "poi" else set())
    rows = [json.loads(l) for l in open(f"results/E51/refs/{name}_{s}.jsonl", encoding="utf-8")]
    hs = [r["host"] for r in rows]
    if hs != hosts(s):
        errs.append(f"{name}_{s}: host list != {s} hosts")
    for r in rows:
        h, pre = r["host"], f"{name}_{s} {r['host']}: "
        if set(r) != fields:
            errs.append(pre + f"fields {sorted(set(r) ^ fields)}")
        if r["schema"] != ("poi3" if task == "poi" else "wz"):
            errs.append(pre + "schema")
        if r["confidence"] not in ("high", "medium", "low"):
            errs.append(pre + "confidence")
        if not isinstance(r["agree_ab"], bool) or (task == "poi" and not isinstance(r["online_only"], bool)):
            errs.append(pre + "bool fields")
        if not r["agree_ab"] and not r["note"].startswith("adjudicated:"):
            errs.append(pre + "adjudication note")
        m = r["main"]
        if m is None:
            if r["path"] or r["extra"]:
                errs.append(pre + "null main needs path [] and no extras")
            continue
        if m not in par:
            errs.append(pre + f"unknown main {m}")
            continue
        if r["path"] != path(par, m):
            errs.append(pre + "path")
        ex = r["extra"]
        if len(ex) > 2 or len(set(ex)) != len(ex):
            errs.append(pre + "extras count/duplicates")
        for e in ex:
            if e not in par:
                errs.append(pre + f"unknown extra {e}")
            elif e in path(par, m):
                errs.append(pre + f"R5 extra {e}")
    return rows


def check_addrs(s, errs):
    txt = {h: r.get("imprint_text") or "" for h, r in inputs(s).items()}
    rows = [json.loads(l) for l in open(f"results/E51/refs/addr_{s}.jsonl", encoding="utf-8")]
    if [r["host"] for r in rows] != hosts(s):
        errs.append(f"addr_{s}: host list != {s} hosts")
    for r in rows:
        h = r["host"]
        core = {k: v for k, v in r.items() if k != "agree_ab"}
        errs += [f"addr_{s} {h}: {e}" for e in check_addr(core, txt.get(h, ""))]
        if not isinstance(r.get("agree_ab"), bool):
            errs.append(f"addr_{s} {h}: agree_ab")
        elif not r["agree_ab"] and not r["note"].startswith("adjudicated:"):
            errs.append(f"addr_{s} {h}: adjudication note")
    return rows


def main():
    errs, report = [], []
    only = sys.argv[1] if len(sys.argv) > 1 else None  # optional: topics or addr
    for task, name, s in TOPIC_FILES if only != "addr" else []:
        rows = check_topics(task, name, s, errs)
        report.append(f"{name}_{s}: {len(rows)} lines, agree_ab {sum(r['agree_ab'] for r in rows)}, "
                      f"main null {sum(r['main'] is None for r in rows)}"
                      + (f", online_only {sum(r['online_only'] for r in rows)}" if task == "poi" else ""))
    for s in ADDR_FILES if only != "topics" else []:
        rows = check_addrs(s, errs)
        report.append(f"addr_{s}: {len(rows)} lines, agree_ab {sum(r['agree_ab'] for r in rows)}, "
                      f"with main {sum(r['main_address_index'] is not None for r in rows)}, "
                      f"no_imprint {sum(r['no_address_reason'] == 'no_imprint' for r in rows)}, "
                      f"imprint_without_address {sum(r['no_address_reason'] == 'imprint_without_address' for r in rows)}, "
                      f"not_verbatim {sum('not_verbatim' in r['flags'] for r in rows)}")
    print("\n".join(report))
    print("\n".join(errs) if errs else "OK: 0 errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
