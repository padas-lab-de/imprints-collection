"""Print the model input of hosts for labelling.

    python3 -I scripts/E51/show.py <inputs.jsonl> <host> [<host> ...]
    python3 -I scripts/E51/show.py <inputs.jsonl> --list <hosts.txt>   (all hosts of a part list)
    add --imprint-only to print only the imprint text (address passes)
"""

import json
import sys


def main() -> None:
    args = sys.argv[1:]
    imp_only = "--imprint-only" in args
    args = [a for a in args if a != "--imprint-only"]
    path, rest = args[0], args[1:]
    if rest and rest[0] == "--list":
        hosts = [l.strip() for l in open(rest[1], encoding="utf-8") if l.strip()]
    else:
        hosts = rest
    recs = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l)
        recs[r["host"]] = r
    for h in hosts:
        r = recs.get(h)
        if r is None:
            print(f"=== {h}: NOT IN INPUT FILE")
            continue
        m = r.get("meta", {})
        print(f"=== HOST {h}")
        if not imp_only:
            print(f"title: {m.get('title', '')}")
            print(f"description: {m.get('description', '')}")
            print(f"lang: {m.get('lang', '')}")
            print("--- homepage_text")
            print(r.get("homepage_text") or "(empty)")
        print("--- imprint_text")
        print(r.get("imprint_text") or "(empty)")
        print(f"=== END {h}\n")


if __name__ == "__main__":
    main()
