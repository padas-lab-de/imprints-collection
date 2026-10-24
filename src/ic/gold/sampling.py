"""Gold-sample design for E12: random core + priority-stratified coverage oversample.

Two-phase design:
  phase 1  simple random sample S of n_screen hosts from the frame (N hosts);
           every host in S is screened with the E8 detectors;
  phase 2  (a) random core: the first n_core hosts of a seeded permutation of S
           (an SRS of the frame on its own);
           (b) coverage oversample: every screened host gets a *priority
           stratum* (the rarest coverage stratum it belongs to; negatives and
           hosts in no coverage stratum get their own non-oversampled
           strata). Rarest stratum first, extra hosts are drawn at random from
           the not-yet-selected hosts of that priority stratum until the
           stratum's marginal count in the sample (core + all extras so far,
           counting every membership) reaches its target.

Within priority stratum h, the selected hosts are a uniform random subset of
size m_h of the M_h screened hosts (core hosts are a random subset, extras a
random subset of the rest), so the phase-2 inclusion probability is m_h / M_h
(conditional on the realized stratum sizes) and the overall one is
pi = (n_screen / N) * m_h / M_h; design weight 1 / pi (Horvitz-Thompson).
"""

from __future__ import annotations

import math
import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

RARE_TOPICS = ("Event", "Dining and Drinking", "Landmarks and Outdoors", "Nightlife Spot")
OPERATOR_TYPES = ("corporate", "sole_trader", "association", "public_body", "private_person")
TECH_FAMILIES = {
    "cms_wordpress": "tech:wordpress",
    "custom_php": "tech:custom_php",
    "site_builder": "tech:site_builder",
    "spa_framework": "tech:spa",
    "shop_system": "tech:shop",
    "static_html": "tech:static_html",
    "cms_other": "tech:cms_other",
    "custom_other": "tech:custom_other",
}
NEG_DEAD = "neg:site_not_live"
NEG_NO_IMPRINT = "neg:no_imprint"
NO_COVERAGE = "other:no_coverage_stratum"
IMAGE_ONLY = "modality:image_only"


# ---------------------------------------------------------------------------
# Confidence intervals
# ---------------------------------------------------------------------------


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for k successes in n trials."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def newcombe_diff(k1: int, n1: int, k2: int, n2: int, z: float = 1.96) -> Tuple[float, float, float]:
    """Difference p1 - p2 with Newcombe's hybrid score interval (method 10)."""
    p1, p2 = (k1 / n1 if n1 else 0.0), (k2 / n2 if n2 else 0.0)
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, lo, hi


# ---------------------------------------------------------------------------
# Strata
# ---------------------------------------------------------------------------


def is_live(rec: dict) -> bool:
    return rec.get("site_status") == "live"


def has_imprint(rec: dict) -> bool:
    """Live, and the detectors reached an imprint (any location but none)."""
    return is_live(rec) and rec.get("imprint_location") not in (None, "none")


def has_text_address(rec: dict) -> bool:
    return bool(rec.get("n_addresses")) or bool(rec.get("model_n_addresses"))


def memberships(rec: dict, image_only_confirmed: Iterable[str] = ()) -> List[str]:
    """Coverage strata a screened host belongs to. Only hosts with a reached
    imprint are members of coverage strata (the oversample adds no negatives);
    negatives get one of the two negative strata. Hand-confirmed image-only
    hosts are coverage members even if the detectors found no imprint."""
    img = set(image_only_confirmed)
    if not is_live(rec):
        return [NEG_DEAD]
    # A hand-confirmed image-only imprint counts as an imprint even when the
    # text detectors did not recognise the page (no address text to match).
    if not has_imprint(rec) and rec["host"] not in img:
        return [NEG_NO_IMPRINT]
    out = []
    age = rec.get("age_bin")
    if age in ("<2010", "2010-2017", "2018-2022", ">=2023"):
        out.append("age:" + age)
    fam = TECH_FAMILIES.get(rec.get("tech_family"))
    if rec.get("tech") == "blogger":
        out.append("tech:blogger")
    elif fam:
        out.append(fam)
    if rec.get("spa_framework") and "tech:spa" not in out:
        out.append("tech:spa")
    if rec.get("server_lang") == "php" and "tech:custom_php" not in out:
        out.append("tech:php_any")
    if rec.get("rendering_need") == "js_required":
        out.append("render:js_required")
    if rec.get("model_operator_type") in OPERATOR_TYPES:
        out.append("op:" + rec["model_operator_type"])
    if rec.get("tld") in ("at", "ch"):
        out.append("tld:" + rec["tld"])
    if rec.get("imprint_location") == "other_domain":
        out.append("loc:other_domain")
    if rec["host"] in img:
        out.append(IMAGE_ONLY)
    elif not has_text_address(rec):
        out.append("hard:imprint_without_address")
    if rec.get("po_box"):
        out.append("hard:po_box")
    if rec.get("multi_address") or (rec.get("model_n_addresses") or 0) >= 2:
        out.append("hard:multi_address")
    if rec.get("obfuscation"):
        out.append("hard:obfuscation")
    if rec.get("model_topic") in RARE_TOPICS:
        out.append("topic:" + rec["model_topic"])
    return out


def rarity_order(member_lists: Sequence[List[str]]) -> List[str]:
    """Coverage strata from rarest to most common (ties by name); the
    image-only edge case always comes first; negative strata are excluded."""
    counts: Dict[str, int] = {}
    for ms in member_lists:
        for m in ms:
            if not m.startswith("neg:"):
                counts[m] = counts.get(m, 0) + 1
    order = sorted(counts, key=lambda s: (s != IMAGE_ONLY, counts[s], s))
    return order


def priority_stratum(ms: List[str], order: List[str]) -> str:
    if len(ms) == 1 and ms[0].startswith("neg:"):
        return ms[0]
    rank = {s: i for i, s in enumerate(order)}
    cands = [m for m in ms if m in rank]
    return min(cands, key=lambda m: rank[m]) if cands else NO_COVERAGE


# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------


def _fill(selected: set, members: Dict[str, List[str]], prio: Dict[str, str], order: List[str],
          targets: Dict[str, int], rng: random.Random, budget: Optional[int], perm: List[str]) -> int:
    """Greedy rarest-first top-up; returns number of hosts added."""
    added = 0
    for s in order:
        need = targets.get(s, 0) - sum(1 for h in selected if s in members[h])
        if need <= 0:
            continue
        pool = [h for h in perm if prio[h] == s and h not in selected]
        take = min(need, len(pool))
        if budget is not None:
            take = min(take, budget - added)
        if take <= 0:
            continue
        for h in rng.sample(pool, take):
            selected.add(h)
        added += take
        if budget is not None and added >= budget:
            break
    return added


def draw_sample(
    records: List[dict],
    core_range: Tuple[int, int],
    n_total: int,
    frame_size: int,
    seed: int,
    target_range: Tuple[int, int] = (20, 30),
    caps: Optional[Dict[str, int]] = None,
    image_only_confirmed: Iterable[str] = (),
) -> Tuple[List[dict], dict]:
    """Draw the gold sample from screened records.

    Core: first n_core hosts of a seeded permutation. Rule for n_core and the
    common target T per coverage stratum: the largest T in target_range for
    which some n_core in core_range gives core + greedy top-up <= n_total;
    for that T the largest such n_core. Leftover budget goes to further passes
    at T + 1, T + 2, ... (rarest strata first) until n_total is reached or the
    pools are empty. caps override T per stratum (e.g. image-only <= 20).
    Returns (items, info)."""
    caps = caps or {}
    img = set(image_only_confirmed)
    hosts = [r["host"] for r in records]
    members = {r["host"]: memberships(r, img) for r in records}
    order = rarity_order(list(members.values()))
    prio = {h: priority_stratum(members[h], order) for h in hosts}
    rng = random.Random(seed)
    perm = list(hosts)
    rng.shuffle(perm)

    def targets_for(t):
        return {s: min(t, caps.get(s, t)) for s in order}

    def total(n0, t):
        sel = set(perm[:n0])
        return n0 + _fill(sel, members, prio, order, targets_for(t), random.Random(seed + 1), None, perm)

    lo, hi = target_range
    c_lo, c_hi = core_range
    choice = None
    for t in range(hi, lo - 1, -1):
        if total(c_lo, t) > n_total:
            continue
        a, b = c_lo, c_hi  # largest n0 in [a, b] with total <= n_total (total ~ monotone in n0)
        while a < b:
            mid = (a + b + 1) // 2
            if total(mid, t) <= n_total:
                a = mid
            else:
                b = mid - 1
        choice = (t, a)
        break
    if choice is None:
        choice = (lo, c_lo)
    T, n_core = choice
    core = set(perm[:n_core])
    selected = set(core)
    rng2 = random.Random(seed + 1)
    budget = max(0, n_total - n_core)
    added = _fill(selected, members, prio, order, targets_for(T), rng2, budget, perm)
    added2, t = 0, T
    while added + added2 < budget:
        open_counts = [
            sum(1 for h in selected if s in members[h])
            for s in order
            if caps.get(s) is None and any(prio[h] == s and h not in selected for h in perm)
        ]
        if not open_counts:
            break  # every uncapped stratum's pool is used up
        t = max(t + 1, min(open_counts) + 1)
        added2 += _fill(selected, members, prio, order, targets_for(t), rng2, budget - added - added2, perm)
    M: Dict[str, int] = {}
    m: Dict[str, int] = {}
    for h in hosts:
        M[prio[h]] = M.get(prio[h], 0) + 1
        if h in selected:
            m[prio[h]] = m.get(prio[h], 0) + 1
    f1 = len(records) / frame_size
    items = []
    for h in perm:
        if h not in selected:
            continue
        p2 = m[prio[h]] / M[prio[h]]
        pi = f1 * p2
        items.append({
            "host": h,
            "core": h in core,
            "strata": members[h],
            "priority_stratum": prio[h],
            "stratum_screened": M[prio[h]],
            "stratum_selected": m[prio[h]],
            "pi_phase2": p2,
            "inclusion_probability": pi,
            "design_weight": 1 / pi,
        })
    info = {
        "n_screen": len(records), "frame_size": frame_size, "n_core": n_core, "n_total": len(items),
        "target": T, "last_pass_target": t, "extras_first_pass": added, "extras_later_passes": added2,
        "caps": caps, "order": order, "M": M, "m": m, "seed": seed,
    }
    return items, info


def marginal_counts(items: List[dict], key: str = "strata") -> Dict[str, int]:
    out: Dict[str, int] = {}
    for it in items:
        for s in it[key]:
            out[s] = out.get(s, 0) + 1
    return out
