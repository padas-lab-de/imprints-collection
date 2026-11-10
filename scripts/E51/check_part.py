"""Check a raw label part file (one pass) for the labeller.

    python3 -I scripts/E51/check_part.py poi  <hosts.txt> <part.jsonl>
    python3 -I scripts/E51/check_part.py wz   <hosts.txt> <part.jsonl>
    python3 -I scripts/E51/check_part.py addr <hosts.txt> <part.jsonl> <inputs.jsonl>
Exit 0 and "OK" when the file is valid. Run from the repository root.
"""

import json
import re
import sys

ROLES = ("operator", "operator_other_site", "representative", "editor", "agency", "host", "other")
MAIN_ROLES = ("operator", "operator_other_site", "representative", "editor")
FLAGS = ("multi_address", "po_box", "obfuscated", "non_dach", "not_verbatim")
ADDR_FIELDS = ("street", "number", "postcode", "town", "country", "evidence")


def ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def schema_parents(schema):
    if schema == "poi":
        rows = [json.loads(l) for l in open("topics/poi_v3.jsonl", encoding="utf-8")]
        return {r["id"]: (None if r["parent"] == r["id"] else r["parent"]) for r in rows}
    rows = [json.loads(l) for l in open("topics/wz2025.jsonl", encoding="utf-8")]
    return {r["code"]: r["parent"] for r in rows}


def ancestors(par, n):
    out = []
    while n is not None:
        out.append(n)
        n = par[n]
    return out


def check_topic(schema, r, par):
    errs = []
    keys = {"host", "schema", "main", "extra", "confidence", "note"} | ({"online_only"} if schema == "poi" else set())
    if set(r) != keys:
        errs.append(f"fields must be {sorted(keys)}, got {sorted(r)}")
    if r.get("schema") != ("poi3" if schema == "poi" else "wz"):
        errs.append("schema must be " + ("poi3" if schema == "poi" else "wz"))
    if r.get("confidence") not in ("high", "medium", "low"):
        errs.append("confidence")
    if schema == "poi" and not isinstance(r.get("online_only"), bool):
        errs.append("online_only must be true/false")
    m, ex = r.get("main"), r.get("extra")
    if not isinstance(ex, list) or len(ex) > 2 or len(set(ex)) != len(ex):
        errs.append("extra must be a list of at most 2 distinct ids")
        ex = []
    if m is None:
        if ex:
            errs.append("main null: extra must be empty")
        if not r.get("note"):
            errs.append("main null: note required")
        return errs
    if m not in par:
        return errs + [f"unknown main {m!r}"]
    anc = set(ancestors(par, m))
    for e in ex:
        if e not in par:
            errs.append(f"unknown extra {e!r}")
        elif e in anc:
            errs.append(f"R5: extra {e} is the main or an ancestor of it")
    return errs


def check_addr(r, text):
    errs = []
    keys = {"host", "addresses", "main_address_index", "no_address_reason", "flags", "confidence", "note"}
    if set(r) != keys:
        errs.append(f"fields must be {sorted(keys)}, got {sorted(r)}")
    hay = ws(text)
    addrs = r.get("addresses")
    if not isinstance(addrs, list):
        return errs + ["addresses must be a list"]
    flags = r.get("flags") or []
    if not isinstance(flags, list) or any(f not in FLAGS for f in flags):
        errs.append(f"flags must come from {FLAGS}")
    for i, a in enumerate(addrs):
        pre = f"address {i}: "
        akeys = {"role", "street", "number", "postcode", "town", "country", "po_box", "modality", "evidence"}
        if not isinstance(a, dict) or set(a) != akeys:
            errs.append(pre + f"fields must be {sorted(akeys)}")
            continue
        if a["role"] not in ROLES:
            errs.append(pre + "role")
        if a["modality"] != "text":
            errs.append(pre + "modality must be text")
        if not isinstance(a["po_box"], bool):
            errs.append(pre + "po_box bool")
        if not (ws(a["street"]) or ws(a["postcode"]) or ws(a["town"])):
            errs.append(pre + "needs street, postcode or town")
        if not ws(a["evidence"]):
            errs.append(pre + "evidence required")
        if "not_verbatim" not in flags:
            for k in ADDR_FIELDS:
                v = ws(a.get(k))
                if v and v not in hay:
                    errs.append(pre + f"{k} {v[:50]!r} not verbatim in imprint_text")
            ev = ws(a["evidence"])
            for k in ("street", "number", "postcode", "town"):
                v = ws(a.get(k))
                if v and ev and v not in ev:
                    errs.append(pre + f"{k} {v!r} not inside evidence")
    mi, reason = r.get("main_address_index"), r.get("no_address_reason")
    if mi is not None:
        if not isinstance(mi, int) or isinstance(mi, bool) or not 0 <= mi < len(addrs):
            errs.append("main_address_index must point to a listed address")
        elif addrs[mi].get("role") not in MAIN_ROLES:
            errs.append(f"main address role must be in {MAIN_ROLES}")
        if reason is not None:
            errs.append("no_address_reason must be null when a main address exists")
    else:
        if reason not in ("no_imprint", "imprint_without_address"):
            errs.append("no main address: no_address_reason must be no_imprint or imprint_without_address")
        if any(a.get("role") in MAIN_ROLES for a in addrs if isinstance(a, dict)):
            errs.append("a row has a main role but main_address_index is null")
        if reason == "no_imprint" and addrs:
            errs.append("no_imprint with listed addresses")
    if r.get("confidence") not in ("high", "medium", "low"):
        errs.append("confidence")
    return errs


def main():
    kind, hosts_file, part = sys.argv[1:4]
    hosts = [l.strip() for l in open(hosts_file, encoding="utf-8") if l.strip()]
    texts = {}
    if kind == "addr":
        for l in open(sys.argv[4], encoding="utf-8"):
            x = json.loads(l)
            texts[x["host"]] = x.get("imprint_text") or ""
    par = schema_parents(kind) if kind in ("poi", "wz") else None
    errs, seen = [], []
    for n, l in enumerate(open(part, encoding="utf-8"), 1):
        if not l.strip():
            continue
        try:
            r = json.loads(l)
        except json.JSONDecodeError as e:
            errs.append(f"line {n}: bad JSON ({e})")
            continue
        h = r.get("host")
        seen.append(h)
        e = check_topic(kind, r, par) if par is not None else check_addr(r, texts.get(h, ""))
        errs += [f"{h}: {x}" for x in e]
    if len(seen) != len(set(seen)):
        errs.append("duplicate hosts")
    miss, extra = set(hosts) - set(seen), set(seen) - set(hosts)
    if miss:
        errs.append(f"missing hosts: {sorted(miss)}")
    if extra:
        errs.append(f"hosts not in the part list: {sorted(extra)}")
    print("\n".join(errs) if errs else f"OK: {len(seen)} lines")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
