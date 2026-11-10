"""A=B agreement of the two E51 label passes, and the worksheet of disagreements for adjudication.

    python3 -I scripts/E51/refs_agree.py            writes results/E51/agreement.json + datasets/E51/adjudication/todo_<task>_<set>.jsonl
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refs_common import (SETS, addr_agree, addr_all, addr_main, addr_ops, hosts, load_pass,  # noqa: E402
                         parents, path)


def topic_stats(A, B, hs, par):
    n = len(hs)
    exact = sum(A[h]["main"] == B[h]["main"] for h in hs)
    lenient = sum(A[h]["main"] == B[h]["main"] or A[h]["main"] in B[h]["extra"] or B[h]["main"] in A[h]["extra"]
                  for h in hs)
    lv = {}
    for L in range(1, 6):
        lv[L] = sum(len(pa) >= L and len(pb) >= L and pa[:L] == pb[:L]
                    for h in hs for pa, pb in [(path(par, A[h]["main"]), path(par, B[h]["main"]))])
    return {"n": n, "main_exact": exact, "main_lenient": lenient, "same_prefix_L1_L5": list(lv.values())}


def addr_stats(A, B, hs):
    return {
        "n": len(hs),
        "strict (main + operator set)": sum(addr_agree(A[h], B[h]) for h in hs),
        "main": sum(addr_main(A[h]) == addr_main(B[h]) for h in hs),
        "main_postcode": sum(addr_main(A[h])[0] == addr_main(B[h])[0]
                             and (addr_main(A[h])[1][2:] if addr_main(A[h])[0] == "main" else addr_main(A[h])[1])
                             == (addr_main(B[h])[1][2:] if addr_main(B[h])[0] == "main" else addr_main(B[h])[1])
                             for h in hs),
        "operator_set": sum(addr_ops(A[h]) == addr_ops(B[h]) for h in hs),
        "all_rows": sum(addr_all(A[h]) == addr_all(B[h]) for h in hs),
        "has_main_A_B": [sum(A[h]["main_address_index"] is not None for h in hs),
                         sum(B[h]["main_address_index"] is not None for h in hs)],
    }


def main():
    out = {}
    os.makedirs("datasets/E51/adjudication", exist_ok=True)
    plan = [("poi", "dev2"), ("poi", "heldout2"), ("wz", "dev2"), ("wz", "heldout2"),
            ("addr", "dev2"), ("addr", "heldout2"), ("addr", "e49")]
    for task, s in plan:
        if not os.path.exists(SETS[s][0]):
            continue
        hs = hosts(s)
        A, B = load_pass("A", task, s), load_pass("B", task, s)
        miss = [h for h in hs if h not in A or h not in B]
        if miss:
            out[f"{task}_{s}"] = {"missing": len(miss)}
            continue
        if task == "addr":
            st = addr_stats(A, B, hs)
            dis = [h for h in hs if not addr_agree(A[h], B[h])]
        else:
            par = parents(task)
            st = topic_stats(A, B, hs, par)
            dis = [h for h in hs if A[h]["main"] != B[h]["main"]]
        out[f"{task}_{s}"] = st
        with open(f"datasets/E51/adjudication/todo_{task}_{s}.jsonl", "w", encoding="utf-8") as f:
            for h in dis:
                f.write(json.dumps({"host": h, "A": A[h], "B": B[h]}, ensure_ascii=False) + "\n")
    js = json.dumps(out, ensure_ascii=False, indent=1)
    open("results/E51/agreement.json", "w").write(js + "\n")
    print(js)


if __name__ == "__main__":
    main()
