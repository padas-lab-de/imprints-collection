"""Monte Carlo check of the weighted estimators on the real E53 design (or a synthetic one of the same shape).

Fast: conditional mode (phase 1 fixed, as the protocol's CI targets), Taylor 200 reps, bootstrap 40 reps.
Slow (`pytest -m slow`): 1000 Taylor reps in both modes and 200 bootstrap reps.
"""

from pathlib import Path

import pytest

from ic.eval.simulate import profile_from_sample, simulate, synthetic_profile


def _profile():
    for p in Path(__file__).resolve().parents:
        f = p / "datasets" / "E53" / "phase2" / "gold_sample.jsonl"
        if f.is_file():
            return profile_from_sample(f)
    return synthetic_profile(0)


PROF = _profile()


def _check(res, lo, hi):
    for k, m in res["metrics"].items():
        assert abs(m["bias"]) < 4 * m["bias_mc_se"] + 1e-9, (k, m)
        assert lo <= m["coverage"] <= hi, (k, m)


def test_profile_shape():
    assert 400 < len(PROF) < 800
    assert sum(m for _, _, m in PROF) > 1500


def test_taylor_unbiased_and_covers():
    res = simulate(PROF, reps=200, method="taylor", mode="conditional", seed=11)
    _check(res, 0.89, 0.99)
    for m in res["metrics"].values():
        assert 0.8 < m["se_ratio"] < 1.25


def test_bootstrap_covers():
    res = simulate(
        PROF, reps=40, method="bootstrap", mode="conditional", B=200, seed=12
    )
    _check(res, 0.85, 1.0)


@pytest.mark.slow
@pytest.mark.parametrize(
    "mode,fpc",
    [("conditional", "phase2"), ("two-phase", "phase2"), ("two-phase", "none")],
)
def test_taylor_large(mode, fpc):
    _check(
        simulate(PROF, reps=1000, method="taylor", mode=mode, fpc=fpc, seed=21),
        0.925,
        0.975,
    )


@pytest.mark.slow
def test_bootstrap_large():
    _check(
        simulate(
            PROF, reps=200, method="bootstrap", mode="conditional", B=500, seed=22
        ),
        0.91,
        0.99,
    )
