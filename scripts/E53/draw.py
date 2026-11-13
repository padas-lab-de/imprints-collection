"""E53 step 4: draw the phase-2 gold sample (D60 D, target (h)) with inclusion probabilities, weights and folds.

    python3 -I scripts/E53/draw.py [--features datasets/E53/screen/screen_features.jsonl] [--out-dir datasets/E53/phase2]

Target (h) of scripts/E53/coverage.py: top level T=25 (POI L1, WZ sections, address cases) + POI L2 T=5 + WZ groups T=5.
Memberships are the union of the two screen models (and the text detector) restricted to the target classes.

Design (docs/gold_set_design.md 4.4, 4.5):
  core        first 600 of a seeded permutation of the screened sites (an SRS of the frame on its own);
  priority    each site belongs to the priority stratum of its rarest target class (fewest S1 members; "other:none" if none);
  oversample  rarest priority stratum first, uniformly at random from the not-yet-selected sites of that stratum, until the
              class has T members in the sample (all memberships counted) or its pool is empty (shortfall: all members drawn).
  probability pi_i = (n1 / N0) * (m_h / M_h) for the priority stratum h of site i, conditional on the realised m_h, M_h.
              w_i = 1 / pi_i. Within h the selected sites are a uniform random subset of size m_h (core: uniform; extras:
              uniform from the rest). m_h itself depends on the draw (the stopping rule looks at other strata), so pi is
              exact only conditional on the realised m_h; see results/E53/phase2_draw.md.
  folds       5 folds, stratified by priority stratum; strata with < 5 items are pooled per schema (poi, wz, address) into
              one "rare" stratum (D58 A). Items in a stratum are dealt round-robin to the folds in seeded random order.

Seed: SEED = 20261113 = frame seed 20261112 + 1. It is the seed of the size simulation in coverage.py, so the draw
reproduces that table (1,795 items for target (h)). Same seed and same input give the same output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
from ic.gold.sampling import NO_COVERAGE, _fill, priority_stratum, rarity_order  # noqa: E402

DATA = Path("/home/dinzinger/GitLab/fim/imprints-collection/datasets/E53")
FRAME_SEED = 20261112
SEED = FRAME_SEED + 1
CORE = 600
FOLDS = 5
ADDR = ["addr:at", "addr:ch", "addr:po_box", "addr:none", "addr:multi", "addr:non_dach", "lang:non_de"]


def target_h() -> tuple[dict[str, int], dict[str, str]]:
    """Target (h) -> ({class: T}, {class: depth label}). Needs the schema trees (scripts/E49/tree.py)."""
    sys.path.insert(0, str(ROOT / "scripts/E49"))
    from tree import load_schema  # noqa: E402

    t, w = load_schema("poi3", ROOT), load_schema("wz", ROOT)
    groups = [
        ("POI L1", [f"poi1:{i}" for i in t.at_level(1)], 25),
        ("WZ section", [f"wz1:{i}" for i in w.at_level(1)], 25),
        ("address cases", ADDR, 25),
        ("POI L2", [f"poi2:{i}" for i in t.at_level(2)], 5),
        ("WZ group", [f"wz3:{i}" for i in w.at_level(3)], 5),
    ]
    target, depth = {}, {}
    for g, cls, T in groups:
        for c in cls:
            target[c] = T
            depth[c] = g
    return target, depth


def schema_of(stratum: str) -> str:
    if stratum.startswith("poi"):
        return "poi"
    if stratum.startswith("wz"):
        return "wz"
    if stratum == NO_COVERAGE:
        return "other"
    return "addr"


def assign_folds(items: list[dict], seed: int, k: int = FOLDS) -> None:
    """Add `fold_group` and `fold` (0..k-1) to each item. Stratified by priority stratum, small strata pooled per schema."""
    size = Counter(it["stratum"] for it in items)
    for it in items:
        s = it["stratum"]
        it["fold_group"] = s if size[s] >= k else f"rare:{schema_of(s)}"
    by_group: dict[str, list[dict]] = {}
    for it in items:
        by_group.setdefault(it["fold_group"], []).append(it)
    rng = random.Random(seed + 7)
    offset = 0  # the round-robin continues across groups, so fold sizes differ by at most 1 overall
    for g in sorted(by_group):
        members = sorted(by_group[g], key=lambda it: it["host"])
        rng.shuffle(members)
        for j, it in enumerate(members):
            it["fold"] = (offset + j) % k
        offset += len(members)


def draw(
    recs: list[dict], target: dict[str, int], N0: int, n1: int, seed: int = SEED, core: int = CORE, min_stratum: int = 0
) -> tuple[list[dict], dict]:
    """Core + rarest-first oversample. recs: dicts with host and strata. Returns (items sorted by host, info).

    min_stratum > 0 (off by default, not part of target (h)): after the oversample, every priority stratum with M_h > 0
    is topped up uniformly at random to min(min_stratum, M_h) items, so that no stratum has weight 0 (see module doc)."""
    hosts = [r["host"] for r in recs]
    members = {r["host"]: [s for s in r["strata"] if s in target] for r in recs}
    order = rarity_order(list(members.values()))
    prio = {h: priority_stratum(members[h], order) for h in hosts}
    perm = list(hosts)
    random.Random(seed).shuffle(perm)
    core_set = set(perm[:core])
    sel = set(core_set)
    _fill(sel, members, prio, order, target, random.Random(seed + 1), None, perm)
    before = set(sel)
    M = Counter(prio.values())
    if min_stratum > 0:
        trng = random.Random(seed + 3)
        have = Counter(prio[h] for h in sel)
        for s in sorted(M):
            need = min(min_stratum, M[s]) - have[s]
            if need > 0:
                pool = [h for h in perm if prio[h] == s and h not in sel]
                sel.update(trng.sample(pool, need))
    m = Counter(prio[h] for h in sel)
    items = []
    for h in sorted(sel):
        p2 = m[prio[h]] / M[prio[h]]
        pi = (n1 / N0) * p2
        items.append(
            {
                "host": h,
                "core": h in core_set,
                "stratum": prio[h],
                "m_h": m[prio[h]],
                "M_h": M[prio[h]],
                "pi": pi,
                "weight": 1.0 / pi,
                "classes": members[h],
                "selected_for": [] if h in core_set else [prio[h]] if h in before else ["min_stratum:" + prio[h]],
            }
        )
    assign_folds(items, seed)
    S1, drawn = Counter(), Counter()
    for h in hosts:
        S1.update(members[h])
    for it in items:
        drawn.update(it["classes"])
    info = {"order": order, "M": dict(M), "m": dict(m), "S1": S1, "drawn": drawn}
    return items, info


def quota_rows(target: dict[str, int], depth: dict[str, str], info: dict) -> list[str]:
    rows = ["class\tdepth\ttarget_T\tscreen_members\tdrawn\tshortfall\tall_members_drawn"]
    for c in target:
        T, S, d = target[c], info["S1"][c], info["drawn"][c]
        rows.append(f"{c}\t{depth.get(c, '')}\t{T}\t{S}\t{d}\t{max(0, T - d)}\t{int(d >= S)}")
    return rows


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--features", default=str(DATA / "screen/screen_features.jsonl"))
    ap.add_argument("--frame", default=str(DATA / "frame/frame.json"))
    ap.add_argument("--out-dir", default=str(DATA / "phase2"))
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--core", type=int, default=CORE)
    ap.add_argument("--min-stratum", type=int, default=0, help="top up every priority stratum to this many items (default off)")
    a = ap.parse_args()
    recs = [json.loads(l) for l in open(a.features, encoding="utf-8") if l.strip()]
    fr = json.load(open(a.frame))
    N0, n1 = fr["N0"], fr["n1"]
    if len(set(r["host"] for r in recs)) != len(recs):
        sys.exit("duplicate hosts in the screen")
    target, depth = target_h()
    items, info = draw(recs, target, N0, n1, a.seed, a.core, a.min_stratum)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "gold_sample.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n")
    (out / "quota.tsv").write_text("\n".join(quota_rows(target, depth, info)) + "\n", encoding="utf-8")
    sw = sum(it["weight"] for it in items)
    empty = [s for s, M in info["M"].items() if info["m"].get(s, 0) == 0]
    print(
        f"screened {len(recs)} (n1 {n1}, N0 {N0}); items {len(items)} (core {sum(i['core'] for i in items)}); "
        f"sum of weights {sw:,.1f}; strata with M_h > 0 and m_h = 0: {len(empty)}"
    )
    print("sha256 gold_sample.jsonl", sha256_file(out / "gold_sample.jsonl"))
    print("sha256 quota.tsv", sha256_file(out / "quota.tsv"))


if __name__ == "__main__":
    main()
