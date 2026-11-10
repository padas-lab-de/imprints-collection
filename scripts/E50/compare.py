"""E50: topic screening tables and paired comparisons with the selection rule of results/E50/design.md section 7.

    python3 scripts/E50/compare.py --schema poi3 --refs results/E49/refs/poi_v3.jsonl \
        --dir results/E50/preds/dev/poi3 --base gemma=r-short --base qwen=r-default --base agentworld=r-short \
        --out results/E50/screen/poi3.md

Run names (topic.tag): <strategy|task>__<model>__r-<reasoning>[__<variant>...]. A run is (model, reasoning, variant);
variant "base" = no variant part and the default first part (poi3 flat, wz retrieve, address address); another first
part (retrieve for POI, joint-poi-wz[-address]) is put in front of the variant. --base gives the reasoning level of
each model's base run. --hosts restricts every run to the hosts in a file (one table per data part).
--schema address: refs and preds in the addr_score format; level 1 hit = main_ok (main address equal, or both
without a main address; cov = 1), level 2 hit = main address exact among hosts where reference and prediction have a
main address (cov = both have one). L* = 1.
Comparisons:
  reasoning (per model): every (model, r-X, base) vs (model, base reasoning, base)
  variants: every (model, base reasoning, V) vs (model, base reasoning, base); pooled over the --main models that
            have V; other models are guards.
Hosts: dev hosts with a non-null reference that every compared run has (pairs: common to the runs in the pair or
pooled group). Per host and level L: hit = predicted canonical path prefix == reference prefix (reference reaches L;
abstention, failure and stopping above L = miss); cov = prediction and reference reach L. acc@L = mean hit;
P@L = sum hit / sum cov.
Paired: d = variant - base; 95% CI from a host bootstrap (5000, seed 1; pooled: hosts resampled, all models of a host
kept together; pooled d = mean of the model d); exact sign test on the per host x model hit at L*.
Cost per host: C = (prompt - cached prompt) + 10 x completion tokens; C0 = without the cache credit.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E49"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import load_schema  # noqa: E402

LSTAR = {"poi3": 2, "wz": 3, "address": 1}
DEFAULT_FIRST = {"poi3": "flat", "wz": "retrieve", "address": "address"}
OUT_W = 10  # completion token weight in C
B = 5000


def load_jsonl(p) -> list[dict]:
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").split("\n") if l.strip()]


def parse_tag(stem: str, schema: str | None = None) -> tuple[str, str, str]:
    parts = stem.split("__")
    model = parts[1]
    rea = parts[2] if len(parts) > 2 and parts[2].startswith("r-") else "r-?"
    rest = parts[3:]
    if schema and parts[0] != DEFAULT_FIRST[schema]:
        rest = [parts[0]] + rest
    var = "__".join(rest) or "base"
    return model, rea, var


class AddrLevels:
    """Stands in for the tree in address mode: two levels (main_ok, exact among both-main)."""
    max_level = 2


def _usage(p: dict) -> dict:
    u = p.get("usage") or {}
    tin, cin, tout = u.get("prompt_tokens", 0), u.get("cached_prompt_tokens", 0), u.get("completion_tokens", 0)
    return {"fail": int(bool(p.get("error"))), "tok_in": tin, "cached_in": cin, "tok_out": tout,
            "reasoning": u.get("reasoning_tokens", 0), "C": tin - cin + OUT_W * tout, "C0": tin + OUT_W * tout,
            "calls": u.get("calls", 0), "s": p.get("latency_s", 0.0), "fast": u.get("fast_calls", 0),
            "trunc": u.get("truncated", 0)}


def addr_vectors(refs_raw: dict, preds: list[dict]) -> dict[str, dict]:
    import addr_score as AS
    refs = {h: AS.to_record(r) for h, r in refs_raw.items()}
    pr = {p["host"]: AS.to_record(p) for p in preds if p["host"] in refs}
    ph = AS.score(refs, pr)["per_host"]
    out = {}
    for p in preds:
        h = p["host"]
        if h not in ph:
            continue
        v = ph[h]
        out[h] = {"hit": [int(v["main_ok"]), int(v["exact"])], "cov": [1, int(v["both_main"])], **_usage(p)}
    return out


def host_vectors(tree, refs: dict, preds: list[dict]) -> dict[str, dict]:
    """host -> {hit: [L1..Lmax], cov: [...], fail, C, C0, tok_in, cached_in, tok_out, calls, s, fast}."""
    P = lambda i: tree.canonical_path(i) if i in tree else []  # noqa: E731
    out = {}
    for p in preds:
        r = refs.get(p["host"])
        if r is None or r.get("main") is None or r["main"] not in tree or p.get("error") == "no_input":
            continue
        rp, pp = P(r["main"]), P(p.get("main"))
        hit, cov = [], []
        for L in range(1, tree.max_level + 1):
            hit.append(int(len(rp) >= L and len(pp) >= L and pp[:L] == rp[:L]))
            cov.append(int(len(rp) >= L and len(pp) >= L))
        out[p["host"]] = {"hit": hit, "cov": cov, **_usage(p)}
    return out


def summary(v: dict[str, dict], hosts: list[str], L: int) -> dict:
    n = len(hosts)
    m = lambda k: sum(v[h][k] for h in hosts) / n if n else float("nan")  # noqa: E731
    acc = [sum(v[h]["hit"][j] for h in hosts) / n for j in range(len(v[hosts[0]]["hit"]))] if n else []
    prec = []
    for j in range(len(acc)):
        c = sum(v[h]["cov"][j] for h in hosts)
        prec.append(sum(v[h]["hit"][j] for h in hosts) / c if c else float("nan"))
    covL = sum(v[h]["cov"][L - 1] for h in hosts) / n if n else float("nan")
    return {"n": n, "acc": acc, "P": prec, "covL": covL, "fail": m("fail"), "tok_in": m("tok_in"),
            "cached_in": m("cached_in"), "tok_out": m("tok_out"), "reasoning": m("reasoning"), "C": m("C"),
            "C0": m("C0"), "calls": m("calls"), "s": m("s"), "trunc": m("trunc")}


def sign_p(w: int, l: int) -> float:
    n = w + l
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(w, l) + 1)) / 2 ** n)


def _accP(v, hosts, j):
    n = len(hosts)
    hit = sum(v[h]["hit"][j] for h in hosts)
    cov = sum(v[h]["cov"][j] for h in hosts)
    return hit / n, (hit / cov if cov else float("nan"))


def paired(pairs: list[tuple[dict, dict]], hosts: list[str], L: int) -> dict:
    """pairs: [(variant vectors, base vectors)] per model. Pooled d = mean over models."""
    j = L - 1

    def deltas(hs):
        da, dp = [], []
        for var, base in pairs:
            a1, p1 = _accP(var, hs, j)
            a0, p0 = _accP(base, hs, j)
            da.append(a1 - a0)
            dp.append(p1 - p0)
        return da, dp

    da, dp = deltas(hosts)
    rng = random.Random(1)
    bs = []
    n = len(hosts)
    for _ in range(B):
        hs = [hosts[rng.randrange(n)] for _ in range(n)]
        a, p = deltas(hs)
        bs.append((sum(a) / len(a), sum(p) / len(p)))
    col = sorted(b[0] for b in bs)
    colp = sorted(b[1] for b in bs if b[1] == b[1])
    w = sum(var[h]["hit"][j] > base[h]["hit"][j] for var, base in pairs for h in hosts)
    l_ = sum(var[h]["hit"][j] < base[h]["hit"][j] for var, base in pairs for h in hosts)
    ratio = (sum(sum(var[h]["C"] for h in hosts) for var, _ in pairs) /
             max(1, sum(sum(base[h]["C"] for h in hosts) for _, base in pairs)))
    return {"n": n, "d": sum(da) / len(da), "d_models": da, "lo": col[int(.025 * B)], "hi": col[int(.975 * B)],
            "dP": sum(dp) / len(dp), "dP_lo": colp[int(.025 * len(colp))] if colp else float("nan"),
            "dP_hi": colp[int(.975 * len(colp))] if colp else float("nan"),
            "wins": w, "losses": l_, "p": sign_p(w, l_), "cost_ratio": ratio}


def verdict(pr: dict, guard_d: list[float], fails: list[float]) -> str:
    """Selection rule, design.md section 7 (point 1-3, 5); guard_d = d of every model incl. guard models."""
    adm = (max(fails) <= 0.01 and pr["d"] >= -0.01 and pr["lo"] >= -0.04 and min(guard_d) >= -0.03
           and not pr["dP"] < -0.03)
    if not adm:
        return "worse/inadmissible"
    better = pr["lo"] > 0 or (pr["p"] < 0.05 and pr["d"] > 0)
    r = pr["cost_ratio"]
    if better and (r <= 1.5 or pr["d"] >= 0.02 * math.log2(r)):
        return "better"
    if r <= 0.9:
        return "cheaper, non-inferior"
    if better:
        return "better, too costly"
    return "no difference"


def f3(x) -> str:
    return "" if x is None or x != x else f"{x:.3f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True, choices=["poi3", "wz", "address"])
    ap.add_argument("--hosts", default=None, help="file with one host per line (a data part)")
    ap.add_argument("--title", default=None, help="extra text for the table heading (e.g. the part name)")
    ap.add_argument("--refs", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--base", action="append", default=[], help="model=r-level (base reasoning of the model)")
    ap.add_argument("--main", default="gemma,qwen", help="models pooled for prompt factors")
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    tree = AddrLevels() if a.schema == "address" else load_schema(a.schema)
    L = LSTAR[a.schema]
    refs = {r["host"]: r for r in load_jsonl(a.refs)}
    if a.hosts:
        want = {l.strip() for l in Path(a.hosts).read_text(encoding="utf-8").splitlines() if l.strip()}
        refs = {h: r for h, r in refs.items() if h in want}
    runs = {}
    for f in sorted(Path(a.dir).glob("*.jsonl")):
        if not re.match(r"^(flat|retrieve|address|joint-[a-z-]+)__", f.stem):
            continue
        preds = load_jsonl(f)
        v = addr_vectors(refs, preds) if a.schema == "address" else host_vectors(tree, refs, preds)
        if v:
            runs[parse_tag(f.stem, a.schema)] = v
    base_r = dict(b.split("=") for b in a.base)
    main_models = [m for m in a.main.split(",") if m]
    lines = [f"# E50 screening, {a.schema}, {a.title or 'dev'} (L* = {L})", "",
             "## Runs", "",
             "| model | reasoning | variant | n | fail | cut | " + " | ".join(f"acc@{i}" for i in range(1, tree.max_level + 1))
             + " | " + " | ".join(f"P@{i}" for i in range(1, tree.max_level + 1))
             + f" | cov@{L} | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |",
             "|" + "---|" * (15 + 2 * tree.max_level)]
    allsum = {}
    for key in sorted(runs):
        v = runs[key]
        hs = sorted(v)
        s = summary(v, hs, L)
        allsum["|".join(key)] = s
        lines.append("| " + " | ".join([key[0], key[1], key[2], str(s["n"]), f"{s['fail']:.3f}", f"{s['trunc']:.3f}"]
                                       + [f3(x) for x in s["acc"]] + [f3(x) for x in s["P"]] +
                                       [f3(s["covL"]), f"{s['calls']:.2f}", f"{s['tok_in']:.0f}", f"{s['cached_in']:.0f}",
                                        f"{s['tok_out']:.0f}", f"{s['reasoning']:.0f}", f"{s['C']:.0f}", f"{s['C0']:.0f}",
                                        f"{s['s']:.1f}"]) + " |")
    res = {"runs": allsum, "reasoning": [], "variants": []}
    # reasoning per model
    lines += ["", f"## Reasoning level vs base level (per model, paired, acc@{L})", "",
              "| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, br in sorted(base_r.items()):
        b = runs.get((m, br, "base"))
        if not b:
            continue
        for (m2, r2, v2), var in sorted(runs.items()):
            if m2 != m or v2 != "base" or r2 == br:
                continue
            hs = sorted(set(b) & set(var))
            pr = paired([(var, b)], hs, L)
            fails = [summary(var, hs, L)["fail"]]
            vd = verdict(pr, pr["d_models"], fails)
            res["reasoning"].append({"model": m, "level": r2, "base": br, **pr, "verdict": vd})
            lines.append(f"| {m} | {r2} | {br} | {pr['n']} | {pr['d']:+.3f} | [{pr['lo']:+.3f}, {pr['hi']:+.3f}] | "
                         f"{pr['dP']:+.3f} | {pr['wins']}/{pr['losses']} | {pr['p']:.3f} | {pr['cost_ratio']:.2f} | {vd} |")
    # prompt variants
    lines += ["", f"## Prompt variants vs base prompt (base reasoning per model; pooled over {', '.join(main_models)})", "",
              "| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    variants = sorted({k[2] for k in runs if k[2] != "base"})
    for var in variants:
        have = [m for m, br in base_r.items() if (m, br, var) in runs and (m, br, "base") in runs]
        pooled = [m for m in main_models if m in have]
        if not pooled:
            continue
        hs = set.intersection(*[set(runs[(m, base_r[m], var)]) & set(runs[(m, base_r[m], "base")]) for m in pooled])
        hs = sorted(hs)
        pr = paired([(runs[(m, base_r[m], var)], runs[(m, base_r[m], "base")]) for m in pooled], hs, L)
        guard = {}
        for m in have:
            hs_m = sorted(set(runs[(m, base_r[m], var)]) & set(runs[(m, base_r[m], "base")]))
            guard[m] = paired([(runs[(m, base_r[m], var)], runs[(m, base_r[m], "base")])], hs_m, L)
        fails = [summary(runs[(m, base_r[m], var)], sorted(runs[(m, base_r[m], var)]), L)["fail"] for m in have]
        vd = verdict(pr, [g["d"] for g in guard.values()], fails)
        if set(pooled) != set(main_models):
            vd += " (not all main models)"
        res["variants"].append({"variant": var, "models": have, **pr, "guard": {m: g["d"] for m, g in guard.items()},
                                "verdict": vd})
        per = ", ".join(f"{m} {g['d']:+.3f}" for m, g in sorted(guard.items()))
        lines.append(f"| {var} | {'+'.join(sorted(have))} | {pr['n']} | {pr['d']:+.3f} | [{pr['lo']:+.3f}, {pr['hi']:+.3f}] | "
                     f"{per} | {pr['dP']:+.3f} | {pr['wins']}/{pr['losses']} | {pr['p']:.3f} | {pr['cost_ratio']:.2f} | {vd} |")
    lines += ["", "acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L "
              "(abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference "
              "reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + "
              f"{OUT_W} x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. "
              "Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, "
              "dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9)."]
    if a.schema == "address":
        lines += ["", "Address: acc@1 = main_ok (main address equal on street, number, postcode, town, or both without a "
                  "main address); acc@2 = main exact over all hosts; P@2 = main exact among hosts where reference and "
                  "prediction both have a main address (cov@2 = their share)."]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
