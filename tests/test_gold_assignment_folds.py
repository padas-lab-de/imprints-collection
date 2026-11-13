"""E53 assignment (build_assignment_folds) on a synthetic sample; no data, no network."""

import random
from collections import Counter, defaultdict

import pytest

from ic.gold.assignment import LABELLERS, PAIRS, build_assignment_folds


def sample(n=1869, n_bad=9, seed=3):
    rng = random.Random(seed)
    items = [
        {"item": k, "host": f"h{k}.de", "fold": k % 5, "core": rng.random() < 0.32, "eligible": True}
        for k in range(n)
    ]
    for it in rng.sample(items, n_bad):
        it["eligible"] = False
    return items


@pytest.fixture(scope="module")
def built():
    items = sample()
    rows, _ = build_assignment_folds(items, seed=11)
    return items, rows


def test_counts_and_loads(built):
    items, rows = built
    assert len(rows) == 2344
    tot = Counter(r["labeller"] for r in rows)
    assert tot == {"L1": 1172, "L2": 586, "L3": 586}
    roles = Counter(r["role"] for r in rows)
    assert roles == {"primary": 1819, "second": 375, "calibration": 150}


def test_calibration_and_second_rules(built):
    items, rows = built
    by = {it["item"]: it for it in items}
    g = defaultdict(list)
    for r in rows:
        g[r["item"]].append(r)
    assert set(g) == set(by)
    cal = [i for i, rs in g.items() if any(r["role"] == "calibration" for r in rs)]
    assert len(cal) == 50
    assert Counter(by[i]["fold"] for i in cal) == {f: 10 for f in range(5)}
    assert any(by[i]["core"] for i in cal) and not all(by[i]["core"] for i in cal)
    for i, rs in g.items():
        roles = sorted(r["role"] for r in rs)
        if i in cal:
            assert roles == ["calibration"] * 3 and {r["labeller"] for r in rs} == set(LABELLERS)
        elif roles == ["primary", "second"]:
            assert len({r["labeller"] for r in rs}) == 2
            assert by[i]["eligible"]
        else:
            assert roles == ["primary"]
    assert all(by[i]["eligible"] for i in cal)
    assert sum(1 for rs in g.values() if len(rs) == 2) == 375


def test_pairs_even_and_folds_proportional(built):
    items, rows = built
    by = {it["item"]: it for it in items}
    g = defaultdict(dict)
    for r in rows:
        g[r["item"]][r["role"]] = r["labeller"]
    pair = Counter()
    pair_fold = Counter()
    for i, d in g.items():
        if "second" in d:
            p = tuple(sorted((d["primary"], d["second"])))
            pair[p] += 1
            pair_fold[(by[i]["fold"], p)] += 1
    assert pair == {p: 125 for p in PAIRS}
    for (f, p), v in pair_fold.items():
        assert 23 <= v <= 27, (f, p, v)


def test_order_calibration_first_random_no_leak(built):
    items, rows = built
    by = {it["item"]: it for it in items}
    for lab in LABELLERS:
        mine = sorted((r for r in rows if r["labeller"] == lab), key=lambda r: r["order"])
        assert [r["order"] for r in mine] == list(range(1, len(mine) + 1))
        assert [r["role"] for r in mine[:50]] == ["calibration"] * 50
        assert all(r["role"] != "calibration" for r in mine[50:])
        folds = [by[r["item"]]["fold"] for r in mine[50:]]
        assert len({tuple(folds[i : i + 20]) for i in range(0, 200, 20)}) > 1  # not sorted by fold
    assert set(rows[0]) == {"item", "host", "labeller", "role", "order"}


def test_deterministic_and_seed_sensitive():
    items = sample()
    a, _ = build_assignment_folds(items, seed=5)
    b, _ = build_assignment_folds(items, seed=5)
    c, _ = build_assignment_folds(items, seed=6)
    assert a == b and a != c
