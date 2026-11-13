"""Unit tests for ic.eval.estimators (Hajek ratio, Taylor, bootstrap, collapse, Wilson, Holm)."""

import math

import numpy as np
import pytest

from ic.eval.estimators import Design, collapse_strata, holm, kish_n, wilson


def test_ratio_and_domain():
    d = Design([1, 2, 3])
    assert d.ratio([1, 0, 1], [1, 1, 1]) == pytest.approx(4 / 6)
    # domain: items outside (z = 0) do not count, but stay in the design
    assert d.ratio([1, 0, 0], [1, 1, 0]) == pytest.approx(1 / 3)
    assert d.ratio([0, 0, 0], [0, 0, 0]) is None
    assert d.estimate([0, 0, 0], [0, 0, 0]).est is None


def test_taylor_equals_srs_formula():
    y = np.array([1, 0, 1, 1, 0, 1, 1, 1, 0, 1], float)
    d = Design(np.ones(10))  # one stratum, M unknown -> no fpc
    e = d.estimate(y, np.ones(10))
    p = y.mean()
    assert e.est == pytest.approx(p)
    assert e.se == pytest.approx(math.sqrt(y.var(ddof=1) / 10))
    assert e.lo == pytest.approx(p - 1.959964 * e.se, abs=1e-6)


def test_fpc_and_census():
    y = np.array([1, 0, 1, 1, 0, 1, 1, 1, 0, 1], float)
    base = Design(np.ones(10)).estimate(y, np.ones(10)).se
    half = (
        Design(np.full(10, 2.0), ["s"] * 10, [20] * 10, [10] * 10)
        .estimate(y, np.ones(10))
        .se
    )
    assert half == pytest.approx(base * math.sqrt(0.5))
    census = Design(np.ones(10), ["s"] * 10, [10] * 10, [10] * 10)
    assert census.estimate(y, np.ones(10)).se == 0
    # fpc="none": with-replacement formula, census strata get a variance
    assert Design(np.ones(10), ["s"] * 10, [10] * 10, [10] * 10, fpc="none").estimate(
        y, np.ones(10)
    ).se == pytest.approx(base)


def test_stratified_variance_by_hand():
    # two strata, weights differ; variance = sum_h fpc_h n_h/(n_h-1) sum (t - tbar_h)^2 with t = w u
    w = np.array([1, 1, 1, 4, 4], float)
    s = ["a", "a", "a", "b", "b"]
    M = [6, 6, 6, 8, 8]
    m = [3, 3, 3, 2, 2]
    y = np.array([1, 0, 1, 1, 0], float)
    z = np.ones(5)
    d = Design(w, s, M, m)
    R = (w * y).sum() / w.sum()
    t = w * (y - R * z) / w.sum()
    v = 0.0
    for idx, f in (([0, 1, 2], 0.5), ([3, 4], 0.75)):
        x = t[idx]
        v += f * len(x) / (len(x) - 1) * ((x - x.mean()) ** 2).sum()
    assert d.estimate(y, z).se == pytest.approx(math.sqrt(v))


def test_collapse_singletons():
    strata = [
        "poi2:a",
        "poi2:b",
        "poi2:c",
        "wz3:x",
        "wz3:big",
        "addr:z",
        "lang:q",
        "poi2:cen",
    ]
    M = [5, 5, 5, 9, 50, 7, 3, 1]
    m = [1, 1, 1, 1, 10, 1, 1, 1]
    out = dict(zip(strata, collapse_strata(strata, M, m)))
    assert (
        out["poi2:a"] == out["poi2:b"] == out["poi2:c"]
    )  # odd one joins the last pair
    assert (
        out["wz3:x"] == "wz3:big"
    )  # lone singleton joins a non-singleton of its schema
    assert out["addr:z"] == out["lang:q"] == "collapsed:misc"
    assert out["poi2:cen"] == "poi2:cen"  # census singleton stays
    out2 = dict(zip(strata, collapse_strata(strata, M, m, collapse_census=True)))
    assert out2["poi2:cen"].startswith("collapsed:")


def test_singleton_strata_get_variance_after_collapse():
    w = np.array([10, 20, 1, 1], float)
    d = Design(w, ["poi2:a", "poi2:b", "x", "x"], [10, 20, 2, 2], [1, 1, 2, 2])
    assert len(set(d.vstrata)) == 2
    assert d.estimate([1, 0, 1, 0], np.ones(4)).se > 0


def test_bootstrap_close_to_taylor():
    rng = np.random.default_rng(3)
    n = 400
    strata = [f"s{i % 8}" for i in range(n)]
    w = np.array([1 + (i % 8) for i in range(n)], float)
    M = [500] * n
    m = [50] * n
    y = (rng.random(n) < 0.7).astype(float)
    z = (rng.random(n) < 0.8).astype(float)
    y *= z
    d = Design(w, strata, M, m, B=4000, seed=1)
    t = d.estimate(y, z, "taylor")
    b = d.estimate(y, z, "bootstrap")
    assert b.est == t.est
    assert b.se == pytest.approx(t.se, rel=0.1)
    assert b.lo == pytest.approx(t.lo, abs=0.01) and b.hi == pytest.approx(
        t.hi, abs=0.01
    )
    # the replicate matrix is built once and reused (paired draws)
    assert d.replicate_weights() is d.replicate_weights()


def test_paired_difference():
    rng = np.random.default_rng(0)
    n = 300
    d = Design(np.ones(n), B=2000)
    y1 = (rng.random(n) < 0.7).astype(float)
    flip = rng.random(n) < 0.1
    y2 = np.where(flip, 1 - y1, y1)
    one = np.ones(n)
    for method in ("taylor", "bootstrap"):
        same = d.diff(y1, one, y1, one, method)
        assert same.est == 0 and same.se == 0
        e = d.diff(y2, one, y1, one, method)
        assert e.est == pytest.approx(y2.mean() - y1.mean())
        # paired SE is far below the unpaired one
        unpaired = math.sqrt(d.estimate(y1, one).se ** 2 + d.estimate(y2, one).se ** 2)
        assert e.se < 0.6 * unpaired
        assert 0 <= e.extra["p"] <= 1


def test_wilson_and_core_check():
    lo, hi = wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-3) and hi == pytest.approx(
        0.9433, abs=1e-3
    )
    d = Design([1, 50, 1, 1], core=[True, False, True, True])
    c = d.core_check([1, 0, 0, 1], [1, 1, 1, 1])
    assert c.est == pytest.approx(2 / 3) and c.n == 3


def test_holm_and_kish():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03)
    assert adj["c"] == pytest.approx(0.06)
    assert adj["b"] == pytest.approx(0.06)
    assert kish_n(np.ones(10)) == pytest.approx(10)
    assert kish_n(np.array([1, 1, 1, 9.0])) < 4


def test_weighted_quantile():
    d = Design([1, 1, 1, 7])
    assert d.quantile([1, 2, 3, 4], 0.5) == 4
    assert Design(np.ones(4)).quantile([1, 2, 3, 4], 0.5) == 2
