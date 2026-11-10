"""Build the E51 reference files from the two passes and the adjudication decisions.

Agreed hosts (refs_common.topic_agree / addr_agree) take pass A. Every host with a line in
results/E51/adjudication/decisions_<task>_<set>.jsonl takes the decision:
  {"host": ..., "pick": "A"|"B"|"new", "label": {...fields...} (pick new only; may also patch A/B),
   "reason": "..."}
A decision on an agreed host is a rule change (note "adjusted: <reason>", agree_ab stays true).

    python3 -I scripts/E51/refs_build.py
writes results/E51/refs/{poi_v3,wz,addr}_<set>.jsonl
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refs_common import SETS, addr_agree, hosts, load_pass, parents, path, topic_agree  # noqa: E402

OUT_NAME = {"poi": "poi_v3", "wz": "wz", "addr": "addr"}
PLAN = [("poi", "dev2"), ("poi", "heldout2"), ("wz", "dev2"), ("wz", "heldout2"),
        ("addr", "dev2"), ("addr", "heldout2"), ("addr", "e49")]


def decisions(task, s):
    p = f"results/E51/adjudication/decisions_{task}_{s}.jsonl"
    if not os.path.exists(p):
        return {}
    return {r["host"]: r for r in map(json.loads, (l for l in open(p, encoding="utf-8") if l.strip()))}


def main():
    os.makedirs("results/E51/refs", exist_ok=True)
    summary = {}
    only = sys.argv[1] if len(sys.argv) > 1 else None  # optional task filter: poi, wz or addr
    for task, s in PLAN:
        if only and task != only:
            continue
        hs = hosts(s)
        A, B = load_pass("A", task, s), load_pass("B", task, s)
        D = decisions(task, s)
        par = parents(task) if task != "addr" else None
        rows, cnt = [], {"agreed": 0, "A": 0, "B": 0, "new": 0, "adjusted_agreed": 0}
        for h in hs:
            a, b = A[h], B[h]
            agree = topic_agree(a, b) if par else addr_agree(a, b)
            d = D.get(h)
            if d is None:
                if not agree:
                    raise SystemExit(f"{task} {s} {h}: disagreement without decision")
                base, note = dict(a), a.get("note") or ""
                cnt["agreed"] += 1
            else:
                base = dict(a if d["pick"] in ("A", "new") else b)
                base.update(d.get("label") or {})
                if agree:
                    note = f"adjusted: {d['reason']}"
                    cnt["adjusted_agreed"] += 1
                else:
                    note = f"adjudicated: {d['pick']}; {d['reason']}"
                    cnt[d["pick"]] += 1
            if par:
                r = {"host": h, "schema": "poi3" if task == "poi" else "wz", "main": base["main"],
                     "extra": list(base.get("extra") or []), "path": path(par, base["main"]),
                     "confidence": base["confidence"], "note": note, "agree_ab": agree}
                if task == "poi":
                    r["online_only"] = bool(base.get("online_only"))
            else:
                r = {"host": h, "addresses": base["addresses"], "main_address_index": base["main_address_index"],
                     "no_address_reason": base["no_address_reason"], "flags": list(base.get("flags") or []),
                     "confidence": base["confidence"], "note": note, "agree_ab": agree}
            rows.append(r)
        unused = set(D) - set(hs)
        if unused:
            raise SystemExit(f"{task} {s}: decisions for unknown hosts {sorted(unused)}")
        with open(f"results/E51/refs/{OUT_NAME[task]}_{s}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        summary[f"{task}_{s}"] = cnt
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
