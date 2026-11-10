"""E49 poi3 rerun: build results/E49/poi3/summary.md (tables + L2 confusion pairs).

    python3 scripts/E49/poi3_summary.py --v2-preds <dir with stage-2 poi preds> --out results/E49/poi3/summary.md
Compares per config: v2 native (v2 refs), v2 predictions migrated to v3 ids (v3 refs), v3 native (v3 refs),
on the hosts common to all runs, for all hosts and for the offline subset (online_only false).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import load_jsonl, score  # noqa: E402
from tree import load_schema  # noqa: E402

Q = "flat__qwen__both__dmax__nt-path__think"
GB = "flat__gemma__both__dmax__nt-path__reason"
GH = "flat__gemma__home__dmax__nt-path__reason"
GBT = "flat__gemma__both__dmax__nt-path__think"
# (label, v2 native file, v3 native file)
CONFIGS = [("qwen38-27b flat think both", Q, Q), ("gemma4-31b-it flat reason both", None, GB),
           ("gemma4-31b-it flat reason home (matched v2)", GH, GH)]


def row(name, m):
    L = {x["level"]: x for x in m["levels"]}
    c = m["cost_per_host"]
    f = lambda v: "-" if v is None else f"{v:.3f}"  # noqa: E731
    return (f"| {name} | {m['n_scored']} | {m['abstain']} | {m['errors']} | {f(L[1]['precision'])} | {f(L[2]['precision'])} | "
            f"{f(L[1]['acc_trunc'])} | {f(L[2]['acc_trunc'])} | {f(L[2]['coverage'])} | {c['latency_s']} | "
            f"{c['prompt_tokens']} | {c['completion_tokens']} |")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-preds", required=True)
    ap.add_argument("--v3-preds", default="results/E49/poi3/preds/poi3")
    ap.add_argument("--migrated", default="results/E49/poi3/migrated/poi3")
    ap.add_argument("--refs2", default="results/E49/refs/poi.jsonl")
    ap.add_argument("--refs3", default="results/E49/refs/poi_v3.jsonl")
    ap.add_argument("--out", default="results/E49/poi3/summary.md")
    a = ap.parse_args()
    t2, t3 = load_schema("poi"), load_schema("poi3")
    r2 = {r["host"]: r for r in load_jsonl(a.refs2)}
    r3 = {r["host"]: r for r in load_jsonl(a.refs3)}
    offline = {h for h, r in r3.items() if not r.get("online_only")}
    runs = {}  # key -> preds
    for lab, f2, f3 in CONFIGS:
        if len(load_jsonl(Path(a.v3_preds) / f"{f3}.jsonl")) < 200:
            print(f"skip {lab}: v3 run incomplete")
            continue
        if f2:
            runs[(lab, "v2 native")] = load_jsonl(Path(a.v2_preds) / f"{f2}.jsonl")
            runs[(lab, "v2 migrated to v3")] = load_jsonl(Path(a.migrated) / f"{f2}.jsonl")
        runs[(lab, "v3 native")] = load_jsonl(Path(a.v3_preds) / f"{f3}.jsonl")
    keep = None
    for ps in runs.values():
        hs = {p["host"] for p in ps if p.get("error") != "no_input"}
        keep = hs if keep is None else keep & hs
    keep &= set(r2) & set(r3)
    out = ["# E49 poi3 rerun (D51 B on schema poi_v3)", "",
           "Date 2026-11-10. Inputs: dev set 200 hosts, refs `results/E49/refs/poi_v3.jsonl` (v3 and migrated) and `refs/poi.jsonl` (v2 native). "
           "Innkube only, no paid cost. Hosts scored are those common to all runs. "
           "acc = strict accuracy with both paths truncated to the level (`acc_trunc`), P = precision among covered, cov@2 = coverage at level 2. "
           "tok = prompt / completion tokens per host. Abst = prediction `main` null; err = failed replies (also counted as abstentions).", ""]
    for title, sub in (("All hosts", keep), ("Offline subset (online_only false)", keep & offline)):
        out += [f"## {title} (n={len(sub)})", "",
                "| run | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | s/host | tok in | tok out |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for (lab, kind), ps in runs.items():
            ps = [p for p in ps if p["host"] in sub]
            tree, refs = (t2, r2) if kind == "v2 native" else (t3, r3)
            out.append(row(f"{lab} / {kind}", score(tree, refs, ps)))
        out.append("")
    # L2 confusion pairs, qwen v3 native
    ps = [p for p in runs[(CONFIGS[0][0], "v3 native")] if p["host"] in keep]
    P = lambda i: t3.canonical_path(i) if i in t3 else []  # noqa: E731
    pairs, abst, shallow, tot = Counter(), 0, 0, 0
    for p in ps:
        r = r3[p["host"]]
        if r.get("main") is None:
            continue
        rp, pp = P(r["main"]), P(p.get("main"))
        if len(rp) < 2:
            continue
        tot += 1
        if not pp:
            abst += 1
        elif len(pp) < 2:
            shallow += 1
        elif pp[:2] != rp[:2]:
            pairs[(rp[1], pp[1])] += 1
    out += ["## Top 10 confusion pairs at level 2 (qwen v3 native, ref -> pred)", "",
            f"Hosts with a reference reaching level 2: {tot}. Abstained: {abst}. Predicted level 1 only: {shallow}. "
            f"Wrong at level 2 (both reach it): {sum(pairs.values())}.", "",
            "| n | reference (level 2) | prediction (level 2) | same root |", "|---|---|---|---|"]
    for (rf, pr), n in pairs.most_common(10):
        out.append(f"| {n} | {t3[rf].title} ({t3[t3[rf].path[0]].title}) | {t3[pr].title} ({t3[t3[pr].path[0]].title}) | "
                   f"{'yes' if t3[rf].path[0] == t3[pr].path[0] else 'no'} |")
    out.append("")
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
