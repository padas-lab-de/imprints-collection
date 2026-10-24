"""Item assignment for the gold-set labelling (E18).

Plan (see docs/annotation_guideline.md and the E18 notes):

* Three labellers; L1 has twice the capacity of L2 and L3 (target share 2:1:1).
* ``n_cal`` calibration items (default 50) are labelled by all three. They are
  counted inside each labeller's load (they are real labelling work) and they
  replace the item's primary label (the consensus after discussion is its gold
  label), so they are not part of the single-label pool or of the second-label
  draw.
* Every other item has exactly one primary labeller.
* ``n_second`` items (default 200) get an independent second labeller who
  differs from the primary. Second labels are spread over all six
  (primary, second) pairs, with fewer L2/L3 pairs because L1 carries the load.
* The double-labelled items are chosen so that every sampling stratum
  (membership in item["strata"]) with >= 10 items in the sample has at least
  min(10, available) double-labelled items. This is a set cover over the
  marginal strata. Covering the 29 *priority* strata with 10 each would need
  more than 260 items, which exceeds the 200 budget.
* Each labeller sees the calibration block first, then the rest in random
  order (not grouped by stratum).
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict

LABELLERS = ("L1", "L2", "L3")
CAPACITY = {"L1": 2, "L2": 1, "L3": 1}
# (primary, second) pair shares among the double-labelled items; L1 second
# labels cannot exceed what L2 and L3 primaries supply.
PAIR_SHARE = {
    ("L1", "L2"): 40,
    ("L1", "L3"): 40,
    ("L2", "L1"): 40,
    ("L3", "L1"): 40,
    ("L2", "L3"): 20,
    ("L3", "L2"): 20,
}
MIN_PER_STRATUM = 10


def _largest_deficit_deal(keys, quotas):
    """Assign ``keys`` (already in the order to deal) to labels, proportional to
    ``quotas`` at every prefix, exactly meeting the totals."""
    total = sum(quotas.values())
    assert total == len(keys), (total, len(keys))
    left = dict(quotas)
    got = Counter()
    out = {}
    for n, k in enumerate(keys, 1):
        best = max(
            (lab for lab in left if left[lab] > 0),
            key=lambda lab: quotas[lab] * n / total - got[lab],
        )
        out[k] = best
        got[best] += 1
        left[best] -= 1
    return out


def pick_calibration(items, rng, n_cal=50, n_neg=6):
    """Calibration set: mostly positives, round-robin over priority strata so
    that hard cases appear; a few negatives so that the negative rules are
    exercised too."""
    pos, neg = defaultdict(list), defaultdict(list)
    for it in items:
        (neg if it["priority_stratum"].startswith("neg:") else pos)[it["priority_stratum"]].append(it)
    chosen = []

    def round_robin(groups, n):
        names = sorted(groups)
        rng.shuffle(names)
        pools = {g: rng.sample(groups[g], len(groups[g])) for g in names}
        out = []
        while len(out) < n and any(pools.values()):
            for g in names:
                if pools[g] and len(out) < n:
                    out.append(pools[g].pop())
        return out

    n_neg = min(n_neg, n_cal)
    chosen += round_robin(neg, n_neg)
    chosen += round_robin(pos, n_cal - len(chosen))
    return chosen


def stratum_sizes(items):
    c = Counter()
    for it in items:
        for s in set(it.get("strata") or []):
            c[s] += 1
    return c


def pick_second(pool, rng, n_second=200, min_per=MIN_PER_STRATUM, sizes=None):
    """Choose the double-labelled items from ``pool``: greedy cover of the marginal
    strata, then fill proportionally over priority strata."""
    sizes = sizes or stratum_sizes(pool)
    need = {s: min(min_per, n) for s, n in stratum_sizes(pool).items() if sizes.get(s, 0) >= min_per}
    have = Counter()
    chosen, chosen_ids = [], set()

    def add(it):
        chosen.append(it)
        chosen_ids.add(it["item"])
        for s in set(it.get("strata") or []):
            have[s] += 1

    def deficit(s):
        return need.get(s, 0) - have[s]

    cands = list(pool)
    rng.shuffle(cands)
    while len(chosen) < n_second:
        open_strata = [s for s in need if deficit(s) > 0]
        if not open_strata:
            break
        # rarest open stratum first (fewest candidates in the pool)
        s0 = min(open_strata, key=lambda s: (sum(1 for it in cands if s in it["strata"]), s))
        options = [it for it in cands if it["item"] not in chosen_ids and s0 in it["strata"]]
        if not options:
            need[s0] = have[s0]  # cannot be met (pool exhausted)
            continue
        # prefer the item that closes the most other open deficits
        best = max(options, key=lambda it: sum(1 for s in set(it["strata"]) if deficit(s) > 0))
        add(best)
    cover_n = len(chosen)
    # fill: equalise the sampling fraction over priority strata
    by_prio = defaultdict(list)
    for it in pool:
        by_prio[it["priority_stratum"]].append(it)
    taken = Counter(it["priority_stratum"] for it in chosen)
    while len(chosen) < n_second:
        open_p = [p for p in by_prio if any(i["item"] not in chosen_ids for i in by_prio[p])]
        p = min(open_p, key=lambda p: (taken[p] / len(by_prio[p]), p))
        it = rng.choice([i for i in by_prio[p] if i["item"] not in chosen_ids])
        add(it)
        taken[p] += 1
    return chosen, cover_n


def build_assignment(items, seed=20261024, n_cal=50, n_second=200):
    """Return (rows, info). ``items``: list of dicts with item, host, strata, priority_stratum."""
    rng = random.Random(seed)
    items = sorted(items, key=lambda it: it["item"])
    hosts = [it["host"] for it in items]
    if len(set(hosts)) != len(hosts) or len({it["item"] for it in items}) != len(items):
        raise ValueError("items/hosts must be unique")
    n = len(items)
    cal = pick_calibration(items, rng, n_cal)
    cal_ids = {it["item"] for it in cal}
    pool = [it for it in items if it["item"] not in cal_ids]
    full_sizes = stratum_sizes(items)
    second, cover_n = pick_second(pool, rng, n_second, sizes=full_sizes)
    sec_ids = {it["item"] for it in second}
    single = [it for it in pool if it["item"] not in sec_ids]

    # The 2:1:1 split applies to ALL labels incl. calibration (each labeller does
    # n_cal of those); ``load`` is what is left outside the calibration block.
    cap_sum = sum(CAPACITY.values())
    target_total = (n - n_cal) + n_second + len(LABELLERS) * n_cal
    load = {lab: round(target_total * CAPACITY[lab] / cap_sum) - n_cal for lab in LABELLERS}
    load["L1"] += (n - n_cal) + n_second - sum(load.values())
    # second labels per labeller / primaries per labeller among doubles from PAIR_SHARE
    scale = n_second / sum(PAIR_SHARE.values())
    pairs = {k: round(v * scale) for k, v in PAIR_SHARE.items()}
    drift = n_second - sum(pairs.values())
    pairs[("L1", "L2")] += drift
    sec_cnt = Counter()
    prim_double = Counter()
    for (p, s), v in pairs.items():
        sec_cnt[s] += v
        prim_double[p] += v
    prim_total = {lab: load[lab] - sec_cnt[lab] for lab in LABELLERS}
    prim_single = {lab: prim_total[lab] - prim_double[lab] for lab in LABELLERS}
    if min(prim_single.values()) < 0 or sum(prim_single.values()) != len(single):
        raise ValueError(f"inconsistent quotas: {prim_single} for {len(single)} single items")

    def stratified(its):
        order = sorted(its, key=lambda it: (it["priority_stratum"], rng.random()))
        return order

    rows = []
    # doubles: deal pair labels stratified by priority stratum
    dbl_order = stratified(second)
    pair_of = _largest_deficit_deal([it["item"] for it in dbl_order], pairs)
    for it in second:
        p, s = pair_of[it["item"]]
        rows.append((it, p, "primary"))
        rows.append((it, s, "second"))
    sgl_order = stratified(single)
    lab_of = _largest_deficit_deal([it["item"] for it in sgl_order], prim_single)
    for it in single:
        rows.append((it, lab_of[it["item"]], "primary"))
    for it in cal:
        for lab in LABELLERS:
            rows.append((it, lab, "calibration"))

    out = []
    for lab in LABELLERS:
        mine = [(it, role) for it, l, role in rows if l == lab]
        calib = [r for r in mine if r[1] == "calibration"]
        rest = [r for r in mine if r[1] != "calibration"]
        rng.shuffle(calib)
        rng.shuffle(rest)
        for k, (it, role) in enumerate(calib + rest, 1):
            out.append({"item": it["item"], "host": it["host"], "labeller": lab, "role": role, "order": k})
    info = {"n_cover": cover_n, "pairs": pairs, "load_noncal": load}
    return out, info


def summarise(rows, items):
    """Return text lines: loads per labeller and per-pair overlap counts."""
    lines = []
    loads = defaultdict(Counter)
    for r in rows:
        loads[r["labeller"]][r["role"]] += 1
    lines.append("loads per labeller (primary / second / calibration / total):")
    for lab in LABELLERS:
        c = loads[lab]
        lines.append(f"  {lab}: {c['primary']:4d} / {c['second']:4d} / {c['calibration']:3d} / {sum(c.values()):4d}")
    lines.append(f"  all: total labels {sum(sum(c.values()) for c in loads.values())}")
    by_item = defaultdict(dict)
    for r in rows:
        by_item[r["item"]].setdefault(r["role"], []).append(r["labeller"])
    pair = Counter()
    for roles in by_item.values():
        if "second" in roles:
            pair[(roles["primary"][0], roles["second"][0])] += 1
    lines.append("double-labelled items by (primary -> second):")
    for p in LABELLERS:
        for s in LABELLERS:
            if p != s:
                lines.append(f"  {p} -> {s}: {pair[(p, s)]}")
    lines.append(f"  total double-labelled: {sum(pair.values())}")
    unordered = Counter()
    for (p, s), v in pair.items():
        unordered[tuple(sorted((p, s)))] += v
    lines.append("  overlap per pair (either direction): " + ", ".join(f"{'/'.join(k)}={v}" for k, v in sorted(unordered.items())))
    cal = [i for i, r in by_item.items() if "calibration" in r]
    lines.append(f"calibration items (all three label): {len(cal)}")
    # stratum coverage of the double-labelled set
    sizes = stratum_sizes(items)
    item_by_id = {it["item"]: it for it in items}
    dbl = Counter()
    for i, roles in by_item.items():
        if "second" in roles:
            for s in set(item_by_id[i].get("strata") or []):
                dbl[s] += 1
    short = [(s, n, dbl[s]) for s, n in sizes.items() if n >= MIN_PER_STRATUM and dbl[s] < MIN_PER_STRATUM]
    lines.append(
        f"strata with >= {MIN_PER_STRATUM} items: {sum(1 for n in sizes.values() if n >= MIN_PER_STRATUM)}; "
        f"with < {MIN_PER_STRATUM} double-labelled: {len(short)}"
    )
    for s, n, d in sorted(short):
        lines.append(f"  short: {s}: {d} double-labelled of {n} (calibration items removed from the pool)")
    return lines
