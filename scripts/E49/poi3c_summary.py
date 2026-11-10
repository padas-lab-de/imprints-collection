"""E49 poi3c: gemma b vs qwen b vs level-majority ens2 (POI v3, --node-lang both), dev and held-out.

    python3 scripts/E49/poi3c_summary.py --out results/E49/poi3c/summary_tables.md
Builds ens2 with scripts/E49/ensemble.py (level_majority over qwen b + gemma b) into results/E49/poi3c/preds/<set>/poi3/.
Hosts scored = common to all three configs with a non-null reference. Subsets: all, offline.
Paired stats reuse poi3b_summary (host bootstrap 5000, seed 1, sign test on acc@2); also reports per-level
precision/coverage of ens2, depth distribution of ens2 predictions, s/host and tokens.
"""
import argparse, subprocess, sys, random
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poi3b_summary import Q, G, hit, sign_p, stats  # noqa: E402
from score import load_jsonl, score  # noqa: E402
from tree import load_schema  # noqa: E402

B = "results/E49/poi3b/preds/"
C = "results/E49/poi3c/preds/"
SETS = {
    "dev": {"refs": "results/E49/refs/poi_v3.jsonl", "q": B + "dev/poi3/" + Q + "__nl-both",
            "g": C + "dev/poi3/" + G + "__nl-both", "ens": C + "dev/poi3/ens2__qwen_gemma__nl-both"},
    "held-out": {"refs": "results/E49/heldout/refs/poi_v3.jsonl", "q": B + "heldout/poi3/" + Q + "__nl-both",
                 "g": B + "heldout/poi3/" + G + "__nl-both", "ens": C + "heldout/poi3/ens2__qwen_gemma__nl-both"}}
PAIRS = [("gemma b", "qwen b"), ("ens2", "qwen b"), ("ens2", "gemma b")]
tree = load_schema("poi3")


def boot(v, x, y, n):
    d0 = [u - w for u, w in zip(stats(v[x]), stats(v[y]))]
    rng = random.Random(1)
    bs = []
    for _ in range(5000):
        idx = [rng.randrange(n) for _ in range(n)]
        sx, sy = stats([v[x][i] for i in idx]), stats([v[y][i] for i in idx])
        bs.append([u - w for u, w in zip(sx, sy)])
    ci = []
    for j in range(3):
        col = sorted(b[j] for b in bs if b[j] == b[j])
        ci.append((col[int(.025 * len(col))], col[int(.975 * len(col))]) if col else (float("nan"),) * 2)
    return d0, ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/E49/poi3c/summary_tables.md")
    a = ap.parse_args()
    out = []
    for sname, S in SETS.items():
        Path(S["ens"]).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "scripts/E49/ensemble.py", "--vote", "level_majority", "--out", S["ens"] + ".jsonl",
                        S["q"] + ".jsonl", S["g"] + ".jsonl"], check=True, stdout=subprocess.DEVNULL)
        refs = {r["host"]: r for r in load_jsonl(S["refs"])}
        preds = {k: {p["host"]: p for p in load_jsonl(S[f] + ".jsonl")} for k, f in
                 (("qwen b", "q"), ("gemma b", "g"), ("ens2", "ens"))}
        keep = {h for h, r in refs.items() if r["main"] is not None}
        for ps in preds.values():
            keep &= {h for h, p in ps.items() if p.get("error") != "no_input"}
        for sub, hosts in (("all hosts", keep), ("offline", {h for h in keep if not refs[h]["online_only"]})):
            hs = sorted(hosts)
            out += [f"### {sname}, {sub} (n={len(hs)})", "",
                    "| config | abst | err | P@1 | P@2 | P@3 | acc@1 | acc@2 | acc@3 | cov@1 | cov@2 | cov@3 | s/host | tok in | tok out |",
                    "|" + "---|" * 15]
            for k, ps in preds.items():
                m = score(tree, refs, [p for h, p in ps.items() if h in hosts])
                L = {x["level"]: x for x in m["levels"]}
                c = m["cost_per_host"]
                f = lambda v: "n/a" if v is None else f"{v:.3f}"  # noqa: E731
                out.append(f"| {k} | {m['abstain']} | {m['errors']} | " + " | ".join(f(L[i]["precision"]) for i in (1, 2, 3)) + " | "
                           + " | ".join(f(L[i]["acc_trunc"]) for i in (1, 2, 3)) + " | " + " | ".join(f(L[i]["coverage"]) for i in (1, 2, 3))
                           + f" | {c['latency_s']} | {c['prompt_tokens']} | {c['completion_tokens']} |")
            out.append("")
            out += [f"Paired ({sname}, {sub}): x - y, 95% bootstrap CI over hosts", "",
                    "| x vs y | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |", "|---|---|---|---|---|"]
            v = {k: [] for k in preds}
            for k in preds:
                for h in hs:
                    h1, _ = hit(refs[h], preds[k][h], 1)
                    h2, c2 = hit(refs[h], preds[k][h], 2)
                    v[k].append((h1, h2, int(c2), h2 if c2 else 0))
            for x, y in PAIRS:
                d0, ci = boot(v, x, y, len(hs))
                w = sum(p[1] > q[1] for p, q in zip(v[x], v[y]))
                l = sum(p[1] < q[1] for p, q in zip(v[x], v[y]))
                f = lambda j: f"{d0[j]:+.3f} [{ci[j][0]:+.3f},{ci[j][1]:+.3f}]"  # noqa: E731
                out.append(f"| {x} vs {y} | {f(0)} | {f(1)} | {f(2)} | {w}/{l}, p={sign_p(w, l):.2f} |")
            out.append("")
            if sub == "all hosts":
                dep = Counter(len(tree.canonical_path(preds["ens2"][h]["main"])) if preds["ens2"][h].get("main") in tree else 0 for h in hs)
                out.append(f"ens2 depth (canonical path length) over {len(hs)} hosts: " + ", ".join(f"L{k}={dep[k]}" if k else f"none={dep[k]}" for k in sorted(dep)))
                out.append("")
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
