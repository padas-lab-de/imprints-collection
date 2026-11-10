"""E49 held-out check: paired comparison of WZ configs (a no rules, b rules+keepout, c b+rules-candidates).

Per host, hit@L = predicted canonical path equals the reference path on the first L levels (abstention = miss).
Reports hit rates, paired wins/losses, exact two-sided sign test and bootstrap 95% CI of the difference, for the
held-out set and the dev set. Run from the repository root with the project venv:

    python3 scripts/E49/heldout_compare.py [--ens-a-dev PATH]   (dev ens2 without rules = scripts/E49/ensemble.py of the two stage-2 k30 preds)
"""
import argparse, json, random
from math import comb
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import load_schema  # noqa: E402

tree = load_schema("wz")
P = lambda i: tree.canonical_path(i) if i in tree else []  # noqa: E731


def jl(p):
    return {json.loads(l)["host"]: json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()}


def hits(refs, preds, L):
    return {h: int(bool(P(preds[h].get("main"))) and P(preds[h].get("main"))[:L] == P(r["main"])[:L])
            for h, r in refs.items() if r["main"] is not None and h in preds}


def sign_p(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def boot(d, B=5000, seed=1):
    rng = random.Random(seed)
    n = len(d)
    m = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return m[int(.025 * B)], m[int(.975 * B)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens-a-dev", default="/home/dinzinger/.claude/jobs/4110e328/tmp/heldout/devens/ens2__a_norules.jsonl")
    ap.add_argument("--md", default="results/E49/heldout/scores/paired.md")
    a = ap.parse_args()
    G, Q = "retrieve__gemma__home__dmax__nt-path__k30__emb-kw", "retrieve__qwen__home__dmax__nt-path__k30__emb-kw"
    R, K = "__rules-wz_rules__keepout", "__rulescand"
    H = "results/E49/heldout/preds/wz/"
    sets = {
        "held-out": ("results/E49/heldout/refs/wz.jsonl", {
            "gemma": [H + G, H + G + R, H + G + R + K], "qwen": [H + Q, H + Q + R, H + Q + R + K],
            "ens2": [H + "ens2__a_norules", H + "ens2__b_rules", H + "ens2__c_rulescand"]}),
        "dev": ("results/E49/refs/wz.jsonl", {
            "gemma": ["results/E49/stage2/preds/wz/" + G, "results/E49/stage3/preds/wz/" + G + R, "results/E49/stage3b/preds/wz/" + G + R + K],
            "qwen": ["results/E49/stage2/preds/wz/" + Q, "results/E49/stage3/preds/wz/" + Q + R, "results/E49/stage3b/preds/wz/" + Q + R + K],
            "ens2": [a.ens_a_dev[:-6], "results/E49/stage3/preds/wz/ens2__gemmaret30RULES_qwenret30RULES", "results/E49/stage3b/preds/wz/ens2__V2rc30"]}),
    }
    out = ["| set | model | L | n | hit a | hit b | hit c | b-a (W/L, p, 95% CI) | c-a (W/L, p, 95% CI) | c-b (W/L, p, 95% CI) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for sname, (rf, models) in sets.items():
        refs = jl(rf)
        for m, files in models.items():
            preds = [jl(f + ".jsonl") for f in files]
            common = set(refs) & set(preds[0]) & set(preds[1]) & set(preds[2])
            sub = {h: refs[h] for h in common}
            for L in (1, 2, 3, 5):
                hs = [hits(sub, p, L) for p in preds]
                ks = sorted(hs[0])
                def cell(x, y):
                    d = [hs[y][k] - hs[x][k] for k in ks]
                    w, l = sum(v > 0 for v in d), sum(v < 0 for v in d)
                    lo, hi = boot(d)
                    return f"{w - l:+d} ({w}/{l}, p={sign_p(w, l):.2f}, [{lo:+.3f},{hi:+.3f}])"

                out.append(f"| {sname} | {m} | {L} | {len(ks)} | {sum(hs[0].values())/len(ks):.3f} | {sum(hs[1].values())/len(ks):.3f} | "
                           f"{sum(hs[2].values())/len(ks):.3f} | {cell(0, 1)} | {cell(0, 2)} | {cell(1, 2)} |")
    Path(a.md).write_text("\n".join(out) + "\n\nCell: net hosts (wins/losses), exact sign-test p (two-sided, ties dropped), bootstrap 95% CI of the mean difference (5000 resamples, seed 1).\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
