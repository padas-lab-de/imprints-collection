"""Search the topic schemas for labelling.

    python3 -I scripts/E51/nodes.py poi <word> [<word> ...]   nodes whose id/English/German name has all words
    python3 -I scripts/E51/nodes.py wz <word> [<word> ...]    nodes whose code/title/keywords have all words
    python3 -I scripts/E51/nodes.py poi --node <id>           node, path, children
    python3 -I scripts/E51/nodes.py wz --node <code> [--full] node, path, children (--full: includes/excludes)
    python3 -I scripts/E51/nodes.py poi --roots | wz --roots  top level
Run from the repository root.
"""

import json
import sys

ROOT = "."


def load(schema):
    if schema == "poi":
        rows = [json.loads(l) for l in open(f"{ROOT}/topics/poi_v3.jsonl", encoding="utf-8")]
        nodes = {r["id"]: r for r in rows}
        par = {r["id"]: (None if r["parent"] == r["id"] else r["parent"]) for r in rows}
        label = {k: f"{v['name']} ({v.get('de', '')})" for k, v in nodes.items()}
        text = {k: f"{k} {v['name']} {v.get('de', '')}".lower() for k, v in nodes.items()}
    else:
        rows = [json.loads(l) for l in open(f"{ROOT}/topics/wz2025.jsonl", encoding="utf-8")]
        nodes = {r["code"]: r for r in rows}
        par = {r["code"]: r["parent"] for r in rows}
        label = {k: v["title"] for k, v in nodes.items()}
        text = {k: f"{k} {v['title']} {' '.join(v.get('keywords') or [])}".lower() for k, v in nodes.items()}
    kids = {}
    for k, p in par.items():
        if p is not None:
            kids.setdefault(p, []).append(k)
    return nodes, par, label, text, kids


def path(par, n):
    p = [n]
    while par[p[-1]] is not None:
        p.append(par[p[-1]])
    return p[::-1]


def main():
    schema, args = sys.argv[1], sys.argv[2:]
    nodes, par, label, text, kids = load(schema)
    fmt = lambda k: f"{k}  [{' > '.join(label[x] for x in path(par, k))}]{'  (leaf)' if k not in kids else ''}"  # noqa: E731
    if args and args[0] == "--roots":
        for k in nodes:
            if par[k] is None:
                print(fmt(k))
        return
    if args and args[0] == "--node":
        k = args[1]
        if k not in nodes:
            print(f"unknown node {k}")
            return
        print(fmt(k))
        if schema == "wz":
            kw = nodes[k].get("keywords") or []
            if kw:
                print("keywords: " + "; ".join(kw[:60]) + (" ..." if len(kw) > 60 else ""))
            if "--full" in args:
                for f in ("includes", "excludes"):
                    if nodes[k].get(f):
                        print(f"{f}: {nodes[k][f]}")
        for c in kids.get(k, []):
            print("  child: " + fmt(c))
        return
    words = [w.lower() for w in args]
    hits = [k for k in nodes if all(w in text[k] for w in words)]
    for k in hits[:60]:
        print(fmt(k))
    if len(hits) > 60:
        print(f"... {len(hits)} hits, refine")
    if not hits:
        print("no hits")


if __name__ == "__main__":
    main()
