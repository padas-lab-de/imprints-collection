"""E49 poi3b: tables and paired comparisons for poi3 node-text variants on dev and held-out.

    python3 scripts/E49/poi3b_summary.py --out results/E49/poi3b/summary_tables.md
Configs (qwen38-27b flat think input both): a = current poi3, b = --node-lang both, c = b + --mfr-line;
gemma4-31b-it flat reason both: a, b (held-out only). Hosts scored = common to all configs of the set
(dev: qwen a,b,c; held-out: all five) with a non-null reference. Subsets: all hosts, offline (online_only false).
Paired: per host hit@L (canonical path prefix equals reference prefix; abstention = miss); bootstrap (5000, seed 1)
over hosts for the difference in acc@1, acc@2 and P@2 (precision among covered), exact sign test on acc@2.
"""
import argparse, json, random, sys
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import load_jsonl, score  # noqa: E402
from tree import load_schema  # noqa: E402

Q = "flat__qwen__both__dmax__nt-path__think"
G = "flat__gemma__both__dmax__nt-path__reason"
SETS = {
    "dev": {"refs": "results/E49/refs/poi_v3.jsonl", "cfgs": {
        "qwen a current": "results/E49/poi3/preds/poi3/" + Q,
        "qwen b bilingual": "results/E49/poi3b/preds/dev/poi3/" + Q + "__nl-both",
        "qwen c bilingual+mfr": "results/E49/poi3b/preds/dev/poi3/" + Q + "__nl-both__mfrline"}},
    "held-out": {"refs": "results/E49/heldout/refs/poi_v3.jsonl", "cfgs": {
        "qwen a current": "results/E49/poi3b/preds/heldout/poi3/" + Q,
        "qwen b bilingual": "results/E49/poi3b/preds/heldout/poi3/" + Q + "__nl-both",
        "qwen c bilingual+mfr": "results/E49/poi3b/preds/heldout/poi3/" + Q + "__nl-both__mfrline",
        "gemma a current": "results/E49/poi3b/preds/heldout/poi3/" + G,
        "gemma b bilingual": "results/E49/poi3b/preds/heldout/poi3/" + G + "__nl-both"}},
}
PAIRS = [("qwen b bilingual", "qwen a current"), ("qwen c bilingual+mfr", "qwen a current"),
         ("qwen c bilingual+mfr", "qwen b bilingual"), ("gemma b bilingual", "gemma a current")]
tree = load_schema("poi3")
P = lambda i: tree.canonical_path(i) if i in tree else []  # noqa: E731


def hit(r, p, L):
    rp, pp = P(r["main"]), P(p.get("main"))
    cov = len(pp) >= L and len(rp) >= L
    return int(bool(pp) and pp[:L] == rp[:L] and len(rp) >= L), cov


def sign_p(w, l):
    n = w + l
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(w, l) + 1)) / 2 ** n)


def stats(hs):  # hs: list of (acc1, acc2, cov2, hit2) per host -> acc1, acc2, P2
    n = len(hs)
    c = sum(h[2] for h in hs)
    return (sum(h[0] for h in hs) / n, sum(h[1] for h in hs) / n, (sum(h[3] for h in hs) / c) if c else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/E49/poi3b/summary_tables.md")
    a = ap.parse_args()
    out = []
    for sname, S in SETS.items():
        refs = {r["host"]: r for r in load_jsonl(S["refs"])}
        preds = {}
        for k, f in S["cfgs"].items():
            if Path(f + ".jsonl").is_file():
                preds[k] = {p["host"]: p for p in load_jsonl(f + ".jsonl")}
        keep = {h for h, r in refs.items() if r["main"] is not None}
        for ps in preds.values():
            keep &= {h for h, p in ps.items() if p.get("error") != "no_input"}
        for sub, hosts in (("all hosts", keep), ("offline (online_only false)", {h for h in keep if not refs[h]["online_only"]})):
            out += [f"### {sname}, {sub} (n={len(hosts)})", "",
                    "| config | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | tok in | tok out |", "|---|---|---|---|---|---|---|---|---|---|---|"]
            for k, ps in preds.items():
                m = score(tree, refs, [p for h, p in ps.items() if h in hosts])
                L = {x["level"]: x for x in m["levels"]}
                c = m["cost_per_host"]
                out.append(f"| {k} | {m['n_scored']} | {m['abstain']} | {m['errors']} | {L[1]['precision']:.3f} | {L[2]['precision']:.3f} | "
                           f"{L[1]['acc_trunc']:.3f} | {L[2]['acc_trunc']:.3f} | {L[2]['coverage']:.3f} | {c['prompt_tokens']} | {c['completion_tokens']} |")
            out.append("")
            out += [f"Paired ({sname}, {sub}): difference x - y, 95% bootstrap CI over hosts", "",
                    "| x vs y | n | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |", "|---|---|---|---|---|---|"]
            for x, y in PAIRS:
                if x not in preds or y not in preds:
                    continue
                hs = sorted(hosts)
                v = {}
                for k in (x, y):
                    v[k] = []
                    for h in hs:
                        h1, _ = hit(refs[h], preds[k][h], 1)
                        h2, c2 = hit(refs[h], preds[k][h], 2)
                        v[k].append((h1, h2, int(c2), h2 if c2 else 0))
                d0 = [u - w for u, w in zip(stats(v[x]), stats(v[y]))]
                rng = random.Random(1)
                boots = []
                for _ in range(5000):
                    idx = [rng.randrange(len(hs)) for _ in hs]
                    sx, sy = stats([v[x][i] for i in idx]), stats([v[y][i] for i in idx])
                    boots.append([u - w for u, w in zip(sx, sy)])
                ci = []
                for j in range(3):
                    col = sorted(b[j] for b in boots if b[j] == b[j])
                    ci.append((col[int(.025 * len(col))], col[int(.975 * len(col))]))
                w = sum(p[1] > q[1] for p, q in zip(v[x], v[y]))
                l = sum(p[1] < q[1] for p, q in zip(v[x], v[y]))
                f = lambda j: f"{d0[j]:+.3f} [{ci[j][0]:+.3f},{ci[j][1]:+.3f}]"  # noqa: E731
                out.append(f"| {x} vs {y} | {len(hs)} | {f(0)} | {f(1)} | {f(2)} | {w}/{l}, p={sign_p(w, l):.2f} |")
            out.append("")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
