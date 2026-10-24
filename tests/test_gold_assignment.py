"""Assignment invariants on a synthetic sample shaped like datasets/E12/gold_sample.jsonl."""

import random
from collections import Counter, defaultdict

import pytest

from ic.gold.assignment import LABELLERS, MIN_PER_STRATUM, build_assignment, stratum_sizes


def synthetic_sample(n=1000, seed=1):
    rng = random.Random(seed)
    prios = (
        [("neg:no_imprint", 219), ("neg:site_not_live", 201)]
        + [(f"p{i}", c) for i, c in enumerate([37, 37, 36, 35, 34, 31, 29, 28, 28, 27, 20, 15, 12, 8, 7, 3, 80, 100, 120, 150])]
    )
    marg = [f"m{i}" for i in range(6)]
    items, k = [], 0
    for prio, c in prios:
        for _ in range(c):
            if k >= n:
                break
            strata = {prio} | set(rng.sample(marg, 2)) if not prio.startswith("neg:") else {prio}
            items.append({"item": k, "host": f"h{k}.de", "strata": sorted(strata), "priority_stratum": prio})
            k += 1
    while k < n:
        items.append({"item": k, "host": f"h{k}.de", "strata": ["m0"], "priority_stratum": "p0"})
        k += 1
    return items


@pytest.fixture(scope="module")
def built():
    items = synthetic_sample()
    rows, info = build_assignment(items, seed=7)
    return items, rows, info


def by_item(rows):
    d = defaultdict(list)
    for r in rows:
        d[r["item"]].append(r)
    return d


def test_loads_are_2_1_1(built):
    _, rows, _ = built
    tot = Counter(r["labeller"] for r in rows)
    assert tot == {"L1": 650, "L2": 325, "L3": 325}
    assert len(rows) == 1300
    noncal = Counter(r["labeller"] for r in rows if r["role"] != "calibration")
    assert noncal == {"L1": 600, "L2": 275, "L3": 275}


def test_exactly_one_primary_and_calibration_by_all(built):
    items, rows, _ = built
    grp = by_item(rows)
    assert set(grp) == {it["item"] for it in items}
    n_cal = n_dbl = 0
    for item, rs in grp.items():
        roles = Counter(r["role"] for r in rs)
        if roles["calibration"]:
            n_cal += 1
            assert roles == {"calibration": 3}
            assert {r["labeller"] for r in rs} == set(LABELLERS)
        else:
            assert roles["primary"] == 1
            assert roles["second"] in (0, 1)
            n_dbl += roles["second"]
    assert n_cal == 50 and n_dbl == 200


def test_second_differs_from_primary_and_pairs_spread(built):
    _, rows, _ = built
    pair = Counter()
    for rs in by_item(rows).values():
        p = [r["labeller"] for r in rs if r["role"] == "primary"]
        s = [r["labeller"] for r in rs if r["role"] == "second"]
        if s:
            assert p[0] != s[0]
            pair[(p[0], s[0])] += 1
    assert len(pair) == 6 and all(v >= 20 for v in pair.values())
    assert sum(pair.values()) == 200


def test_no_labeller_gets_an_item_twice(built):
    _, rows, _ = built
    assert len({(r["item"], r["labeller"]) for r in rows}) == len(rows)


def test_stratum_coverage_of_doubles(built):
    items, rows, _ = built
    sizes = stratum_sizes(items)
    item_by_id = {it["item"]: it for it in items}
    dbl = Counter()
    for item, rs in by_item(rows).items():
        if any(r["role"] == "second" for r in rs):
            for s in set(item_by_id[item]["strata"]):
                dbl[s] += 1
    big = [s for s, n in sizes.items() if n >= MIN_PER_STRATUM]
    assert big
    assert all(dbl[s] >= MIN_PER_STRATUM for s in big), {s: dbl[s] for s in big if dbl[s] < MIN_PER_STRATUM}


def test_order_is_a_shuffled_permutation_calibration_first(built):
    items, rows, _ = built
    prio = {it["item"]: it["priority_stratum"] for it in items}
    for lab in LABELLERS:
        mine = sorted((r for r in rows if r["labeller"] == lab), key=lambda r: r["order"])
        assert [r["order"] for r in mine] == list(range(1, len(mine) + 1))
        roles = [r["role"] for r in mine]
        assert roles[:50] == ["calibration"] * 50 and "calibration" not in roles[50:]
        # not grouped by stratum: strata change nearly every step in the main block
        seq = [prio[r["item"]] for r in mine[50:]]
        changes = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
        assert changes > 0.8 * len(seq)


def test_no_stratum_info_in_rows(built):
    _, rows, _ = built
    assert set(rows[0]) == {"item", "host", "labeller", "role", "order"}


def test_deterministic():
    items = synthetic_sample()
    a, _ = build_assignment(items, seed=7)
    b, _ = build_assignment(items, seed=7)
    c, _ = build_assignment(items, seed=8)
    assert a == b and a != c
