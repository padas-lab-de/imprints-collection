"""E49: combine prediction files (e.g. the same strategy from several models) by vote.

    python3 scripts/E49/ensemble.py --vote level_majority --out results/E49/preds/poi/ens__flat4.jsonl \
        results/E49/preds/poi/flat__qwen__*.jsonl results/E49/preds/poi/flat__gemma__*.jsonl ...

Output lines look like run.py output (main, ranked, path, usage summed over members, samples = member mains),
so score.py scores them like any run. Hosts missing in a member count as an abstaining voter.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import load_schema  # noqa: E402
from vote import VOTES  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--vote", default="level_majority", choices=sorted(VOTES))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    members = [{(r := json.loads(l))["host"]: r for l in open(f, encoding="utf-8") if l.strip()} for f in a.preds]
    schema = next(iter(members[0].values()))["schema"]
    tree = load_schema(schema)
    hosts = sorted(set().union(*members))
    tag = Path(a.out).stem
    with open(a.out, "w", encoding="utf-8") as f:
        for h in hosts:
            rs = [m.get(h) for m in members]
            if all(r is None or r.get("error") == "no_input" for r in rs):
                rec = {"main": None, "error": "no_input"}
            else:
                mains = [r.get("main") if r else None for r in rs]
                main = VOTES[a.vote](tree, mains)
                rec = {"main": main, "error": None, "samples": mains,
                       "confidence": sum(m == main for m in mains) / len(mains)}
            usage = {}
            for r in rs:
                for k, v in ((r or {}).get("usage") or {}).items():
                    usage[k] = usage.get(k, 0) + v
            rec.update({"host": h, "schema": tree.name, "tag": tag, "model": "ensemble",
                        "members": [Path(p).stem for p in a.preds], "ranked": [rec["main"]] if rec["main"] else [],
                        "path": tree.path(rec["main"]) if rec["main"] else [], "usage": usage,
                        "latency_s": sum((r or {}).get("latency_s", 0) for r in rs)})
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{len(hosts)} hosts -> {a.out}")


if __name__ == "__main__":
    main()
