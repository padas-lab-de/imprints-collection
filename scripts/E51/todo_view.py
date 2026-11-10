"""Print a compact view of a todo file from refs_agree.py (for adjudication).

Usage: python3 -I scripts/E51/todo_view.py <todo.jsonl>
"""

import json
import sys


def row(a):
    if not isinstance(a, dict):
        return str(a)
    if "addresses" not in a:
        keep = {k: a.get(k) for k in ("main", "extra", "online_only", "confidence", "note") if k in a}
        return json.dumps(keep, ensure_ascii=False)
    out = []
    for i, r in enumerate(a.get("addresses") or []):
        star = "*" if i == a.get("main_address_index") else " "
        out.append(
            f"   {star}{i} {r.get('role')}: {r.get('street')} | {r.get('number')} | "
            f"{r.get('postcode')} | {r.get('town')} | {r.get('country')} po={r.get('po_box')}"
        )
    out.append(
        f"    reason={a.get('no_address_reason')} flags={a.get('flags')} "
        f"conf={a.get('confidence')} note={a.get('note')}"
    )
    return "\n".join(out)


def main():
    for line in open(sys.argv[1], encoding="utf-8"):
        d = json.loads(line)
        print("==", d["host"])
        for p in ("A", "B"):
            print(f"  {p}:")
            print(row(d.get(p)))


if __name__ == "__main__":
    main()
