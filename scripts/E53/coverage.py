"""E53 step 4: coverage of the schemas in the phase-1 screen and phase-2 sizes for several targets.

    python3 -I scripts/E53/coverage.py [--features datasets/E53/screen/screen_features.jsonl] [--partial]

Per depth (POI L1 8, POI L2 357, WZ section 22, division 87, group 287) and for the address cases: S1 members per
class (union of the two models and each model alone), estimated population count (x N0 / n_screened), number of
classes with >= 1, 5, 10, 25 members. Then phase-2 sizes: core 600 (first 600 of a seeded permutation of the
screened sites) + rarest-first oversample with union memberships (src/ic/gold/sampling.py _fill, docs/
gold_set_design.md 4.4) until every target class has T members in the sample (or its S1 pool is used up).
Writes results/E53/screen_coverage.md and datasets/E53/screen/coverage_classes.tsv.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/E49"))
sys.path.insert(0, str(ROOT / "src"))
from common import DATA  # noqa: E402
from tree import load_schema  # noqa: E402

from ic.gold.sampling import _fill, priority_stratum, rarity_order  # noqa: E402

ADDR = ["addr:at", "addr:ch", "addr:po_box", "addr:none", "addr:multi", "addr:non_dach", "lang:non_de"]
CORE = 600
SEED = 20261113  # simulation seed for the size table only (the real phase-2 draw records its own seed)


def depth_classes(trees) -> dict[str, list[str]]:
    t, w = trees["poi3"], trees["wz"]
    return {
        "POI L1": [f"poi1:{i}" for i in t.at_level(1)],
        "POI L2": [f"poi2:{i}" for i in t.at_level(2)],
        "WZ section": [f"wz1:{i}" for i in w.at_level(1)],
        "WZ division": [f"wz2:{i}" for i in w.at_level(2)],
        "WZ group": [f"wz3:{i}" for i in w.at_level(3)],
        "address cases": ADDR,
    }


def counts(recs, key):
    c = Counter()
    for r in recs:
        c.update(set(key(r)))
    return c


def fmt(n):
    return f"{n:,}"


def size_for(recs, target: dict[str, int], seed: int = SEED) -> dict:
    """Core + rarest-first oversample. target: stratum -> T. Memberships restricted to the target strata."""
    hosts = [r["host"] for r in recs]
    members = {r["host"]: [s for s in r["strata"] if s in target] for r in recs}
    order = rarity_order(list(members.values()))
    prio = {h: priority_stratum(members[h], order) for h in hosts}
    perm = list(hosts)
    random.Random(seed).shuffle(perm)
    sel = set(perm[:CORE])
    extra = _fill(sel, members, prio, order, target, random.Random(seed + 1), None, perm)
    m = Counter()
    for h in sel:
        m.update(members[h])
    S1 = Counter()
    for h in hosts:
        S1.update(members[h])
    short_s1 = [s for s in target if S1[s] < target[s]]
    short_sample = [s for s in target if m[s] < target[s]]
    return {"items": len(sel), "extra": extra, "short_s1": short_s1, "short_sample": short_sample, "S1": S1, "m": m}


def needed_n1(c: int, T: int, n: int) -> str:
    if c == 0:
        return f">{math.ceil(T * n / 3):,} (0 in S1; rule of three)"
    return f"{math.ceil(T * n / c):,}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default=str(DATA / "screen/screen_features.jsonl"))
    ap.add_argument("--frame", default=str(DATA / "frame/frame.json"))
    ap.add_argument("--out", default="results/E53/screen_coverage.md")
    ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    recs = [json.loads(l) for l in open(a.features, encoding="utf-8") if l.strip()]
    N0 = json.load(open(a.frame))["N0"]
    n = len(recs)
    f = N0 / n
    trees = {"poi3": load_schema("poi3"), "wz": load_schema("wz")}
    groups = depth_classes(trees)
    cu = counts(recs, lambda r: r["strata"])
    cg = counts(recs, lambda r: r["strata_model"]["gemma"] + r["strata_detector"])
    cq = counts(recs, lambda r: r["strata_model"]["qwen"] + r["strata_detector"])
    err = Counter()
    for r in recs:
        for s, e in r["errors"].items():
            for k, v in e.items():
                if v:
                    err[f"{k}_{s}"] += 1
    L = []
    title = "# E53 phase-1 screen: schema coverage and phase-2 sizes"
    if a.partial:
        title += " (PARTIAL: screen still running)"
    L += [title, "",
          f"Screened sites n = {fmt(n)} of S1 (n1 = 20,000); N0 = {fmt(N0)}; population estimate = count x N0 / n "
          f"= count x {f:,.1f}.",
          "Classes from the fixed E50 configs: POI v3 retrieve k30 (gemma r-short, qwen r-low), WZ retrieve k30 c1500,"
          " address mode main (f-schema). Union = either model (address cases: or the text detector). Prediction "
          "errors (counted as no class): " + (", ".join(f"{k} {v}" for k, v in sorted(err.items())) or "none") + ".",
          "", "## 1. Classes per depth", "",
          "| depth | classes | union >=1 | >=5 | >=10 | >=25 | gemma >=1 / >=10 / >=25 | qwen >=1 / >=10 / >=25 |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g, cls in groups.items():
        u = [cu[c] for c in cls]
        gm = [cg[c] for c in cls]
        qw = [cq[c] for c in cls]
        ge = lambda xs, k: sum(x >= k for x in xs)  # noqa: E731
        L.append(f"| {g} | {len(cls)} | {ge(u, 1)} | {ge(u, 5)} | {ge(u, 10)} | {ge(u, 25)} | "
                 f"{ge(gm, 1)} / {ge(gm, 10)} / {ge(gm, 25)} | {ge(qw, 1)} / {ge(qw, 10)} / {ge(qw, 25)} |")
    L += ["", "Per-class counts for all depths: `datasets/E53/screen/coverage_classes.tsv` (columns group, class, "
          "title, union, gemma, qwen, population estimate).", ""]
    rows = ["group\tclass\ttitle\tunion\tgemma\tqwen\tpop_est"]
    for g, cls in groups.items():
        for c in cls:
            pre, _, i = c.partition(":")
            t = trees["poi3"] if pre.startswith("poi") else trees["wz"] if pre.startswith("wz") else None
            title_ = t.title_of(i) if t is not None and i in t else c
            rows.append(f"{g}\t{c}\t{title_}\t{cu[c]}\t{cg[c]}\t{cq[c]}\t{round(cu[c] * f)}")
    Path(DATA / "screen/coverage_classes.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    for g in ("POI L1", "WZ section", "address cases"):
        L += [f"### {g}", "", "| class | title | union | gemma | qwen | population est. |", "|---|---|---:|---:|---:|---:|"]
        for c in sorted(groups[g], key=lambda c: -cu[c]):
            pre, _, i = c.partition(":")
            t = trees["poi3"] if pre.startswith("poi") else trees["wz"] if pre.startswith("wz") else None
            title_ = t.title_of(i) if t is not None and i in t else ""
            L.append(f"| {c} | {title_} | {cu[c]} | {cg[c]} | {cq[c]} | {fmt(round(cu[c] * f))} |")
        L.append("")
    for g in ("POI L2", "WZ division", "WZ group"):
        cls = groups[g]
        dist = Counter(min(cu[c], 10**9) for c in cls)
        bins = [(0, 0), (1, 4), (5, 9), (10, 24), (25, 99), (100, 10**9)]
        L.append(f"### {g}: classes by union count in S1")
        L.append("")
        L.append("| members in S1 | " + " | ".join(f"{lo}-{hi}" if hi < 10**9 else f">={lo}" for lo, hi in bins) + " |")
        L.append("|---|" + "---:|" * len(bins))
        L.append("| classes | " + " | ".join(str(sum(v for k, v in dist.items() if lo <= k <= hi)) for lo, hi in bins)
                 + " |")
        L.append("")
    # ---- size table
    top = groups["POI L1"] + groups["WZ section"] + ADDR
    scen = {
        "(a) top level T=25 (POI L1, WZ sections, address cases)": {s: 25 for s in top},
        "(b) (a) + WZ divisions T=10": {**{s: 25 for s in top}, **{s: 10 for s in groups["WZ division"]}},
        "(c) (b) + POI L2 T=5": {**{s: 25 for s in top}, **{s: 10 for s in groups["WZ division"]},
                                 **{s: 5 for s in groups["POI L2"]}},
        "(d) (b) + POI L2 T=10": {**{s: 25 for s in top}, **{s: 10 for s in groups["WZ division"]},
                                  **{s: 10 for s in groups["POI L2"]}},
        "(e) (a) + WZ divisions T=5 + POI L2 T=5": {**{s: 25 for s in top}, **{s: 5 for s in groups["WZ division"]},
                                                     **{s: 5 for s in groups["POI L2"]}},
        "(f) (d) + WZ groups T=5": {**{s: 25 for s in top}, **{s: 10 for s in groups["WZ division"]},
                                    **{s: 10 for s in groups["POI L2"]}, **{s: 5 for s in groups["WZ group"]}},
        "(g) top level T=10 + WZ divisions T=10 + POI L2 T=10": {**{s: 10 for s in top},
                                                                 **{s: 10 for s in groups["WZ division"]},
                                                                 **{s: 10 for s in groups["POI L2"]}},
    }
    L += ["## 2. Phase-2 size per target", "",
          f"Core {CORE} (first {CORE} of a seeded permutation of the screened sites, seed {SEED}) + rarest-first "
          "oversample with union memberships (`src/ic/gold/sampling.py` `_fill`, no budget). A class is **short in S1** "
          "if it has fewer than T union members in the screen; then all its members are drawn. 'n1 to fill' = size of "
          "S1 at which the rarest short class with >= 1 member would have T members (T x n / count); classes with 0 "
          "members need more than T x n / 3 (rule of three, 95%).", "",
          "| target | items (core + extra) | target classes | short in S1 (0 members) | still short in sample | "
          "n1 to fill all short classes with >= 1 member |",
          "|---|---:|---:|---:|---:|---:|"]
    detail = []
    for name, tg in scen.items():
        r = size_for(recs, tg)
        zero = sum(1 for s in r["short_s1"] if r["S1"][s] == 0)
        pos = [s for s in r["short_s1"] if r["S1"][s] > 0]
        need = max((math.ceil(tg[s] * n / r["S1"][s]) for s in pos), default=n)
        L.append(f"| {name} | {fmt(r['items'])} ({CORE} + {fmt(r['extra'])}) | {len(tg)} | {len(r['short_s1'])} "
                 f"({zero}) | {len(r['short_sample'])} | {fmt(need)} |")
        by_g = Counter()
        for s in r["short_s1"]:
            g = next(gg for gg, cls in groups.items() if s in cls)
            by_g[g] += 1
        detail.append(f"- {name}: short in S1 by depth: "
                      + (", ".join(f"{g} {k}" for g, k in by_g.items()) or "none")
                      + ". Short top-level/address classes: "
                      + (", ".join(f"{s} ({r['S1'][s]})" for s in r["short_s1"] if s in top) or "none") + ".")
    L += ["", *detail, ""]
    L += ["## 3. S1 size needed per depth (union counts)", "",
          "Smallest n1 at which every class with >= 1 member in the screen reaches T (T x n / min count), and number "
          "of classes with 0 members in the screen.", "",
          "| depth | 0 members | T=5 | T=10 | T=25 |", "|---|---:|---:|---:|---:|"]
    for g, cls in groups.items():
        pos = [cu[c] for c in cls if cu[c] > 0]
        mn = min(pos) if pos else 0
        L.append(f"| {g} | {sum(cu[c] == 0 for c in cls)} | "
                 + " | ".join(fmt(math.ceil(T * n / mn)) if mn else "-" for T in (5, 10, 25)) + " |")
    L.append("")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
