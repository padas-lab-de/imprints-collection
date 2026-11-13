"""E49 reproduction through ic.eval: results/E49/poi3c/summary.md (dev and held-out, poi3, nl-both).

results/ is untracked; the test looks for it in the parents of this file (a worktree sits inside the
main checkout) and skips when it is not there.
"""

from pathlib import Path

import numpy as np
import pytest

from ic.eval import io as IO
from ic.eval._legacy import get_tree
from ic.eval.ensemble import ens2
from ic.eval.estimators import Design
from ic.eval.metrics import pred_state, topic_vectors
from ic.eval.reference import refs_from_e49


def _find_e49():
    for p in Path(__file__).resolve().parents:
        cand = p / "results" / "E49" / "poi3c" / "summary.md"
        if cand.is_file():
            return cand.parent.parent
    return None


E49 = _find_e49()
pytestmark = pytest.mark.skipif(E49 is None, reason="results/E49 not found")

DEV = {
    "qwen": dict(
        P=(0.926, 0.852, 0.899),
        acc=(0.879, 0.784, 0.698),
        cov=(0.95, 0.979, 0.814),
        nolabel=10,
        fail=2,
    ),
    "gemma": dict(
        P=(0.934, 0.855, 0.88), acc=(0.92, 0.799, 0.714), cov=(0.985, 0.995, 0.856)
    ),
    "ens2": dict(
        P=(0.961, 0.914, 0.943),
        acc=(0.859, 0.759, 0.673),
        cov=(0.894, 0.872, 0.722),
        nolabel=21,
    ),
}
HELDOUT = {
    "qwen": dict(
        P=(0.957, 0.854, 0.875),
        acc=(0.918, 0.794, 0.701),
        cov=(0.959, 0.989, 0.923),
        nolabel=4,
    ),
    "gemma": dict(
        P=(0.948, 0.867, 0.894),
        acc=(0.948, 0.814, 0.742),
        cov=(1.0, 1.0, 0.904),
        nolabel=0,
    ),
    "ens2": dict(
        P=(0.978, 0.914, 0.911),
        acc=(0.918, 0.784, 0.701),
        cov=(0.938, 0.9, 0.865),
        nolabel=6,
    ),
}


def _files(split):
    if split == "dev":
        d = E49 / "poi3b/preds/dev/poi3"
        qwen = d / "flat__qwen__both__dmax__nt-path__think__nl-both.jsonl"
        gemma = (
            E49
            / "poi3c/preds/dev/poi3/flat__gemma__both__dmax__nt-path__reason__nl-both.jsonl"
        )
        ens = E49 / "poi3c/preds/dev/poi3/ens2__qwen_gemma__nl-both.jsonl"
        return E49 / "refs/poi_v3.jsonl", [qwen, gemma, ens]
    singles = [
        f for f in sorted((E49 / "poi3b/preds/heldout/poi3").glob("*nl-both.jsonl"))
    ]
    return E49 / "heldout/refs/poi_v3.jsonl", singles + [
        E49 / "poi3c/preds/heldout/poi3/ens2__qwen_gemma__nl-both.jsonl"
    ]


def _short(name):
    return "ens2" if "ens2" in name else "qwen" if "qwen" in name else "gemma"


def _setup(split):
    refp, files = _files(split)
    if not all(Path(f).is_file() for f in [refp, *files]):
        pytest.skip("E49 prediction files missing")
    refs = refs_from_e49(refp, "poi")
    sets = {_short(p.name): p for p in IO.load_predictions(files)}
    keys = {k for k, r in refs.items() if r["poi"]["main"] is not None}
    for p in sets.values():
        keys &= {k for k, r in p.rows.items() if pred_state(r) != "no_input"}
    smp = IO.unit_sample(sorted(keys))
    return smp, refs, sets


def _numbers(smp, refs, ps):
    d = smp.design()
    v = topic_vectors(smp, refs, ps, get_tree("poi3"))
    r = lambda y, z: round(d.ratio(y, z), 3)  # noqa: E731
    return v, {
        "P": tuple(r(v[f"hit@{L}"], v[f"cov@{L}"]) for L in (1, 2, 3)),
        "acc": tuple(r(v[f"acct@{L}"], v["scored"]) for L in (1, 2, 3)),
        "cov": tuple(r(v[f"cov@{L}"], v[f"nref@{L}"]) for L in (1, 2, 3)),
        "nolabel": int(v["nolabel"].sum()),
        "fail": int(v["fail"].sum()),
    }


def test_e49_dev_summary():
    smp, refs, sets = _setup("dev")
    assert len(smp.items) == 199
    for name, exp in DEV.items():
        _, got = _numbers(smp, refs, sets[name])
        for k, val in exp.items():
            assert got[k] == pytest.approx(val, abs=0.0015), (name, k)


def test_e49_heldout_summary():
    smp, refs, sets = _setup("heldout")
    assert len(smp.items) == 97
    assert set(sets) == {"qwen", "gemma", "ens2"}
    for name, exp in HELDOUT.items():
        _, got = _numbers(smp, refs, sets[name])
        for k, val in exp.items():
            assert got[k] == pytest.approx(val, abs=0.0015), (name, k)


def test_e49_ens2_rebuilt_from_singles_and_paired_diffs():
    smp, refs, sets = _setup("dev")
    tree = get_tree("poi3")
    rebuilt = ens2(sets["qwen"], sets["gemma"], tree, member_fail="abstain")
    _, got = _numbers(smp, refs, rebuilt)
    for k in ("P", "acc", "cov"):
        assert got[k] == pytest.approx(DEV["ens2"][k], abs=0.0015), k
    d = smp.design()
    vq, _ = _numbers(smp, refs, sets["qwen"])
    vg, _ = _numbers(smp, refs, sets["gemma"])
    ve, _ = _numbers(smp, refs, rebuilt)
    dg = d.diff(vg["acct@2"], vg["scored"], vq["acct@2"], vq["scored"])
    assert dg.est == pytest.approx(0.799 - 0.784, abs=0.002)
    de = d.diff(ve["hit@2"], ve["cov@2"], vq["hit@2"], vq["cov@2"])
    assert de.est == pytest.approx(0.914 - 0.852, abs=0.002)
    assert de.lo < de.est < de.hi and np.isfinite(de.se)
