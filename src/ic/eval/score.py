"""E52 scorer: all candidates of all tasks, weighted estimates, OOF publish depth, ens2, decision.

``score(sample, refs, predsets, params, ...)`` returns one JSON-able dict; ``report.write`` turns it
into the files of protocol section 8. Every open item of the protocol that the code touches is a field
of ``Params`` with the protocol default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from itertools import combinations

import numpy as np

from ic.eval import depth as D
from ic.eval import metrics as M
from ic.eval._legacy import get_tree
from ic.eval.decision import decide, resolve_shifts
from ic.eval.ensemble import ens2, ens2_usd_per_1M
from ic.eval.estimators import Design, Est, holm, wilson

SCREEN_MODELS = ("gemma4-31b-it", "qwen38-27b", "gemma", "qwen")


@dataclass
class Params:
    # CI (open item 20)
    method: str = "taylor"  # "taylor" | "bootstrap"
    B: int = 5000
    seed: int = 1
    level: float = 0.95
    collapse_census: bool = False
    fpc: str = (
        "phase2"  # "phase2" (protocol: phase 1 fixed) | "none" (with replacement, covers phase 1)
    )
    # reference (open items 3, 4)
    adjudication_scope: str = "disagreements"  # "disagreements" | "double" | "all"
    depth_rule: str = "lcp"  # "lcp" | "deeper"
    unresolved_topic: str = "lcp"  # "lcp" | "primary" | "drop"
    unresolved_other: str = "primary"  # "primary" | "drop"
    # scoring
    no_input: str = "miss"  # "miss" | "skip" (E49)
    # publish depth (2.3, open item 12)
    min_precision: float = 0.8
    depth_criterion: str = "point"  # "point" | "ci"
    depth_contiguous: bool = True
    # decision (section 7; open items 16-19)
    q_level: dict = field(default_factory=lambda: {"poi": 2, "wz": 3})
    q_metric: str = "acc"  # "acc" (protocol 5.1) | "acc_trunc" (E49 summary "acc")
    addr_q: str = "loc100_all"  # "loc100_all" | "loc100"
    target: str = "acc"  # "acc" | "depth" (OOF correct levels per host; open item 18)
    max_fail: float = 0.02
    p_floor: float = 0.7
    margin: object = 0.02  # float or "se"
    tie_rule: str = "report"  # "report" | "cheaper" | "better"
    cost_axis: str = "auto"  # "auto" | "usd" | "gpu_hours" | "proxy"
    # ens2 (open item 10)
    ens2_pairs: object = "top2"  # "none" | "top2" | "all" | ["nameA+nameB", ...]
    ens2_member_fail: str = "fail"  # "fail" | "abstain" (E49)
    # reporting
    min_stratum_n: int = 10
    screen_models: tuple = SCREEN_MODELS

    def as_dict(self) -> dict:
        d = asdict(self)
        d["screen_models"] = list(self.screen_models)
        return d


def _slice(v: dict, idx: np.ndarray) -> dict:
    return {
        k: (a[idx] if isinstance(a, np.ndarray) else [a[i] for i in idx])
        for k, a in v.items()
    }


def _binary(y: np.ndarray) -> bool:
    return bool(np.all((y == 0) | (y == 1)))


class Scorer:
    def __init__(
        self,
        sample,
        refs: dict,
        predsets: list,
        params: Params | None = None,
        geocodes: dict | None = None,
        texts: dict | None = None,
        alt_refs: dict | None = None,
    ):
        self.p = params or Params()
        self.sample, self.refs, self.predsets = sample, refs, predsets
        self.geocodes, self.texts = geocodes or {}, texts or {}
        self.alt_refs = alt_refs or {}  # "first" / "second" -> refs
        self.design = sample.design(
            collapse_census=self.p.collapse_census,
            B=self.p.B,
            seed=self.p.seed,
            fpc=self.p.fpc,
        )
        self.core_idx = np.flatnonzero(self.design.core)
        self.core_design = Design(
            np.ones(len(self.core_idx)), B=self.p.B, seed=self.p.seed
        )
        self.double = np.array(
            [bool((refs.get(it["key"]) or {}).get("double")) for it in sample.items],
            dtype=float,
        )
        self.trees = {}

    # -- vectors --------------------------------------------------------------------------------
    def tree(self, schema):
        if schema not in self.trees:
            self.trees[schema] = get_tree(schema)
        return self.trees[schema]

    def vectors(self, ps, refs=None) -> dict:
        refs = self.refs if refs is None else refs
        if ps.task == "topic":
            return M.topic_vectors(
                self.sample, refs, ps, self.tree(ps.schema), self.p.no_input
            )
        return M.address_vectors(self.sample, refs, ps, self.geocodes, self.texts)

    def q_def(self, group: str) -> tuple[str, str, str]:
        if group == "address":
            return {
                "loc100_all": ("loc100_all", "loc100_all", "ref"),
                "loc100": ("loc100", "loc100", "ref_main"),
            }[self.p.addr_q]
        L = self.p.q_level[group]
        if self.p.target == "depth":
            return ("oof_correct_levels", "levels", "scored")
        if self.p.q_metric == "acc_trunc":
            return (f"acc_trunc@{L}", f"acct@{L}", "scored")
        return (f"acc@{L}", f"hit@{L}", f"nref@{L}")

    def q_vectors(self, group, v, oof=None):
        _, y, z = self.q_def(group)
        src = oof["v"] if (self.p.target == "depth" and group != "address") else v
        return src[y], src[z]

    def est(self, y, z, design=None) -> Est:
        return (design or self.design).estimate(y, z, self.p.method, self.p.level)

    def table(self, v, defs, mask=None, core=True) -> tuple[dict, dict]:
        w, c = {}, {}
        for name, yk, zk in defs:
            y, z = v[yk], v[zk]
            if mask is not None:
                y, z = y * mask, z * mask
            w[name] = self.est(y, z).as_dict()
            if core and _binary(y[z > 0]):
                c[name] = self.design.core_check(y, z, self.p.level).as_dict()
        return w, c

    # -- one candidate --------------------------------------------------------------------------
    def candidate(self, ps, v, u) -> dict:
        g = ps.group
        out = {
            "name": ps.name,
            "model": ps.model,
            "variant": ps.variant,
            "task": ps.task,
            "schema": ps.schema,
            "path": ps.path,
            "screen": self.is_screen(ps),
            "suggestion": bool(ps.meta.get("suggestion")),
            "ens2": bool(ps.meta.get("ens2")),
            "members": ps.meta.get("members"),
        }
        oof = None
        if ps.task == "topic":
            Lmax = self.tree(ps.schema).max_level
            defs = M.topic_metric_defs(Lmax)
            out["weighted"], out["core"] = self.table(v, defs)
            out["subsets"] = {}
            for sub, mask in (
                ("offline", 1 - v["online"]),
                ("online_only", v["online"]),
            ):
                out["subsets"][sub] = self.table(v, defs, mask, core=False)[0]
            out["counts"] = {
                "scored": int(v["scored"].sum()),
                "ref_none": int(v["ref_none"].sum()),
                "no_label": int((v["nolabel"] * v["scored"]).sum()),
                "failed": int(v["fail"].sum()),
            }
            kw = dict(
                min_precision=self.p.min_precision,
                criterion=self.p.depth_criterion,
                contiguous=self.p.depth_contiguous,
                method=self.p.method,
            )
            oof = D.cross_fit(self.design, v, Lmax, **kw)
            ow, oc = self.table(oof["v"], D.oof_metric_defs(Lmax))
            out["oof"] = {
                "cuts": oof["cuts"],
                "cut_full": oof["cut_full"],
                "weighted": ow,
                "core": oc,
                "criterion": self.p.depth_criterion,
                "min_precision": self.p.min_precision,
            }
            out["p1"] = out["weighted"]["P@1"]["est"]
            depth_hist = {}
            for d in range(Lmax + 1):
                depth_hist[d] = int(((v["depth"] == d) & (v["scored"] > 0)).sum())
            out["depth_hist"] = depth_hist
        else:
            out["weighted"], out["core"] = self.table(v, M.ADDRESS_METRIC_DEFS)
            out["counts"] = {
                "ref": int(v["ref"].sum()),
                "ref_main": int(v["ref_main"].sum()),
                "pred_main": int(v["pred_main"].sum()),
                "failed": int(v["fail"].sum()),
                "geocoded_pairs": int(v["loc_by_dist"].sum()),
                "geocode_missing": int(v["geo_missing"].sum()),
            }
            out["p1"] = out["weighted"]["addr_P"]["est"]
        out["efficiency"] = M.efficiency(self.design, u, ps.meta, self.p.method)
        ce = self.est(u["C"], u["attempted"])
        out["efficiency"]["C_mean_ci"] = ce.as_dict()
        y, z = self.q_vectors(g, v, oof)
        q = self.est(y, z)
        out["Q"] = q.as_dict()
        out["Q_core"] = (
            self.design.core_check(y, z, self.p.level).as_dict()
            if _binary(y[z > 0])
            else None
        )
        out["Q_metric"] = self.q_def(g)[0]
        return out, oof

    def is_screen(self, ps) -> bool:
        if ps.meta.get("screen") is not None:
            return bool(ps.meta["screen"])
        return ps.model in self.p.screen_models

    # -- cost -----------------------------------------------------------------------------------
    def cost_axis(self, cands: dict) -> str:
        if self.p.cost_axis != "auto":
            return self.p.cost_axis
        effs = [c["efficiency"] for c in cands.values()]
        if effs and all(e.get("usd_per_1M") is not None for e in effs):
            return "usd"
        if effs and all(e.get("gpu_hours_per_1M") is not None for e in effs):
            return "gpu_hours"
        return "proxy"

    @staticmethod
    def cost_of(c: dict, axis: str):
        e = c["efficiency"]
        return {
            "usd": e.get("usd_per_1M"),
            "gpu_hours": e.get("gpu_hours_per_1M"),
            "proxy": e.get("C_per_1M"),
        }[axis]

    # -- one task -------------------------------------------------------------------------------
    def group(self, g: str, sets: list) -> dict:
        res = {"candidates": {}, "q_metric": self.q_def(g)[0]}
        V, U, O = {}, {}, {}
        for ps in sets:
            V[ps.name], U[ps.name] = self.vectors(ps), M.usage_vectors(self.sample, ps)
            res["candidates"][ps.name], O[ps.name] = self.candidate(
                ps, V[ps.name], U[ps.name]
            )
        by_name = {ps.name: ps for ps in sets}
        # ens2
        if g != "address" and self.p.ens2_pairs not in ("none", None, []):
            singles = [ps for ps in sets if not ps.meta.get("ens2")]
            pairs = self.ens2_pairs(singles, res["candidates"])
            for a, b in pairs:
                e = ens2(a, b, self.tree(g), member_fail=self.p.ens2_member_fail)
                V[e.name], U[e.name] = self.vectors(e), M.usage_vectors(self.sample, e)
                res["candidates"][e.name], O[e.name] = self.candidate(
                    e, V[e.name], U[e.name]
                )
                usd = ens2_usd_per_1M(
                    res["candidates"][a.name]["efficiency"],
                    res["candidates"][b.name]["efficiency"],
                )
                if usd is not None:
                    res["candidates"][e.name]["efficiency"]["usd_per_1M"] = usd
                by_name[e.name] = e
        axis = self.cost_axis(res["candidates"])
        res["cost_axis"] = axis
        cands = {}
        for n_, c in res["candidates"].items():
            c["C"] = self.cost_of(c, axis)
            cands[n_] = {
                "name": n_,
                "Q": c["Q"]["est"],
                "Q_se": c["Q"]["se"],
                "C": c["C"],
                "fail": c["efficiency"]["failed_rate"],
                "p1": c["p1"],
            }
        QV = {n_: self.q_vectors(g, V[n_], O.get(n_)) for n_ in cands}

        def paired_w(x, b, design=None, qv=None):
            qv = qv or QV
            return (design or self.design).diff(
                *qv[x], *qv[b], self.p.method, self.p.level
            )

        cl = list(cands.values())
        main = decide(cl, paired_w, self.p.margin, self.p.max_fail, self.p.p_floor)
        res["decision"] = main
        res["paired"] = []
        if main["best"]:
            for n_ in cands:
                if n_ != main["best"]:
                    d = paired_w(n_, main["best"]).as_dict()
                    res["paired"].append(
                        {"x": n_, "y": main["best"], "metric": res["q_metric"], **d}
                    )
                    if g != "address":
                        Lq = self.p.q_level[g]
                        dp = self.design.diff(
                            V[n_][f"hit@{Lq}"],
                            V[n_][f"cov@{Lq}"],
                            V[main["best"]][f"hit@{Lq}"],
                            V[main["best"]][f"cov@{Lq}"],
                            self.p.method,
                            self.p.level,
                        ).as_dict()
                        res["paired"].append(
                            {"x": n_, "y": main["best"], "metric": f"P@{Lq}", **dp}
                        )
        # shifts (step 7)
        variants = {}
        ci = self.core_idx
        if len(ci):
            qv_core = {n_: (QV[n_][0][ci], QV[n_][1][ci]) for n_ in cands}
            cc = []
            for n_, c in cands.items():
                q = self.core_design.ratio(*qv_core[n_])
                cc.append({**c, "Q": q})
            variants["core_unweighted"] = decide(
                cc,
                lambda x, b: self.core_design.diff(
                    *qv_core[x], *qv_core[b], "taylor", self.p.level
                ),
                self.p.margin,
                self.p.max_fail,
                self.p.p_floor,
            )
        noise = {}
        for lab, arefs in self.alt_refs.items():
            qv_alt = {}
            for n_ in cands:
                va = self.vectors(by_name[n_], arefs)
                oa = None
                if self.p.target == "depth" and g != "address":
                    oa = D.cross_fit(
                        self.design,
                        va,
                        self.tree(g).max_level,
                        min_precision=self.p.min_precision,
                        criterion=self.p.depth_criterion,
                        contiguous=self.p.depth_contiguous,
                        method=self.p.method,
                    )
                qv_alt[n_] = self.q_vectors(g, va, oa)
            ca = [{**c, "Q": self.design.ratio(*qv_alt[n_])} for n_, c in cands.items()]
            variants[f"label_{lab}"] = decide(
                ca,
                lambda x, b, q=qv_alt: paired_w(x, b, qv=q),
                self.p.margin,
                self.p.max_fail,
                self.p.p_floor,
            )
            dm = self.double
            noise[lab] = {
                n_: self.est(qv_alt[n_][0] * dm, qv_alt[n_][1] * dm).as_dict()
                for n_ in cands
            }
        res["variants"] = variants
        res["noise"] = noise
        res["final"] = resolve_shifts(main, variants, cands, self.p.tie_rule)
        res["per_stratum"] = self.per_stratum(g, V)
        return res

    def ens2_pairs(self, singles: list, cands: dict) -> list:
        p = self.p.ens2_pairs
        if p == "all":
            return list(combinations(singles, 2))
        if p == "top2":
            ranked = sorted(
                (s for s in singles if cands[s.name]["Q"]["est"] is not None),
                key=lambda s: -cands[s.name]["Q"]["est"],
            )
            return [tuple(ranked[:2])] if len(ranked) >= 2 else []
        by = {s.name: s for s in singles}
        out = []
        for spec in p:
            a, b = spec.split("+", 1)
            if a in by and b in by:
                out.append((by[a], by[b]))
        return out

    # -- per true stratum -----------------------------------------------------------------------
    def true_class(self, g: str, it: dict) -> str | None:
        ref = self.refs.get(it["key"]) or {}
        if g == "address":
            a = ref.get("address")
            if a is None:
                return None
            if a.get("main_index") is None:
                return f"addr:none:{a.get('no_address_reason')}"
            flags = set(a.get("flags") or [])
            for f in ("po_box", "multi_address", "obfuscated", "non_dach"):
                if f in flags:
                    return f"addr:{f}"
            return "addr:main"
        t = ref.get(g)
        if not t or t.get("main") is None:
            return None
        tree = self.tree(g)
        rp = tree.canonical_path(t["main"]) if t["main"] in tree else []
        if not rp:
            return None
        lv = 2 if g == "poi" else 3
        k = min(lv, len(rp))
        return f"{g}{k}:{rp[k - 1]}"

    def per_stratum(self, g: str, V: dict) -> dict:
        cls = [self.true_class(g, it) for it in self.sample.items]
        _, yk, zk = (
            self.q_def(g)
            if self.p.target != "depth" or g == "address"
            else (None, *self.q_def_acc(g))
        )
        out = {}
        for c in sorted({x for x in cls if x}):
            idx = np.array([x == c for x in cls])
            row = {}
            for n_, v in V.items():
                y, z = v[yk][idx], v[zk][idx]
                n = int((z > 0).sum())
                k = float(y[z > 0].sum())
                if n >= self.p.min_stratum_n:
                    lo, hi = wilson(k, n)
                    row[n_] = {"n": n, "k": k, "rate": k / n, "lo": lo, "hi": hi}
                else:
                    row[n_] = {"n": n, "k": k}
            out[c] = row
        return out

    def q_def_acc(self, g):
        L = self.p.q_level[g]
        return (f"hit@{L}", f"nref@{L}")

    # -- all ------------------------------------------------------------------------------------
    def run(self) -> dict:
        res = {
            "params": self.p.as_dict(),
            "n_items": len(self.sample),
            "n_core": int(len(self.core_idx)),
            "n_double": int(self.double.sum()),
            "kish_n": round(
                float(self.design.w.sum() ** 2 / (self.design.w**2).sum()), 1
            ),
            "variance_strata": len(set(self.design.vstrata)),
            "groups": {},
        }
        groups = {}
        for ps in self.predsets:
            groups.setdefault(ps.group, []).append(ps)
        for g in sorted(groups):
            res["groups"][g] = self.group(g, groups[g])
        # Holm over the primary tests: Q of each candidate vs the best, per task
        pv = {}
        for g, r in res["groups"].items():
            for d in r["paired"]:
                if d["metric"] == r["q_metric"] and d.get("p") is not None:
                    pv[f"{g}:{d['x']} vs {d['y']}"] = d["p"]
        res["holm"] = holm(pv)
        return res


def score(sample, refs, predsets, params: Params | None = None, **kw) -> dict:
    return Scorer(sample, refs, predsets, params, **kw).run()
