"""Weighted estimators for the two-phase gold sample (protocol section 6, gold design 4.6).

Every population figure is a Hajek ratio theta = sum(w y) / sum(w z). Items outside a domain have
y = z = 0 but stay in their strata, so domain estimates keep the full design (no subsetting).

CIs, phase 2 only (the phase-1 screen and the M_h are treated as fixed, as the protocol says):
- "taylor": linearisation u_i = (y_i - R z_i) / Z, stratified with fpc 1 - m_h / M_h.
- "bootstrap": Rao-Wu rescaling bootstrap within strata (n_h - 1 draws, fpc in the scale factor),
  5,000 replicates, seed 1, 95% percentile interval. The replicate weights are built once per design
  and shared by all models, so paired differences use the same draws.

``fpc``: "phase2" (protocol default: fpc 1 - m_h / M_h, phase 1 fixed, so the CI is conditional on the
screened 20,000) or "none" (with-replacement formula, no fpc, census strata collapsed like the others).
Without the fpc the variance also covers most of the phase-1 component (for a census stratum the
with-replacement term equals the phase-1 term); see ``ic.eval.simulate`` for the coverage of both.

Variance strata: phase-2 strata. A stratum with one sampled item and M_h > m_h is collapsed with
neighbouring singletons of the same schema (stratum name prefix before ":"). A census stratum
(m_h = M_h) has no phase-2 variance and is left alone unless ``collapse_census`` is set.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

Z95 = 1.959963984540054


@dataclass
class Est:
    est: float | None
    se: float | None = None
    lo: float | None = None
    hi: float | None = None
    n: int = 0  # items in the domain (z > 0)
    n_eff: float | None = None  # Kish effective n in the domain
    wsum: float = 0.0  # sum of w z
    method: str = ""
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        r = lambda v: (
            None
            if v is None or (isinstance(v, float) and math.isnan(v))
            else round(float(v), 6)
        )  # noqa
        return {
            "est": r(self.est),
            "se": r(self.se),
            "lo": r(self.lo),
            "hi": r(self.hi),
            "n": self.n,
            "n_eff": None if self.n_eff is None else round(self.n_eff, 1),
            "method": self.method,
            **self.extra,
        }


def wilson(k: float, n: float, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval (unweighted core check, per-stratum tables)."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / den
    return max(0.0, c - h), min(1.0, c + h)


def kish_n(w: np.ndarray) -> float:
    s, s2 = float(w.sum()), float((w * w).sum())
    return s * s / s2 if s2 > 0 else 0.0


def collapse_strata(
    strata: list[str],
    M: list[float | None],
    m: list[int],
    collapse_census: bool = False,
) -> list[str]:
    """Variance strata: singleton strata (m_h = 1) are collapsed with neighbours of the same schema.

    Rule: per schema prefix, the singleton strata are sorted by name and paired in that order; an odd
    one joins the last pair. A schema with a single singleton joins it to the nearest non-singleton
    stratum of that schema by name; if there is none, all such leftovers form one "collapsed:misc" group
    (or join the largest stratum if alone).
    """
    info = {}
    for s, Mh, mh in zip(strata, M, m):
        info[s] = (Mh, mh)
    census = {s for s, (Mh, mh) in info.items() if Mh is not None and mh >= Mh}
    single = sorted(
        s
        for s, (Mh, mh) in info.items()
        if mh <= 1 and (collapse_census or s not in census)
    )
    by_schema = defaultdict(list)
    for s in single:
        by_schema[s.split(":", 1)[0]].append(s)
    others = defaultdict(list)
    for s, (Mh, mh) in info.items():
        if mh > 1:
            others[s.split(":", 1)[0]].append(s)
    mapping = {s: s for s in info}
    leftovers = []
    for sch, ss in by_schema.items():
        if len(ss) >= 2:
            groups = [ss[i : i + 2] for i in range(0, len(ss) - len(ss) % 2, 2)]
            if len(ss) % 2:
                groups[-1].append(ss[-1])
            for g in groups:
                for s in g:
                    mapping[s] = "collapsed:" + "|".join(g)
        else:
            s = ss[0]
            cands = sorted(others.get(sch, []))
            if cands:
                pos = sorted(cands + [s]).index(s)
                mapping[s] = cands[min(pos, len(cands) - 1)]
            else:
                leftovers.append(s)
    if len(leftovers) >= 2:
        for s in leftovers:
            mapping[s] = "collapsed:misc"
    elif leftovers:
        big = max(
            (s for s in info if info[s][1] > 1), key=lambda s: info[s][1], default=None
        )
        if big is not None:
            mapping[leftovers[0]] = big
    return [mapping[s] for s in strata]


class Design:
    """Weights and variance strata of the sample (one entry per item, fixed order)."""

    def __init__(
        self,
        weights,
        strata=None,
        M=None,
        m=None,
        core=None,
        fold=None,
        collapse_census: bool = False,
        B: int = 5000,
        seed: int = 1,
        fpc: str = "phase2",
    ):
        self.w = np.asarray(weights, dtype=float)
        n = len(self.w)
        self.n = n
        strata = list(strata) if strata is not None else ["all"] * n
        if m is None:
            cnt = defaultdict(int)
            for s in strata:
                cnt[s] += 1
            m = [cnt[s] for s in strata]
        M = list(M) if M is not None else [None] * n
        self.strata = strata
        if fpc not in ("phase2", "none"):
            raise ValueError(f"unknown fpc {fpc!r}")
        self.fpc_mode = fpc
        self.vstrata = collapse_strata(
            strata, M, list(m), collapse_census or fpc == "none"
        )
        # fpc per variance stratum: 1 - sum m_h / sum M_h over the original strata in the group
        grp_m, grp_M, seen = defaultdict(float), defaultdict(float), set()
        unknown = set()
        for s, v, Mh, mh in zip(strata, self.vstrata, M, m):
            if s in seen:
                continue
            seen.add(s)
            grp_m[v] += mh
            if Mh is None:
                unknown.add(v)
            else:
                grp_M[v] += Mh
        self.fpc = {
            v: (
                1.0
                if fpc == "none" or v in unknown or grp_M[v] <= 0
                else max(0.0, 1 - grp_m[v] / grp_M[v])
            )
            for v in grp_m
        }
        codes = {v: i for i, v in enumerate(sorted(set(self.vstrata)))}
        self.vcode = np.array([codes[v] for v in self.vstrata])
        order = np.argsort(self.vcode, kind="stable")
        self._groups = np.split(
            order, np.cumsum(np.bincount(self.vcode, minlength=len(codes)))[:-1]
        )
        self._gfpc = [self.fpc[v] for v in sorted(codes)]
        self.core = (
            np.asarray(core, dtype=bool)
            if core is not None
            else np.zeros(n, dtype=bool)
        )
        self.fold = np.asarray(fold) if fold is not None else None
        self.B, self.seed = B, seed
        self._W = None

    # -- point estimates ------------------------------------------------------------------------
    def ratio(self, y, z, w=None) -> float | None:
        w = self.w if w is None else w
        den = float(np.dot(w, z))
        return float(np.dot(w, y)) / den if den > 0 else None

    # -- Taylor linearisation -------------------------------------------------------------------
    def _var_total(self, t: np.ndarray) -> float:
        """Stratified variance of sum(t) where t_i = w_i * u_i (with replacement + fpc)."""
        G = len(self._groups)
        k = np.bincount(self.vcode, minlength=G).astype(float)
        s1 = np.bincount(self.vcode, weights=t, minlength=G)
        s2 = np.bincount(self.vcode, weights=t * t, minlength=G)
        f = np.asarray(self._gfpc, float)
        ok = (k >= 2) & (f > 0)
        ss = np.maximum(s2[ok] - s1[ok] ** 2 / k[ok], 0.0)
        return float((f[ok] * k[ok] / (k[ok] - 1) * ss).sum())

    def lin(self, y, z) -> tuple[float | None, np.ndarray | None]:
        """Point estimate and linearised values u_i (so that var(R) = var(sum w u))."""
        y, z = np.asarray(y, float), np.asarray(z, float)
        Zh = float(np.dot(self.w, z))
        if Zh <= 0:
            return None, None
        R = float(np.dot(self.w, y)) / Zh
        return R, (y - R * z) / Zh

    def taylor_se(self, y, z) -> float | None:
        R, u = self.lin(y, z)
        return None if R is None else math.sqrt(self._var_total(self.w * u))

    # -- bootstrap ------------------------------------------------------------------------------
    def replicate_weights(self) -> np.ndarray:
        """B x n matrix of Rao-Wu rescaled weights (built once, shared by all metrics and models)."""
        if self._W is None:
            rng = np.random.default_rng(self.seed)
            A = np.ones((self.B, self.n))
            for idx, f in zip(self._groups, self._gfpc):
                k = len(idx)
                if k < 2 or f <= 0:
                    continue
                mp = k - 1
                lam = math.sqrt(mp * f / (k - 1))
                r = rng.multinomial(mp, np.full(k, 1.0 / k), size=self.B)
                A[:, idx] = 1 - lam + lam * (k / mp) * r
            self._W = A * self.w[None, :]
        return self._W

    def boot_ratio(self, y, z) -> np.ndarray:
        W = self.replicate_weights()
        num, den = W @ np.asarray(y, float), W @ np.asarray(z, float)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)

    # -- interface ------------------------------------------------------------------------------
    def _domain(self, z) -> tuple[int, float]:
        z = np.asarray(z, float)
        d = z > 0
        return int(d.sum()), kish_n(self.w[d] * z[d]) if d.any() else 0.0

    def estimate(self, y, z, method: str = "taylor", level: float = 0.95) -> Est:
        y, z = np.asarray(y, float), np.asarray(z, float)
        n, ne = self._domain(z)
        R = self.ratio(y, z)
        e = Est(R, n=n, n_eff=ne, wsum=float(np.dot(self.w, z)), method=method)
        if R is None:
            return e
        zq = _zq(level)
        if method == "taylor":
            e.se = self.taylor_se(y, z)
            e.lo, e.hi = R - zq * e.se, R + zq * e.se
        elif method == "bootstrap":
            b = self.boot_ratio(y, z)
            b = b[~np.isnan(b)]
            if len(b):
                e.se = float(b.std(ddof=1)) if len(b) > 1 else 0.0
                a = (1 - level) / 2
                e.lo, e.hi = float(np.quantile(b, a)), float(np.quantile(b, 1 - a))
        else:
            raise ValueError(f"unknown CI method {method!r}")
        return e

    def diff(self, y1, z1, y2, z2, method: str = "taylor", level: float = 0.95) -> Est:
        """Paired difference R1 - R2 on the same items (same linearisation or same replicate weights)."""
        R1, u1 = self.lin(y1, z1)
        R2, u2 = self.lin(y2, z2)
        n, ne = self._domain(np.maximum(np.asarray(z1, float), np.asarray(z2, float)))
        if R1 is None or R2 is None:
            return Est(None, n=n, n_eff=ne, method=method)
        d = R1 - R2
        e = Est(d, n=n, n_eff=ne, method=method)
        zq = _zq(level)
        if method == "taylor":
            e.se = math.sqrt(self._var_total(self.w * (u1 - u2)))
            e.lo, e.hi = d - zq * e.se, d + zq * e.se
            e.extra["p"] = _p_two_sided(d, e.se)
        else:
            b = self.boot_ratio(y1, z1) - self.boot_ratio(y2, z2)
            b = b[~np.isnan(b)]
            if len(b):
                e.se = float(b.std(ddof=1)) if len(b) > 1 else 0.0
                a = (1 - level) / 2
                e.lo, e.hi = float(np.quantile(b, a)), float(np.quantile(b, 1 - a))
                e.extra["p"] = min(
                    1.0, 2 * min(float((b <= 0).mean()), float((b >= 0).mean()))
                )
        return e

    def core_check(self, y, z, level: float = 0.95) -> Est:
        """Unweighted share on the random core (SRS) with a Wilson CI."""
        y, z = np.asarray(y, float), np.asarray(z, float)
        c = self.core & (z > 0)
        n = int(c.sum())
        if n == 0:
            return Est(None, n=0, method="core-wilson")
        k = float(y[c].sum())
        lo, hi = wilson(k, n, _zq(level))
        return Est(
            k / n,
            lo=lo,
            hi=hi,
            n=n,
            n_eff=float(n),
            wsum=float(n),
            method="core-wilson",
        )

    def quantile(self, x, q: float, z=None) -> float | None:
        """Weighted quantile of x over the domain z (lower weighted quantile)."""
        x = np.asarray(x, float)
        d = np.ones(self.n, bool) if z is None else np.asarray(z, float) > 0
        d &= ~np.isnan(x)
        if not d.any():
            return None
        xs, ws = x[d], self.w[d]
        o = np.argsort(xs, kind="stable")
        cw = np.cumsum(ws[o])
        return float(xs[o][min(np.searchsorted(cw, q * cw[-1]), len(xs) - 1)])


def _zq(level: float) -> float:
    if abs(level - 0.95) < 1e-12:
        return Z95
    # inverse normal by bisection (no scipy)
    lo, hi, t = 0.0, 10.0, 1 - (1 - level) / 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < t:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _p_two_sided(d: float, se: float) -> float:
    if not se:
        return 0.0 if d else 1.0
    return math.erfc(abs(d / se) / math.sqrt(2))


def holm(pvals: dict) -> dict:
    """Holm step-down adjusted p-values for a dict name -> p."""
    items = sorted(((p, k) for k, p in pvals.items() if p is not None))
    m, out, run = len(items), {}, 0.0
    for i, (p, k) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out
