"""Decision rule (protocol section 7), per task: filter, Pareto front, margin rule, shifts.

1. Filter: drop candidates with failed-reply rate > ``max_fail`` (open item 16, default 0.02) or
   P at the first level < ``p_floor`` (default 0.7; addresses: precision of the predicted main address,
   ``addr_P``).
2. Pareto front on quality Q (higher is better) vs cost C (lower is better). A candidate is dominated if
   another has Q >= and C <= with one strict. A candidate without a cost counts as infinitely costly.
3. B = best Q. Choose the cheapest front candidate with Q >= Q(B) - m whose paired CI lower bound of
   Q - Q(B) is >= -m; equal cost: higher Q.
4. m (open item 17): a number (default 0.02) or "se" = the standard error of Q(B).
7. Shifts: the choice is repeated under variants (core-only unweighted, first / second label, ...).
   ``tie_rule`` (open item 19): "report" (default: keep the main choice, list the shifts), "cheaper"
   (take the cheapest of the differing choices), "better" (take the highest-Q of them).
"""

from __future__ import annotations

import math


def _cost(c: dict) -> float:
    v = c.get("C")
    return math.inf if v is None else v


def filter_candidates(
    cands: list[dict], max_fail: float = 0.02, p_floor: float = 0.7
) -> tuple[list, dict]:
    keep, dropped = [], {}
    for c in cands:
        why = []
        if c.get("fail") is not None and c["fail"] > max_fail:
            why.append(f"failed rate {c['fail']:.3f} > {max_fail}")
        if c.get("p1") is not None and c["p1"] < p_floor:
            why.append(f"P first level {c['p1']:.3f} < {p_floor}")
        if c.get("Q") is None:
            why.append("no Q")
        if why:
            dropped[c["name"]] = why
        else:
            keep.append(c)
    return keep, dropped


def pareto(cands: list[dict]) -> list[str]:
    front = []
    for c in cands:
        dom = False
        for d in cands:
            if d is c:
                continue
            if (
                d["Q"] >= c["Q"]
                and _cost(d) <= _cost(c)
                and (d["Q"] > c["Q"] or _cost(d) < _cost(c))
            ):
                dom = True
                break
        if not dom:
            front.append(c["name"])
    return front


def decide(
    cands: list[dict], paired, margin=0.02, max_fail: float = 0.02, p_floor: float = 0.7
) -> dict:
    """cands: [{name, Q, Q_se, C, fail, p1}]; paired(name_x, name_b) -> Est of Q(x) - Q(b)."""
    keep, dropped = filter_candidates(cands, max_fail, p_floor)
    out = {
        "filtered_out": dropped,
        "front": [],
        "best": None,
        "margin": None,
        "eligible": [],
        "choice": None,
        "checks": {},
    }
    if not keep:
        return out
    front = pareto(keep)
    best = max(keep, key=lambda c: (c["Q"], -_cost(c)))
    m = (best.get("Q_se") or 0.0) if margin == "se" else float(margin)
    out.update(front=front, best=best["name"], margin=m)
    elig = []
    for c in keep:
        if c["name"] not in front:
            continue
        if c["name"] == best["name"]:
            out["checks"][c["name"]] = {"dQ": 0.0, "lo": 0.0, "ok": True}
            elig.append(c)
            continue
        d = paired(c["name"], best["name"])
        lo = d.lo if d is not None else None
        ok = c["Q"] >= best["Q"] - m and lo is not None and lo >= -m
        out["checks"][c["name"]] = {
            "dQ": c["Q"] - best["Q"],
            "lo": lo,
            "hi": None if d is None else d.hi,
            "ok": ok,
        }
        if ok:
            elig.append(c)
    choice = min(elig, key=lambda c: (_cost(c), -c["Q"]))
    out.update(eligible=[c["name"] for c in elig], choice=choice["name"])
    return out


def resolve_shifts(
    main: dict,
    variants: dict[str, dict],
    cands: dict[str, dict],
    tie_rule: str = "report",
) -> dict:
    """variants: label -> decide() output. Returns {choice, shifts, rule}."""
    shifts = {
        k: v.get("choice")
        for k, v in variants.items()
        if v.get("choice") != main.get("choice")
    }
    choice = main.get("choice")
    if shifts and tie_rule in ("cheaper", "better"):
        opts = [choice] + [c for c in shifts.values() if c is not None]
        opts = [o for o in opts if o in cands]
        if tie_rule == "cheaper":
            choice = min(opts, key=lambda o: (_cost(cands[o]), -cands[o]["Q"]))
        else:
            choice = max(opts, key=lambda o: (cands[o]["Q"], -_cost(cands[o])))
    return {
        "choice": choice,
        "main_choice": main.get("choice"),
        "shifts": shifts,
        "tie_rule": tie_rule,
        "needs_lead": bool(shifts),
    }
