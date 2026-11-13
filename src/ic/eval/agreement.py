"""Inter-labeller agreement (protocol 2.2, gold design 5.4), on items with two or more labels.

- site_status, imprint_present: Cohen's kappa (pairs) and raw agreement.
- main address: location match (same postcode + street, or <= 100 m once geocoded; the same measure
  as the model score) and exact agreement per field; "agreement with suggestions shown".
- topics: share of equal path prefix per level (among pairs where at least one label reaches L; both
  must reach L and agree), full-path agreement (E49 "A=B"), Krippendorff's alpha (nominal) on L1.
Calibration items (three labels) are reported separately with all three pairs.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from ic.eval._legacy import addr, get_tree
from ic.eval.io import hkey
from ic.eval.metrics import location_match
from ic.eval.reference import (
    TOPIC,
    _ordered_labels,
    _path,
    address_of,
    main_address,
    status_of,
    topic_of,
)

FIELDS = ("street", "number", "postcode", "town", "country")


def cohen_kappa(a: list, b: list) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe >= 1:
        return 1.0 if po >= 1 else None
    return (po - pe) / (1 - pe)


def krippendorff_alpha_nominal(units: list[list]) -> float | None:
    """units: one list of values per item (None = missing). Items with < 2 values are ignored."""
    coinc = Counter()
    for vals in units:
        v = [x for x in vals if x is not None]
        m = len(v)
        if m < 2:
            continue
        for i, j in ((i, j) for i in range(m) for j in range(m) if i != j):
            coinc[(v[i], v[j])] += 1 / (m - 1)
    n_c = Counter()
    for (c, _), x in coinc.items():
        n_c[c] += x
    n = sum(n_c.values())
    if n <= 1:
        return None
    do = sum(x for (c, k), x in coinc.items() if c != k)
    de = sum(n_c[c] * n_c[k] for c in n_c for k in n_c if c != k) / (n - 1)
    if de == 0:
        return 1.0 if do == 0 else None
    return 1 - do / de


def _pairs(keys, labels, assignment, calibration: bool):
    for key in keys:
        labs = _ordered_labels(hkey(key), labels, assignment)
        is_cal = len(labs) >= 3 or any(r == "calibration" for _, r, _ in labs)
        if len(labs) < 2 or is_cal != calibration:
            continue
        lbs = [lb for _, _, lb in labs]
        yield key, lbs, list(combinations(range(len(lbs)), 2))


def agreement(
    keys,
    labels: dict,
    assignment: dict | None = None,
    geocodes: dict | None = None,
    calibration: bool = False,
) -> dict:
    assignment = assignment or {}
    AS = addr()
    st_a, st_b, ip_a, ip_b = [], [], [], []
    loc = [0, 0]
    loc_both = [0, 0]
    fld = {f: [0, 0] for f in FIELDS}
    topic = {s: {"pairs": 0, "full": 0, "levels": {}, "alpha_units": []} for s in TOPIC}
    trees = {s: get_tree(s) for s in TOPIC}
    n_items = 0
    for key, lbs, prs in _pairs(keys, labels, assignment, calibration):
        n_items += 1
        for i, j in prs:
            a, b = lbs[i], lbs[j]
            sa, sb = status_of(a), status_of(b)
            st_a.append(sa[0])
            st_b.append(sb[0])
            ip_a.append(sa[1])
            ip_b.append(sb[1])
            ra, rb = address_of(a), address_of(b)
            ma, mb = main_address(ra), main_address(rb)
            loc[1] += 1
            if ma is None or mb is None:
                loc[0] += ma is None and mb is None
            else:
                ok = location_match(ma, mb, geocodes or {}, 100.0)[0]
                loc[0] += ok
                loc_both[0] += ok
                loc_both[1] += 1
                for f in FIELDS:
                    if AS.norm(f, ma.get(f, "")) or AS.norm(f, mb.get(f, "")):
                        fld[f][1] += 1
                        fld[f][0] += AS.field_eq(f, ma.get(f, ""), mb.get(f, ""))
            for s in TOPIC:
                ta, tb = topic_of(a, s), topic_of(b, s)
                if ta is None and tb is None:
                    continue
                pa, pb = _path(trees[s], (ta or {}).get("main")), _path(
                    trees[s], (tb or {}).get("main")
                )
                if not pa and not pb:
                    continue
                T = topic[s]
                T["pairs"] += 1
                T["full"] += pa == pb
                for L in range(1, trees[s].max_level + 1):
                    if len(pa) >= L or len(pb) >= L:
                        c = T["levels"].setdefault(L, [0, 0])
                        c[1] += 1
                        c[0] += len(pa) >= L and len(pb) >= L and pa[:L] == pb[:L]
        for s in TOPIC:
            l1 = []
            for lb in lbs:
                t = topic_of(lb, s)
                p = _path(trees[s], (t or {}).get("main"))
                l1.append(p[0] if p else None)
            topic[s]["alpha_units"].append(l1)
    r = lambda k, n: round(k / n, 4) if n else None  # noqa: E731
    out = {
        "items": n_items,
        "pairs": len(st_a),
        "site_status": {
            "agree": r(sum(x == y for x, y in zip(st_a, st_b)), len(st_a)),
            "kappa": _rnd(cohen_kappa(st_a, st_b)),
        },
        "imprint_present": {
            "agree": r(sum(x == y for x, y in zip(ip_a, ip_b)), len(ip_a)),
            "kappa": _rnd(cohen_kappa(ip_a, ip_b)),
        },
        "address": {
            "location_match": r(*loc),
            "n": loc[1],
            "location_match_both_address": r(*loc_both),
            "n_both_address": loc_both[1],
            "field_exact": {f: r(*fld[f]) for f in FIELDS},
            "note": "agreement with suggestions shown",
        },
        "topics": {},
    }
    for s in TOPIC:
        T = topic[s]
        out["topics"][s] = {
            "pairs": T["pairs"],
            "full_path": r(T["full"], T["pairs"]),
            "prefix": {
                L: {"agree": r(*c), "n": c[1]} for L, c in sorted(T["levels"].items())
            },
            "alpha_L1": _rnd(krippendorff_alpha_nominal(T["alpha_units"])),
        }
    return out


def _rnd(v):
    return None if v is None else round(v, 4)
