"""Shared helpers for E51 reference building (stdlib only). Run scripts from the repository root."""

import glob
import json
import re

SETS = {  # set name -> (hosts file, inputs file, part prefix)
    "dev2": ("results/E51/dev2_hosts.txt", "datasets/E51/dev2_inputs.jsonl", "d2"),
    "heldout2": ("results/E51/heldout2_hosts.txt", "datasets/E51/heldout2_inputs.jsonl", "h2"),
    "e49": ("results/E51/e49_hosts.txt", "datasets/E51/e49_inputs.jsonl", "e49a"),
}
TASKS = ("poi", "wz", "addr")
MAIN_ROLES = ("operator", "operator_other_site", "representative", "editor")


def hosts(set_name):
    return [l.strip() for l in open(SETS[set_name][0], encoding="utf-8") if l.strip()]


def inputs(set_name):
    return {r["host"]: r for r in map(json.loads, open(SETS[set_name][1], encoding="utf-8"))}


def load_pass(p, task, set_name):
    """host -> raw line of pass p for task, from datasets/E51/refs_raw/<p>/<prefix>*_<task>.jsonl
    (topic parts d2NN/h2NN of 25 hosts, address parts d2aNN/h2aNN/e49aNN of 50 hosts)."""
    out = {}
    pre = SETS[set_name][2]
    for f in sorted(glob.glob(f"datasets/E51/refs_raw/{p}/{pre}*_{task}.jsonl")):
        for l in open(f, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                out[r["host"]] = r
    return out


def parents(task):
    if task == "poi":
        rows = [json.loads(l) for l in open("topics/poi_v3.jsonl", encoding="utf-8")]
        return {r["id"]: (None if r["parent"] == r["id"] else r["parent"]) for r in rows}
    rows = [json.loads(l) for l in open("topics/wz2025.jsonl", encoding="utf-8")]
    return {r["code"]: r["parent"] for r in rows}


def path(par, n):
    if n is None:
        return []
    p = [n]
    while par[p[-1]] is not None:
        p.append(par[p[-1]])
    return p[::-1]


def ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def tup(a):
    return tuple(ws(a.get(k)).lower() for k in ("street", "number", "postcode", "town"))


def addr_main(r):
    i = r.get("main_address_index")
    return ("main", tup(r["addresses"][i])) if i is not None else ("none", r.get("no_address_reason"))


def addr_ops(r):
    return frozenset(tup(a) for a in r["addresses"] if a["role"] == "operator")


def addr_all(r):
    return frozenset((a["role"], tup(a)) for a in r["addresses"])


def topic_agree(a, b):
    return a["main"] == b["main"]


def addr_agree(a, b):
    """Strict agreement used for agree_ab: same main (or same no-address reason) and same operator set."""
    return addr_main(a) == addr_main(b) and addr_ops(a) == addr_ops(b)
