"""Decision rule (section 7), OOF depth cut-off (2.3) and ens2 from stored predictions."""

import numpy as np
import pytest

from ic.eval._legacy import get_tree
from ic.eval.decision import decide, filter_candidates, pareto, resolve_shifts
from ic.eval.depth import choose_depth, cross_fit
from ic.eval.ensemble import ens2
from ic.eval.estimators import Design, Est
from ic.eval.io import PredSet

BATH, PAINT, HIS, HW = (
    "bathroom-contractor",
    "painter",
    "home-improvement-service",
    "hardware-store-and-building-supplies",
)


def C(name, Q, cost, fail=0.0, p1=0.9, se=0.01):
    return {"name": name, "Q": Q, "Q_se": se, "C": cost, "fail": fail, "p1": p1}


def test_filter_and_pareto():
    cands = [
        C("a", 0.80, 10),
        C("b", 0.78, 5),
        C("c", 0.70, 6),
        C("d", 0.90, 1, fail=0.05),
        C("e", 0.9, 1, p1=0.6),
    ]
    keep, dropped = filter_candidates(cands)
    assert [c["name"] for c in keep] == ["a", "b", "c"]
    assert set(dropped) == {"d", "e"}
    assert pareto(keep) == ["a", "b"]  # c is dominated by b
    assert pareto([C("x", 0.8, None), C("y", 0.7, 3)]) == [
        "x",
        "y",
    ]  # no cost = infinitely costly


def test_decide_margin_and_paired_ci():
    cands = [C("a", 0.80, 10), C("b", 0.785, 5), C("c", 0.75, 1)]

    def paired(x, b, lo=None):
        q = {c["name"]: c["Q"] for c in cands}
        d = q[x] - q[b]
        return Est(d, se=0.002, lo=d - 0.004, hi=d + 0.004)

    out = decide(cands, paired)
    assert out["best"] == "a" and out["front"] == ["a", "b", "c"]
    assert out["eligible"] == ["a", "b"]  # c is 0.05 below
    assert out["choice"] == "b"  # cheapest within 0.02
    # the paired CI lower bound must also be within the margin
    wide = lambda x, b: Est(-0.015, lo=-0.04, hi=0.01)  # noqa: E731
    assert decide(cands, wide)["choice"] == "a"
    # margin "se" = standard error of Q(B)
    out = decide(cands, paired, margin="se")
    assert out["margin"] == 0.01 and out["choice"] == "a"
    assert decide([C("x", 0.9, 1, fail=0.5)], paired)["choice"] is None


def test_shift_tie_rules():
    cands = {c["name"]: c for c in (C("a", 0.8, 10), C("b", 0.79, 5))}
    main = {"choice": "a"}
    var = {"core_unweighted": {"choice": "b"}, "label_first": {"choice": "a"}}
    r = resolve_shifts(main, var, cands, "report")
    assert (
        r["choice"] == "a"
        and r["shifts"] == {"core_unweighted": "b"}
        and r["needs_lead"]
    )
    assert resolve_shifts(main, var, cands, "cheaper")["choice"] == "b"
    assert resolve_shifts(main, var, cands, "better")["choice"] == "a"
    assert resolve_shifts(main, {"x": {"choice": "a"}}, cands)["needs_lead"] is False


def _depth_vectors(n, p_by_level):
    rng = np.random.default_rng(0)
    v = {}
    for L, p in p_by_level.items():
        v[f"cov@{L}"] = np.ones(n)
        v[f"hit@{L}"] = (rng.random(n) < p).astype(float)
        v[f"nref@{L}"] = np.ones(n)
    return v


def test_choose_depth_point_ci_contiguous():
    d = Design(np.ones(200))
    v = _depth_vectors(200, {1: 0.95, 2: 0.6, 3: 0.95})
    assert choose_depth(d, v, 3) == 1
    assert choose_depth(d, v, 3, contiguous=False) == 3
    v = _depth_vectors(200, {1: 0.95, 2: 0.81, 3: 0.2})
    p2 = d.ratio(v["hit@2"], v["cov@2"])
    assert choose_depth(d, v, 3) == (2 if p2 >= 0.8 else 1)
    assert choose_depth(d, v, 3, criterion="ci") == 1  # CI lower bound below 0.8
    assert choose_depth(d, v, 3, min_precision=0.99) == 0


def test_cross_fit_is_out_of_fold():
    tree = get_tree("poi3")
    n = 50
    folds = np.arange(n) % 5
    # fold 0 is perfect at level 2, all other folds are bad at level 2
    rp = [tree.canonical_path(BATH)] * n
    pp = [
        (
            tree.canonical_path(BATH)
            if f == 0
            else [tree.canonical_path(BATH)[0], "x", "y"]
        )
        for f in folds
    ]
    v = {"scored": np.ones(n), "rpath": rp, "ppath": pp}
    for L in (1, 2, 3):
        v[f"nref@{L}"] = np.ones(n)
        v[f"cov@{L}"] = np.ones(n)
        v[f"hit@{L}"] = np.array([float(pp[i][:L] == rp[i][:L]) for i in range(n)])
    d = Design(np.ones(n), fold=folds)
    out = cross_fit(d, v, 3)
    assert out["cut_full"] == 1
    assert all(c == 1 for c in out["cuts"].values())
    o = out["v"]
    assert o["hit@2"].sum() == 0 and o["cov@2"].sum() == 0  # level 2 never published
    assert o["pub"].sum() == n and o["levels"].sum() == n  # one correct level per host
    assert (o["pubdepth"] == 1).all()


def _ps(name, rows):
    return PredSet(
        name,
        "topic",
        "poi",
        name,
        "v",
        {r["host"]: r for r in rows},
        "",
        {"gpu_hours_per_mhost": 1.0},
    )


def test_ens2_longest_common_prefix_and_failures():
    tree = get_tree("poi3")
    u = {"calls": 1, "prompt_tokens": 100, "completion_tokens": 10}
    a = _ps(
        "A",
        [
            {"host": "x.de", "main": BATH, "usage": u},
            {"host": "y.de", "main": BATH, "usage": u},
            {"host": "z.de", "main": None, "error": "timeout", "usage": u},
            {"host": "w.de", "main": None, "error": "no_input"},
        ],
    )
    b = _ps(
        "B",
        [
            {"host": "x.de", "main": PAINT, "usage": u},
            {"host": "y.de", "main": HW, "usage": u},
            {"host": "z.de", "main": BATH, "usage": u},
            {"host": "w.de", "main": None, "error": "no_input"},
        ],
    )
    e = ens2(a, b, tree)
    assert e.rows["x.de"]["main"] == HIS  # lcp of the two paths
    assert (
        e.rows["y.de"]["main"] is None and e.rows["y.de"]["error"] is None
    )  # disagree at L1 -> abstain
    assert e.rows["z.de"]["error"] == "member_failed"
    assert e.rows["w.de"]["error"] == "no_input"
    assert e.rows["x.de"]["usage"]["prompt_tokens"] == 200
    assert e.meta["gpu_hours_per_mhost"] == 2.0 and e.meta["ens2"]
    e2 = ens2(a, b, tree, member_fail="abstain")  # E49: a failed member votes None
    assert e2.rows["z.de"]["main"] is None and e2.rows["z.de"]["error"] is None
    with pytest.raises(AssertionError):
        ens2(a, PredSet("C", "address", "address", "c", "v", {}, "", {}), tree)
