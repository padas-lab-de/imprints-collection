#!/usr/bin/env python3
"""E53 step 6: assign the 1,869 gold items to the three labellers (docs/gold_set_design.md 5.2).

    PYTHONPATH=src python3 -I scripts/E53/assign.py            # run from the repo root

Reads datasets/E53/phase2/gold_sample.jsonl and datasets/E53/gold/<host>/meta.json (capture outcome only).
Writes datasets/E53/gold/assignment.jsonl (item, host, labeller, role, order; no stratum or weight) and
results/E53/assignment.md. Needs no network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ic.gold.assignment import LABELLERS, PAIRS, build_assignment_folds  # noqa: E402


def safe(host: str) -> str:  # as scripts/gold/e8_pilot.py safe(): the capture directory name
    return re.sub(r"[^a-zA-Z0-9.\-]", "_", host)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_items(sample: Path, gold: Path) -> list[dict]:
    items = []
    with open(sample, encoding="utf-8") as f:
        for k, line in enumerate(ln for ln in f if ln.strip()):
            r = json.loads(line)
            d = safe(r["host"])
            meta = json.loads((gold / d / "meta.json").read_text(encoding="utf-8"))
            items.append(
                {
                    "item": k,
                    "host": d,
                    "fold": r["fold"],
                    "core": bool(r["core"]),
                    "outcome": meta.get("outcome"),
                    "strato": bool(meta.get("strato")),
                    "eligible": meta.get("outcome") != "failed",
                }
            )
    return items


def report(items, rows, args, hashes) -> str:
    roles = defaultdict(lambda: defaultdict(list))
    for r in rows:
        roles[r["item"]][r["role"]].append(r["labeller"])
    L = []
    L.append("# E53 step 6: labeller assignment\n")
    L.append(
        f"Items: {len(items)}. Seed: {args.seed}. n_cal {args.n_cal}, n_second {args.n_second}. "
        "Labellers L1, L2, L3 (names to be set)."
    )
    L.append("Script: `scripts/E53/assign.py`, function `ic.gold.assignment.build_assignment_folds`. No network.\n")
    L.append("## Counts per labeller and role\n")
    L.append("| Labeller | primary | second | calibration | total |\n|---|---|---|---|---|")
    c = defaultdict(Counter)
    for r in rows:
        c[r["labeller"]][r["role"]] += 1
    for lab in LABELLERS:
        L.append(f"| {lab} | {c[lab]['primary']} | {c[lab]['second']} | {c[lab]['calibration']} | {sum(c[lab].values())} |")
    tot = Counter(r["role"] for r in rows)
    L.append(f"| all | {tot['primary']} | {tot['second']} | {tot['calibration']} | {len(rows)} |\n")
    n_single = sum(1 for v in roles.values() if "primary" in v and "second" not in v)
    n_dbl = sum(1 for v in roles.values() if "second" in v)
    n_cal = sum(1 for v in roles.values() if "calibration" in v)
    L.append(
        "Calibration items have three `calibration` rows and no `primary` row (their gold label is the consensus). "
        f"Items with one label: {n_single}; double-labelled (primary + second): {n_dbl}; calibration: {n_cal}; "
        f"together {n_single + n_dbl + n_cal}.\n"
    )
    L.append("## Second labels per pair\n")
    L.append("| Pair | items | first-named is primary / second is primary |\n|---|---|---|")
    pc = Counter()
    for v in roles.values():
        if "second" in v:
            pc[(v["primary"][0], v["second"][0])] += 1
    for a, b in PAIRS:
        L.append(f"| {a}-{b} | {pc[(a, b)] + pc[(b, a)]} | {pc[(a, b)]} / {pc[(b, a)]} |")
    L.append("")
    L.append("## Per fold\n")
    L.append(
        "| Fold | items | calibration | calibration core | second | L1-L2 | L1-L3 | L2-L3 | failed captures |\n"
        "|---|---|---|---|---|---|---|---|---|"
    )
    for f in sorted({it["fold"] for it in items}):
        its = [it for it in items if it["fold"] == f]
        cal = [it for it in its if "calibration" in roles[it["item"]]]
        sec = [it for it in its if "second" in roles[it["item"]]]
        pf = Counter(tuple(sorted((roles[it["item"]]["primary"][0], roles[it["item"]]["second"][0]))) for it in sec)
        L.append(
            f"| {f} | {len(its)} | {len(cal)} | {sum(it['core'] for it in cal)} | {len(sec)} | "
            f"{pf[('L1', 'L2')]} | {pf[('L1', 'L3')]} | {pf[('L2', 'L3')]} | {sum(not it['eligible'] for it in its)} |"
        )
    L.append("")
    cc = Counter(it["core"] for it in items if "calibration" in roles[it["item"]])
    sc = Counter(it["core"] for it in items if "second" in roles[it["item"]])
    n_core = sum(it["core"] for it in items)
    L.append(
        f"Core / oversample: sample {n_core} / {len(items) - n_core}; calibration {cc[True]} / {cc[False]}; "
        f"second {sc[True]} / {sc[False]}.\n"
    )
    bad = [it for it in items if not it["eligible"]]
    L.append(
        f"Failed captures: {len(bad)}; in calibration: {sum('calibration' in roles[it['item']] for it in bad)}; "
        f"in second labels: {sum('second' in roles[it['item']] for it in bad)} (both excluded by design; they keep one primary label)."
    )
    st = [it for it in items if it["strato"] and it["outcome"] == "landing_only"]
    L.append(
        f"Strato landing-only items: {len(st)}, all kept in the assignment as normal items (card D62 decides their "
        "capture later); the assignment format has no field to mark them. "
        f"In calibration: {sum('calibration' in roles[it['item']] for it in st)}; "
        f"in second labels: {sum('second' in roles[it['item']] for it in st)}.\n"
    )
    L.append("## Design choices\n")
    L.append("- Load split 2:1:1 over all labels incl. calibration (design 5.2): L1 1,172, L2 586, L3 586 of 2,344.")
    L.append("- Calibration: 10 per fold, core/oversample in proportion inside the fold; seeded random.")
    L.append(
        "- Second labels: 375 = 125 per pair; drawn proportional over fold x core; pairs and directions dealt in "
        "fold order, so every fold is close to even over the pairs."
    )
    L.append(
        "- Order: per labeller, calibration block first (random), then the rest (random). Not by stratum, weight "
        "or fold. The file holds no stratum, weight or fold.\n"
    )
    L.append("## Files and sha256\n")
    L.append("| File | sha256 |\n|---|---|")
    for k, v in hashes.items():
        L.append(f"| `{k}` | `{v}` |")
    L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", default="datasets/E53/phase2/gold_sample.jsonl")
    ap.add_argument("--gold", default="datasets/E53/gold")
    ap.add_argument("--seed", type=int, default=20261113)
    ap.add_argument("--n-cal", type=int, default=50)
    ap.add_argument("--n-second", type=int, default=375)
    ap.add_argument("--report", default="results/E53/assignment.md")
    a = ap.parse_args()
    gold = Path(a.gold)
    items = load_items(Path(a.sample), gold)
    rows, _info = build_assignment_folds(items, a.seed, a.n_cal, a.n_second)
    out = gold / "assignment.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in sorted(rows, key=lambda r: (r["labeller"], r["order"])):
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    hashes = {
        "datasets/E53/gold/assignment.jsonl": sha256(out),
        "datasets/E53/phase2/gold_sample.jsonl": sha256(Path(a.sample)),
        "datasets/E53/gold/prefill.jsonl (read only)": sha256(gold / "prefill.jsonl"),
    }
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(report(items, rows, a, hashes) + "\n", encoding="utf-8")
    print(f"{len(items)} items, {len(rows)} rows -> {out}; report {a.report}")


if __name__ == "__main__":
    main()
