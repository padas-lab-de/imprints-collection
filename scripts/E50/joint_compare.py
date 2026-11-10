"""E50 stage D: joint calls vs separate calls, per model, per part of the answer and in total cost.

    python3 scripts/E50/joint_compare.py --dir results/E50/preds/dev500 --refs-dir results/E50/refs --set dev500 \
        --sep gemma=poi3:r-short,wz:r-none,address:r-none --joint joint-poi-wz,joint-poi-wz-address \
        [--hosts results/E50/parts/dev500_e51.txt] --out results/E50/dev500/joint.md

For each model and joint run J (reasoning = the model's POI base reasoning): per part (poi3 acc@2, wz acc@3,
address main_ok) d = joint - separate base run on the common hosts with a host bootstrap CI (compare.paired), and
the cost per host: C(joint call) vs the sum of C(separate base runs of the parts that J answers). The joint part
files carry the usage of the whole call; it is counted once.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare as CP  # noqa: E402

from tree import load_schema  # noqa: E402

PART = {"poi": "poi3", "wz": "wz", "address": "address"}
REF = {"poi3": "poi3", "wz": "wz", "address": "addr"}


def vectors(schema, tree, refs, path):
    preds = CP.load_jsonl(path)
    return CP.addr_vectors(refs, preds) if schema == "address" else CP.host_vectors(tree, refs, preds)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--refs-dir", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--sep", action="append", default=[], help="model=poi3:r-x,wz:r-y,address:r-z")
    ap.add_argument("--joint", default="joint-poi-wz,joint-poi-wz-address")
    ap.add_argument("--hosts", default=None)
    ap.add_argument("--title", default="dev 500")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    want = None
    if a.hosts:
        want = {l.strip() for l in Path(a.hosts).read_text(encoding="utf-8").splitlines() if l.strip()}
    trees = {"poi3": load_schema("poi3"), "wz": load_schema("wz"), "address": CP.AddrLevels()}
    refs = {}
    for s in trees:
        rs = {r["host"]: r for r in CP.load_jsonl(Path(a.refs_dir) / f"{REF[s]}_{a.set}.jsonl")}
        refs[s] = {h: r for h, r in rs.items() if want is None or h in want}
    lines = [f"# E50 stage D: joint vs separate calls, {a.title}", "",
             "| model | joint run | part | n | separate | joint | d | 95% CI | W/L | C separate (sum) | C joint | C ratio |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    res = []
    for spec in a.sep:
        model, rest = spec.split("=")
        sep = dict(x.split(":") for x in rest.split(","))
        poi_r = sep["poi3"]
        for jn in [j for j in a.joint.split(",") if j]:
            parts = [PART[p] for p in jn.split("-")[1:]]
            jv, sv = {}, {}
            for s in parts:
                jp = Path(a.dir) / s / f"{jn}__{model}__{poi_r}.jsonl"
                sp = Path(a.dir) / s / f"{CP.DEFAULT_FIRST[s]}__{model}__{sep[s]}.jsonl"
                if not jp.exists() or not sp.exists():
                    break
                jv[s], sv[s] = vectors(s, trees[s], refs[s], jp), vectors(s, trees[s], refs[s], sp)
            else:
                hs_all = sorted(set.intersection(*[set(jv[s]) & set(sv[s]) for s in parts]))
                c_sep = sum(sv[s][h]["C"] for s in parts for h in hs_all) / max(1, len(hs_all))
                c_joint = sum(jv[parts[0]][h]["C"] for h in hs_all) / max(1, len(hs_all))
                for s in parts:
                    L = CP.LSTAR[s]
                    hs = sorted(set(jv[s]) & set(sv[s]))
                    pr = CP.paired([(jv[s], sv[s])], hs, L)
                    acc_s = sum(sv[s][h]["hit"][L - 1] for h in hs) / len(hs)
                    acc_j = sum(jv[s][h]["hit"][L - 1] for h in hs) / len(hs)
                    row = {"model": model, "joint": jn, "part": s, "n": len(hs), "sep": acc_s, "joint_acc": acc_j,
                           "d": pr["d"], "lo": pr["lo"], "hi": pr["hi"], "wins": pr["wins"], "losses": pr["losses"],
                           "C_sep": c_sep, "C_joint": c_joint, "fail_joint": CP.summary(jv[s], hs, L)["fail"]}
                    res.append(row)
                    lines.append(f"| {model} | {jn} ({poi_r}) | {s} ({sep[s]}) | {len(hs)} | {acc_s:.3f} | {acc_j:.3f} | "
                                 f"{pr['d']:+.3f} | [{pr['lo']:+.3f}, {pr['hi']:+.3f}] | {pr['wins']}/{pr['losses']} | "
                                 f"{c_sep:.0f} | {c_joint:.0f} | {c_joint / max(1, c_sep):.2f} |")
    lines += ["", "Metric per part: poi3 acc@2, wz acc@3, address main_ok. separate = the model's base run of that part "
              "(reasoning in brackets); joint = the part of the joint call at the model's POI base reasoning. C per host "
              "= (tok in - cached in) + 10 x tok out over the hosts common to all parts; C separate = sum over the parts."]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(a.out).with_suffix(".json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
