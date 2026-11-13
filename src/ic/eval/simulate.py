"""Monte Carlo check of the weighted estimators on the real two-phase design.

The design profile is the list of phase-2 strata with (M_h, m_h), read from the gold sample
(``datasets/E53/phase2/gold_sample.jsonl``) or generated (``synthetic_profile``, same shape: about 570
strata, singletons, census strata, one large stratum). Items get outcomes from stratum-specific rates:

- share:  y = correct (z = 1 for all items), e.g. acc@L;
- ratio:  P = correct / covered (domain z = covered, varies by stratum), e.g. P@L;
- diff:   paired difference P(model 2) - P(model 1), correlated outcomes, different domains.

Two modes:
- "conditional" (what the protocol's CI targets: phase 1 fixed): one phase-1 sample of n1 items is
  drawn once; each replicate redraws phase 2 only; truth = phase-1 value.
- "two-phase": each replicate redraws phase 1 (stratum counts M_h and the item outcomes) and phase 2;
  truth = super-population value. The protocol says the phase-1 part is not covered by the CI.

Weights: w = (N0 / n1) (M_h / m_h) with the realised M_h. Report per metric: bias of the point
estimate (mean error, Monte Carlo SE), CI coverage, mean SE / empirical SD.

Run the large version: ``python -m ic.eval.simulate --sample datasets/E53/phase2/gold_sample.jsonl
--reps 2000 --boot-reps 300 --B 1000``.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict

import numpy as np

from ic.eval.estimators import Design

N0 = 3_901_721


def profile_from_sample(path) -> list[tuple[str, int, int]]:
    """[(stratum, M_h, m_h)] from a gold sample file."""
    from ic.eval.io import load_sample

    smp = load_sample(path)
    prof = {}
    for it in smp.items:
        prof[it["stratum"]] = (int(it["M_h"] or it["m_h"]), int(it["m_h"]))
    return [(s, M, m) for s, (M, m) in sorted(prof.items())]


def synthetic_profile(seed: int = 0, n1: int = 20_000) -> list[tuple[str, int, int]]:
    """A profile shaped like E53 phase 2: 574 strata, 161 with m_h = 1, about 150 census strata."""
    rng = np.random.default_rng(seed)
    prof = []
    pre = ["poi2", "wz3", "poi1", "wz1", "addr", "lang"]
    for i in range(150):  # census: small strata fully sampled
        M = int(rng.integers(1, 5))
        prof.append((f"{pre[i % 6]}:c{i}", M, M))
    for i in range(110):  # singletons with M_h > 1
        M = int(rng.integers(2, 60))
        prof.append((f"{pre[i % 6]}:s{i}", M, 1))
    for i in range(313):  # oversampled strata
        M = int(rng.integers(6, 120))
        prof.append((f"{pre[i % 6]}:o{i}", M, int(min(M - 1, rng.integers(2, 6)))))
    used = sum(M for _, M, _ in prof)
    prof.append(("other:core", max(n1 - used, 1000), 600))
    return prof


def _rates(prof, rng):
    """Per-stratum outcome rates: coverage c, P of model 1, P of model 2 (shifted)."""
    k = len(prof)
    c1 = rng.beta(6, 2, k)
    c2 = rng.beta(4, 2, k)
    p1 = rng.beta(5, 1.5, k)
    p2 = np.clip(p1 + rng.normal(0.03, 0.08, k), 0.01, 0.99)
    return c1, c2, p1, p2


def _units(rng, M, c1, c2, p1, p2):
    """Outcomes of M units of one stratum (correlated correctness of the two models)."""
    u = rng.random(M)
    cov1 = rng.random(M) < c1
    cov2 = rng.random(M) < c2
    y1 = (u < p1) & cov1
    y2 = (u < p2) & cov2
    return np.c_[cov1, y1, cov2, y2].astype(float)


def _truth(X: np.ndarray) -> dict:
    cov1, y1, cov2, y2 = X.T
    return {
        "share": y1.mean(),
        "ratio": y1.sum() / cov1.sum(),
        "diff": y2.sum() / cov2.sum() - y1.sum() / cov1.sum(),
    }


def _super_truth(prof, rates) -> dict:
    c1, c2, p1, p2 = rates
    M = np.array([M for _, M, _ in prof], float)
    q = M / M.sum()
    share = float((q * c1 * p1).sum())
    r1 = share / float((q * c1).sum())
    r2 = float((q * c2 * p2).sum()) / float((q * c2).sum())
    return {"share": share, "ratio": r1, "diff": r2 - r1}


def _phase1(prof, rates, rng, n1, redraw_counts: bool):
    c1, c2, p1, p2 = rates
    if redraw_counts:
        q = np.array([M for _, M, _ in prof], float)
        counts = rng.multinomial(n1, q / q.sum())
    else:
        counts = [M for _, M, _ in prof]
    units = {}
    for h, (s, M0, m0) in enumerate(prof):
        M = int(counts[h])
        if M == 0:
            continue
        units[s] = (_units(rng, M, c1[h], c2[h], p1[h], p2[h]), m0, M0)
    return units


def _phase2(units: dict, rng, n1: int):
    """Stratified SRS without replacement in every stratum (census strata stay census)."""
    names = list(units)
    U = np.vstack([units[s][0] for s in names])
    Ms = np.array([len(units[s][0]) for s in names])
    ms = np.array(
        [
            M if units[s][1] >= units[s][2] else min(units[s][1], M)
            for s, M in zip(names, Ms)
        ]
    )
    code = np.repeat(np.arange(len(names)), Ms)
    order = np.lexsort(
        (rng.random(len(code)), code)
    )  # random order within each stratum
    start = np.repeat(np.cumsum(Ms) - Ms, Ms)
    rank = np.empty(len(code), int)
    rank[order] = np.arange(len(code)) - start
    take = rank < ms[code]
    c = code[take]
    w = (N0 / n1) * (Ms[c] / ms[c])
    return U[take], w, [names[i] for i in c], Ms[c].tolist(), ms[c].tolist()


def simulate(
    prof,
    reps: int = 200,
    method: str = "taylor",
    mode: str = "conditional",
    fpc: str = "phase2",
    B: int = 200,
    seed: int = 0,
    level: float = 0.95,
) -> dict:
    rng = np.random.default_rng(seed)
    rates = _rates(prof, rng)
    n1 = sum(M for _, M, _ in prof)
    fixed = (
        _phase1(prof, rates, rng, n1, redraw_counts=False)
        if mode == "conditional"
        else None
    )
    truth0 = (
        _truth(np.vstack([u for u, _, _ in fixed.values()]))
        if fixed
        else _super_truth(prof, rates)
    )
    err, cover, ses = defaultdict(list), Counter(), defaultdict(list)
    for r in range(reps):
        units = fixed if fixed else _phase1(prof, rates, rng, n1, redraw_counts=True)
        X, w, st, MM, mm = _phase2(units, rng, n1)
        d = Design(w, st, MM, mm, B=B, seed=int(rng.integers(1 << 30)), fpc=fpc)
        cov1, y1, cov2, y2 = X.T
        one = np.ones(len(w))
        ests = {
            "share": d.estimate(y1, one, method, level),
            "ratio": d.estimate(y1, cov1, method, level),
            "diff": d.diff(y2, cov2, y1, cov1, method, level),
        }
        for k, e in ests.items():
            t = truth0[k]
            err[k].append(e.est - t)
            ses[k].append(e.se or 0.0)
            cover[k] += int(e.lo <= t <= e.hi)
    out = {
        "mode": mode,
        "method": method,
        "fpc": fpc,
        "reps": reps,
        "B": B if method == "bootstrap" else None,
        "n_items": int(len(w)),
        "strata": len(prof),
        "metrics": {},
    }
    for k in err:
        e = np.array(err[k])
        sd = float(e.std(ddof=1))
        out["metrics"][k] = {
            "truth": round(float(truth0[k]), 4),
            "bias": round(float(e.mean()), 5),
            "bias_mc_se": round(sd / math.sqrt(reps), 5),
            "coverage": round(cover[k] / reps, 3),
            "coverage_mc_se": round(math.sqrt(0.95 * 0.05 / reps), 3),
            "mean_se": round(float(np.mean(ses[k])), 5),
            "emp_sd": round(sd, 5),
            "se_ratio": round(float(np.mean(ses[k])) / sd, 3) if sd > 0 else None,
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--sample",
        default=None,
        help="gold_sample.jsonl for the real profile (else synthetic)",
    )
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--boot-reps", type=int, default=300)
    ap.add_argument("--B", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None, help="write the JSON result here")
    a = ap.parse_args(argv)
    prof = profile_from_sample(a.sample) if a.sample else synthetic_profile(a.seed)
    res = []
    for mode in ("conditional", "two-phase"):
        for fpc in ("phase2", "none"):
            res.append(simulate(prof, a.reps, "taylor", mode, fpc, seed=a.seed))
            res.append(
                simulate(prof, a.boot_reps, "bootstrap", mode, fpc, B=a.B, seed=a.seed)
            )
    for r in res:
        print(
            f"{r['mode']:12s} {r['method']:9s} fpc={r['fpc']:6s} reps={r['reps']:5d} "
            + "  ".join(
                f"{k}: bias {m['bias']:+.4f} (mc se {m['bias_mc_se']:.4f}) cov {m['coverage']:.3f} se/sd {m['se_ratio']}"
                for k, m in r["metrics"].items()
            )
        )
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump({"profile": a.sample or "synthetic", "runs": res}, f, indent=1)


if __name__ == "__main__":
    main()
