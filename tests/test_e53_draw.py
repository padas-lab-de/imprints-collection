"""E53 phase-2 draw: determinism, class quotas, weight identity, folds (synthetic screen)."""

import importlib.util
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("e53_draw", ROOT / "scripts" / "E53" / "draw.py")
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)

N0, N1 = 1_000_000, 2000
TARGET = {"a": 20, "b": 20, "r1": 5, "r2": 5, "r3": 5, "r4": 5, "r5": 5, "r6": 5}


def synth(seed=1):
    """2,000 sites: a, b common; r1..r5 rare (some below T); r6 never occurs; some sites in no class."""
    rng = random.Random(seed)
    recs = []
    for i in range(N1):
        s = []
        if rng.random() < 0.5:
            s.append("a")
        if rng.random() < 0.3:
            s.append("b")
        for j, p in enumerate([0.02, 0.01, 0.006, 0.003, 0.001], start=1):
            if rng.random() < p:
                s.append(f"r{j}")
        s.append("junk:x")  # not a target class, must be ignored
        recs.append({"host": f"h{i}.de", "strata": s})
    return recs


def run(**kw):
    return D.draw(synth(), TARGET, N0, N1, seed=42, core=100, **kw)


def test_deterministic():
    a, _ = run()
    b, _ = run()
    assert a == b
    c, _ = D.draw(synth(), TARGET, N0, N1, seed=43, core=100)
    assert [i["host"] for i in c] != [i["host"] for i in a]


def test_every_class_reaches_min_t_or_all_members():
    items, info = run()
    for c, T in TARGET.items():
        assert info["drawn"][c] >= min(T, info["S1"][c]), c
        if info["S1"][c] < T:
            assert info["drawn"][c] == info["S1"][c]  # shortfall: all members, probability 1 within the class
    assert "junk:x" not in info["drawn"]
    assert info["S1"]["r6"] == 0
    rows = D.quota_rows(TARGET, {}, info)
    assert len(rows) == len(TARGET) + 1


def test_core_and_probabilities():
    items, info = run()
    assert sum(i["core"] for i in items) == 100
    assert len({i["host"] for i in items}) == len(items)
    for it in items:
        p2 = it["m_h"] / it["M_h"]
        assert 0 < p2 <= 1
        assert abs(it["pi"] - N1 / N0 * p2) < 1e-15
        assert abs(it["weight"] * it["pi"] - 1) < 1e-12
        assert it["core"] or it["selected_for"] == [it["stratum"]]
    # m_h in the items equals the number of items of the stratum
    cnt = Counter(i["stratum"] for i in items)
    assert all(i["m_h"] == cnt[i["stratum"]] for i in items)


def test_weight_sum_identity():
    """sum w = (N0 / n1) * sum over sampled strata of M_h; equals N0 when no stratum is empty (min_stratum = 1)."""
    items, info = run()
    sampled = {i["stratum"] for i in items}
    expect = N0 / N1 * sum(M for s, M in info["M"].items() if s in sampled)
    assert abs(sum(i["weight"] for i in items) - expect) < 1e-6 * N0
    items1, info1 = run(min_stratum=1)
    assert {i["stratum"] for i in items1} == set(info1["M"])
    assert abs(sum(i["weight"] for i in items1) - N0) < 1e-6 * N0
    assert len(items1) >= len(items)


def test_folds_balanced_and_stratified():
    items, _ = run(min_stratum=2)
    sizes = Counter(i["fold"] for i in items)
    assert set(sizes) == set(range(5))
    assert max(sizes.values()) - min(sizes.values()) <= 1
    # inside every fold group, fold sizes differ by at most 1 (round-robin)
    groups = {}
    for i in items:
        groups.setdefault(i["fold_group"], Counter())[i["fold"]] += 1
    for g, c in groups.items():
        n = sum(c.values())
        if n >= 5:
            assert max(c.get(f, 0) for f in range(5)) - min(c.get(f, 0) for f in range(5)) <= 1, g
    # strata with < 5 items are pooled into rare:<schema>
    cnt = Counter(i["stratum"] for i in items)
    for i in items:
        if cnt[i["stratum"]] < 5:
            assert i["fold_group"].startswith("rare:")
        else:
            assert i["fold_group"] == i["stratum"]


def test_schema_of():
    assert D.schema_of("poi2:x") == "poi" and D.schema_of("wz3:01.4") == "wz"
    assert D.schema_of("addr:at") == "addr" and D.schema_of("lang:non_de") == "addr"
