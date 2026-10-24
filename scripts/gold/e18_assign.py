#!/usr/bin/env python3
"""E18: assign the gold-sample items to the three labellers.

    PYTHONPATH=src python scripts/gold/e18_assign.py            # run from the repo root
    PYTHONPATH=src python scripts/gold/e18_assign.py --sample datasets/E12/gold_sample.jsonl \
        --out datasets/gold/assignment.jsonl --seed 20261024

Output rows: item, host, labeller, role (primary | second | calibration), order.
No stratum or detector information is written (labellers must not see it).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ic.gold.assignment import build_assignment, summarise  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", default="datasets/E12/gold_sample.jsonl")
    ap.add_argument("--out", default="datasets/gold/assignment.jsonl")
    ap.add_argument("--seed", type=int, default=20261024)
    ap.add_argument("--n-cal", type=int, default=50)
    ap.add_argument("--n-second", type=int, default=200)
    a = ap.parse_args()

    with open(a.sample, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    rows, info = build_assignment(items, a.seed, a.n_cal, a.n_second)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in sorted(rows, key=lambda r: (r["labeller"], r["order"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(items)} items, seed {a.seed}, {len(rows)} assignment rows -> {out}")
    print("\n".join(summarise(rows, items)))
    print(f"set-cover part of the double-labelled draw: {info['n_cover']} items; rest filled by priority stratum")


if __name__ == "__main__":
    main()
