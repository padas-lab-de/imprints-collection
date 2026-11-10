"""Check a topic schema JSONL ({"name", "parent"}; root: parent == name or null).

Also reads the v3 format ({"id", "name", "parent", ...}; root: parent == id): the node key is then "id",
and names must be unique too.

Checks: unique names, every parent exists, no cycles. Prints depth stats
(root = depth 0), inner/leaf counts and leaves per root. Exit code 1 on error.

Usage: python scripts/E49/check_poi_schema.py [topics/poi_v2.jsonl]
"""

import json
import sys
from collections import Counter


def main(path: str) -> int:
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    errors = []

    key = "id" if rows and "id" in rows[0] else "name"
    for k in sorted({key, "name"}):
        counts = Counter(r[k] for r in rows)
        for name, c in counts.items():
            if c > 1:
                errors.append(f"duplicate {k}: {name!r} ({c}x)")

    parent = {}
    for r in rows:
        p = r["parent"]
        parent[r[key]] = None if p is None or p == r[key] else p
    for name, p in parent.items():
        if p is not None and p not in parent:
            errors.append(f"missing parent: {name!r} -> {p!r}")

    depth, root_of = {}, {}
    for name in parent:
        seen, cur = [], name
        while cur is not None and cur in parent and cur not in seen:
            seen.append(cur)
            cur = parent[cur]
        if cur is not None and cur in seen:
            errors.append(f"cycle: {' -> '.join(seen + [cur])}")
            continue
        depth[name] = len(seen) - 1
        root_of[name] = seen[-1]

    children = Counter(p for p in parent.values() if p is not None)
    roots = [n for n, p in parent.items() if p is None]
    inner = [n for n in parent if children[n] and parent[n] is not None]
    leaves = [n for n in parent if not children[n]]

    print(f"file: {path}")
    print(f"nodes: {len(rows)}  roots: {len(roots)}  inner (non-root): {len(inner)}  leaves: {len(leaves)}")
    print(f"max depth: {max(depth.values()) if depth else 0}  depth histogram: {dict(sorted(Counter(depth.values()).items()))}")
    print(f"inner nodes: {inner}")
    print("leaves per root:")
    for r in roots:
        n_leaves = sum(1 for n in leaves if root_of.get(n) == r and n != r)
        print(f"  {r}: {n_leaves}" + ("  (EMPTY ROOT)" if not children[r] else ""))
    for r in roots:
        if not children[r]:
            errors.append(f"root without children: {r!r}")

    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "topics/poi_v2.jsonl"))
