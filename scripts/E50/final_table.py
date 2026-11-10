"""E50: one table of the frozen final configs (results/E50/final_config.md) on dev 500 and held-out 300.

    python3 -I scripts/E50/final_table.py --out results/E50/heldout300/final.md --json results/E50/heldout300/final.json

Per schema, model and data part (all, e49, e49_noimprint, e51): n, acc@L* with a 95% host-bootstrap CI (5000, seed 1),
P@L*, fail, C per host. Dev and held-out numbers are for the same run config; they are not paired (other hosts).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E49"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import LSTAR, AddrLevels, addr_vectors, host_vectors, load_jsonl  # noqa: E402
from tree import load_schema  # noqa: E402

FINAL = {
    "poi3": {"gemma": "flat__gemma__r-short", "qwen": "flat__qwen__r-low", "agentworld": "flat__agentworld__r-short"},
    "wz": {m: f"retrieve__{m}__r-none__c1500" for m in ("gemma", "qwen", "agentworld")},
    "address": {m: f"address__{m}__r-none__f-schema__mode-main" for m in ("gemma", "qwen", "agentworld")},
}
SETS = ["dev500", "heldout300"]
PARTS = ["all", "e49", "e49_noimprint", "e51"]
B = 5000


def ci(v: dict, hosts: list[str], j: int) -> tuple[float, float]:
    rng = random.Random(1)
    n = len(hosts)
    bs = sorted(sum(v[hosts[rng.randrange(n)]]["hit"][j] for _ in range(n)) / n for _ in range(B))
    return bs[int(.025 * B)], bs[int(.975 * B)]


def row(v: dict, hosts: list[str], L: int) -> dict:
    j = L - 1
    n = len(hosts)
    if not n:
        return {"n": 0}
    acc = sum(v[h]["hit"][j] for h in hosts) / n
    cov = sum(v[h]["cov"][j] for h in hosts)
    lo, hi = ci(v, hosts, j)
    m = lambda k: sum(v[h][k] for h in hosts) / n  # noqa: E731
    return {"n": n, "acc": acc, "lo": lo, "hi": hi, "P": sum(v[h]["hit"][j] for h in hosts) / cov if cov else None,
            "fail": m("fail"), "C": m("C")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    res = []
    lines = ["# E50 final configs: dev 500 and held-out 300", "",
             "Frozen configs: results/E50/final_config.md. acc@L* (POI L*=2, WZ L*=3, address L*=1 = main_ok) with a 95% "
             "host-bootstrap CI; P = precision at L*; C = (tok in - cached in) + 10 x tok out per host. Dev and held-out "
             "are different hosts (not paired). e49 = E49 part (rendered DOM, E49 refs); e49_noimprint = E49 hosts "
             "with an empty imprint text (subset of e49); e51 = E51 part (static HTML, E51 refs).", ""]
    for schema, runs in FINAL.items():
        tree = AddrLevels() if schema == "address" else load_schema(schema)
        L = LSTAR[schema]
        lines += [f"## {schema} (acc@{L})", "", "| model | run | part | dev n | dev acc [95% CI] | dev P | dev C | "
                  "held-out n | held-out acc [95% CI] | held-out P | held-out fail | held-out C |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for m, stem in runs.items():
            for part in PARTS:
                cells = {}
                for s in SETS:
                    refs = {r["host"]: r for r in load_jsonl(f"results/E50/refs/{'addr' if schema == 'address' else schema}_{s}.jsonl")}
                    if part != "all":
                        want = {l.strip() for l in Path(f"results/E50/parts/{s}_{part}.txt").read_text(
                            encoding="utf-8").split("\n") if l.strip()}
                        refs = {h: r for h, r in refs.items() if h in want}
                    f = Path(f"results/E50/preds/{s}/{schema}/{stem}.jsonl")
                    if not f.exists():
                        cells[s] = {"n": 0}
                        continue
                    preds = load_jsonl(f)
                    v = addr_vectors(refs, preds) if schema == "address" else host_vectors(tree, refs, preds)
                    cells[s] = row(v, sorted(v), L)
                res.append({"schema": schema, "model": m, "run": stem, "part": part, **{s: cells[s] for s in SETS}})

                def fmt(c, fail=False):
                    if not c.get("n"):
                        return ["0", "-", "-"] + (["-"] if fail else []) + ["-"]
                    out = [str(c["n"]), f"{c['acc']:.3f} [{c['lo']:.3f}, {c['hi']:.3f}]",
                           "-" if c["P"] is None else f"{c['P']:.3f}"]
                    if fail:
                        out.append(f"{c['fail']:.3f}")
                    return out + [f"{c['C']:.0f}"]
                lines.append("| " + " | ".join([m, stem, part] + fmt(cells["dev500"]) + fmt(cells["heldout300"], True))
                             + " |")
        lines.append("")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
