"""Publish depth by 5-fold cross-fitting (protocol 2.3, D58 A; D54 threshold P >= 0.8).

For each fold k, the cut-off is the deepest level with weighted P@L >= ``min_precision`` on the other
four folds; it is applied to fold k. The out-of-fold (OOF) numbers pool all folds.

Parameters:
- ``criterion`` (open item 12): "point" (default, as E49) or "ci" (the lower CI bound must reach the
  threshold).
- ``contiguous``: True (default, E49 ``deepest_reliable``): stop at the first level that fails;
  False: the deepest level that passes, even if a level above it fails.
"""

from __future__ import annotations

import numpy as np


def choose_depth(
    design,
    v: dict,
    Lmax: int,
    train=None,
    min_precision: float = 0.8,
    criterion: str = "point",
    contiguous: bool = True,
    method: str = "taylor",
) -> int:
    train = np.ones(design.n) if train is None else np.asarray(train, float)
    best = 0
    for L in range(1, Lmax + 1):
        y, z = v[f"hit@{L}"] * train, v[f"cov@{L}"] * train
        if criterion == "ci":
            e = design.estimate(y, z, method)
            val = e.lo
        else:
            val = design.ratio(y, z)
        if val is not None and val >= min_precision:
            best = L
        elif contiguous:
            break
    return best


def _lcp_len(a: list, b: list) -> int:
    k = 0
    for x, y in zip(a, b):
        if x != y:
            break
        k += 1
    return k


def cross_fit(design, v: dict, Lmax: int, folds=None, **kw) -> dict:
    """Out-of-fold cut-offs and OOF item vectors (to be estimated with the full design)."""
    n = design.n
    folds = design.fold if folds is None else np.asarray(folds)
    if folds is None:
        folds = np.arange(n) % 5
    folds = np.array([-1 if f is None else int(f) for f in folds])
    cut_full = choose_depth(design, v, Lmax, None, **kw)
    cuts = {}
    for k in sorted(set(folds.tolist()) - {-1}):
        cuts[k] = choose_depth(design, v, Lmax, (folds != k).astype(float), **kw)
    cut_i = np.array([cuts.get(f, cut_full) for f in folds], dtype=float)
    out = {"cuts": cuts, "cut_full": cut_full, "cut_i": cut_i}
    o = {}
    for L in range(1, Lmax + 1):
        on = (L <= cut_i).astype(float)
        o[f"hit@{L}"] = v[f"hit@{L}"] * on
        o[f"cov@{L}"] = v[f"cov@{L}"] * on
        o[f"nref@{L}"] = v[f"nref@{L}"]
    pub, pub_ok, levels, depth = (np.zeros(n) for _ in range(4))
    for i in range(n):
        if not v["scored"][i]:
            continue
        q = v["ppath"][i][: int(cut_i[i])]
        rp = v["rpath"][i]
        if q:
            pub[i] = 1
            d = min(len(q), len(rp))
            pub_ok[i] = q[:d] == rp[:d]
            levels[i] = _lcp_len(q, rp)
            depth[i] = len(q)
    o.update(
        {
            "pub": pub,
            "pub_ok": pub_ok,
            "levels": levels,
            "pubdepth": depth,
            "scored": v["scored"],
        }
    )
    out["v"] = o
    return out


def oof_metric_defs(Lmax: int) -> list[tuple[str, str, str]]:
    out = []
    for L in range(1, Lmax + 1):
        out += [
            (f"oof_P@{L}", f"hit@{L}", f"cov@{L}"),
            (f"oof_acc@{L}", f"hit@{L}", f"nref@{L}"),
            (f"oof_cov@{L}", f"cov@{L}", f"nref@{L}"),
        ]
    out += [
        ("oof_published", "pub", "scored"),
        ("oof_published_P", "pub_ok", "pub"),
        ("oof_correct_levels", "levels", "scored"),
        ("oof_depth", "pubdepth", "scored"),
    ]
    return out
