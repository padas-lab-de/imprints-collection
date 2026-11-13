"""Per-item metric vectors (protocol 5.1-5.3). Every metric is a pair (y, z) of item vectors in sample
order; the population figure is the Hajek ratio sum(w y) / sum(w z) (``estimators.Design``).

Topics (E49 semantics, canonical paths, per level L):
- nref@L: the reference reaches L; cov@L: and the prediction reaches L; hit@L: and the prefixes agree.
- acc@L = hit/nref, P@L = hit/cov, cov@L = cov/nref (protocol 5.1).
- acct@L (E49 "acc_trunc", the "acc" column of the E49 summaries): both paths cut to L, over all
  scored items; an item whose reference stops above L counts as correct if the prediction equals it.
- items without a topic reference (no label, not live, reference main None) do not count.
- a missing prediction line or an error counts as failed (no answer). ``no_input`` (no text): "miss"
  (default; counts as no answer, the item stays) or "skip" (E49: the item does not count).

Addresses (main address only, E50 matcher):
- location match: same postcode + street after normalisation, or both geocoded and <= 100 m (1 km
  secondary). A pair without both geocodes is scored by postcode + street only.
- loc100_all: over all items with an address reference, "no address" vs "no address" counts as a
  match (E50 ``main_ok``); loc100: over items whose reference has an address.
- no prediction line, an error or ``no_input`` = "no address" (E50 rule).
"""

from __future__ import annotations

import re

import numpy as np

from ic.eval._legacy import addr
from ic.eval.io import addr_key
from ic.evaluation.geocoding import haversine_m

FIELDS = ("street", "number", "postcode", "town", "country")
OUT_W = 10  # E50 cost proxy C = uncached prompt + 10 x completion tokens


def pred_state(row: dict | None) -> str:
    if row is None:
        return "missing"
    err = row.get("error")
    if err == "no_input":
        return "no_input"
    if err:
        return "failed"
    return "ok"


# ---------------------------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------------------------


def topic_vectors(
    sample, refs: dict, ps, tree, no_input: str = "miss", schema: str | None = None
) -> dict:
    schema = schema or ps.schema
    n, Lmax = len(sample), tree.max_level
    P = lambda i: tree.canonical_path(i) if i in tree else []  # noqa: E731
    v = {
        k: np.zeros(n)
        for k in (
            "scored",
            "nolabel",
            "fail",
            "online",
            "ref_none",
            "depth",
            "refdepth",
        )
    }
    for L in range(1, Lmax + 1):
        for k in ("nref", "cov", "hit", "acct", "len"):
            v[f"{k}@{L}"] = np.zeros(n)
    v["rpath"], v["ppath"] = [[] for _ in range(n)], [[] for _ in range(n)]
    for i, it in enumerate(sample.items):
        ref = (refs.get(it["key"]) or {}).get(schema)
        if ref is None:
            continue
        if ref.get("main") is None or ref["main"] not in tree:
            v["ref_none"][i] = 1
            continue
        row = ps.rows.get(it["key"])
        st = pred_state(row)
        if st == "no_input" and no_input == "skip":
            continue
        rp = P(ref["main"])
        pp = P(row.get("main")) if st == "ok" else []
        v["rpath"][i], v["ppath"][i] = rp, pp
        v["scored"][i] = 1
        v["online"][i] = bool(ref.get("online_only"))
        v["fail"][i] = st in ("failed", "missing")
        v["nolabel"][i] = not pp
        v["depth"][i] = len(pp)
        v["refdepth"][i] = len(rp)
        alts = [P(ref["main"])] + [P(e) for e in ref.get("extra", []) if e in tree]
        for L in range(1, Lmax + 1):
            if len(rp) >= L:
                v[f"nref@{L}"][i] = 1
                if len(pp) >= L:
                    v[f"cov@{L}"][i] = 1
                    v[f"hit@{L}"][i] = pp[:L] == rp[:L]
            v[f"acct@{L}"][i] = bool(pp) and pp[:L] == rp[:L]
            v[f"len@{L}"][i] = bool(pp) and any(pp[:L] == a[:L] for a in alts)
    return v


def topic_metric_defs(Lmax: int) -> list[tuple[str, str, str]]:
    out = []
    for L in range(1, Lmax + 1):
        out += [
            (f"P@{L}", f"hit@{L}", f"cov@{L}"),
            (f"acc@{L}", f"hit@{L}", f"nref@{L}"),
            (f"cov@{L}", f"cov@{L}", f"nref@{L}"),
            (f"acc_trunc@{L}", f"acct@{L}", "scored"),
            (f"lenient@{L}", f"len@{L}", "scored"),
        ]
    out += [("no_label", "nolabel", "scored"), ("failed", "fail", "scored")]
    return out


# ---------------------------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------------------------


def location_match(
    ref_main: dict, pred_main: dict, geocodes: dict, radius_m: float
) -> tuple[bool, str]:
    """(match, how): how = postcode+street | distance | no_geocode."""
    AS = addr()
    if (
        AS.norm("postcode", ref_main.get("postcode", ""))
        and AS.norm("street", ref_main.get("street", ""))
        and AS.field_eq(
            "postcode", ref_main.get("postcode", ""), pred_main.get("postcode", "")
        )
        and AS.field_eq(
            "street", ref_main.get("street", ""), pred_main.get("street", "")
        )
    ):
        return True, "postcode+street"
    gr, gp = geocodes.get(addr_key(ref_main)), geocodes.get(addr_key(pred_main))
    if gr and gp:
        return haversine_m(gr[1], gr[0], gp[1], gp[0]) <= radius_m, "distance"
    return False, "no_geocode"


def evidence_ok(pm: dict, text: str) -> bool:
    """E50 evidence check: the postcode digits and the start of the street occur in the input text."""
    AS = addr()
    t = AS.norm("street", text)
    pc = AS.norm("postcode", pm.get("postcode", ""))
    st = AS.norm("street", pm.get("street", ""))
    return (not pc or pc in re.sub(r"\D", "", text)) and (
        not st or st.split("strasse")[0][:6] in t
    )


def address_vectors(
    sample, refs: dict, ps, geocodes: dict | None = None, texts: dict | None = None
) -> dict:
    AS = addr()
    geocodes = geocodes or {}
    texts = texts or {}
    n = len(sample)
    keys = (
        "ref",
        "ref_main",
        "ref_none",
        "pred_main",
        "pred_none",
        "both_main",
        "loc100_all",
        "loc100",
        "loc1km_all",
        "loc1km",
        "exact",
        "role_ok",
        "na_tp",
        "na_pred",
        "false_addr",
        "missed",
        "reason_ok",
        "geo_fail",
        "geo_missing",
        "ev_n",
        "halluc",
        "fail",
        "loc_by_dist",
        "tp",
        "np",
        "nr",
    )
    v = {k: np.zeros(n) for k in keys}
    for f in FIELDS:
        for k in ("tp", "np", "nr"):
            v[f"{k}_{f}"] = np.zeros(n)
    for i, it in enumerate(sample.items):
        ref = (refs.get(it["key"]) or {}).get("address")
        if ref is None:
            continue
        row = ps.rows.get(it["key"])
        st = pred_state(row)
        prec = (
            AS.to_record(row)
            if st == "ok"
            else {"addresses": [], "main_index": None, "no_address_reason": None}
        )
        rm = (
            ref["addresses"][ref["main_index"]]
            if ref.get("main_index") is not None
            else None
        )
        pm = (
            prec["addresses"][prec["main_index"]]
            if prec.get("main_index") is not None
            else None
        )
        v["ref"][i] = 1
        v["fail"][i] = st in ("failed", "missing")
        v["ref_main"][i] = rm is not None
        v["ref_none"][i] = rm is None
        v["pred_main"][i] = pm is not None
        v["pred_none"][i] = pm is None
        for f in FIELDS:
            r_, p_ = (rm or {}).get(f, ""), (pm or {}).get(f, "")
            nr, np_ = bool(AS.norm(f, r_)), bool(AS.norm(f, p_))
            tp = nr and np_ and AS.field_eq(f, r_, p_)
            v[f"nr_{f}"][i], v[f"np_{f}"][i], v[f"tp_{f}"][i] = nr, np_, tp
            v["nr"][i] += nr
            v["np"][i] += np_
            v["tp"][i] += tp
        if pm is not None:
            g = geocodes.get(addr_key(pm), "absent")
            v["geo_missing"][i] = g == "absent"
            v["geo_fail"][i] = g is None
            if it["key"] in texts:
                v["ev_n"][i] = 1
                v["halluc"][i] = not evidence_ok(pm, texts[it["key"]])
        if rm is None:
            v["loc100_all"][i] = v["loc1km_all"][i] = pm is None
            v["na_tp"][i] = pm is None
            v["false_addr"][i] = pm is not None
            v["reason_ok"][i] = pm is None and ref.get("no_address_reason") == prec.get(
                "no_address_reason"
            )
        else:
            v["missed"][i] = pm is None
        v["na_pred"][i] = pm is None
        if rm is not None and pm is not None:
            v["both_main"][i] = 1
            ok100, how = location_match(rm, pm, geocodes, 100.0)
            ok1k, _ = location_match(rm, pm, geocodes, 1000.0)
            v["loc100"][i] = v["loc100_all"][i] = ok100
            v["loc1km"][i] = v["loc1km_all"][i] = ok1k
            v["loc_by_dist"][i] = how == "distance"
            v["exact"][i] = all(
                AS.field_eq(f, rm[f], pm[f])
                for f in ("street", "number", "postcode", "town")
            )
            v["role_ok"][i] = (rm.get("role") or "operator") == (
                pm.get("role") or "operator"
            )
    v["np+nr"] = v["np"] + v["nr"]
    v["2tp"] = 2 * v["tp"]
    for f in FIELDS:
        v[f"np+nr_{f}"] = v[f"np_{f}"] + v[f"nr_{f}"]
        v[f"2tp_{f}"] = 2 * v[f"tp_{f}"]
    return v


ADDRESS_METRIC_DEFS = [
    ("loc100_all", "loc100_all", "ref"),
    ("loc100", "loc100", "ref_main"),
    ("loc1km_all", "loc1km_all", "ref"),
    ("loc1km", "loc1km", "ref_main"),
    ("addr_P", "loc100", "pred_main"),
    ("exact", "exact", "ref_main"),
    ("exact_both", "exact", "both_main"),
    ("field_P", "tp", "np"),
    ("field_R", "tp", "nr"),
    ("field_F1", "2tp", "np+nr"),
    *[
        (f"{m}_{f}", y, z)
        for f in FIELDS
        for m, y, z in (
            ("P", f"tp_{f}", f"np_{f}"),
            ("R", f"tp_{f}", f"nr_{f}"),
            ("F1", f"2tp_{f}", f"np+nr_{f}"),
        )
    ],
    ("noaddr_P", "na_tp", "na_pred"),
    ("noaddr_R", "na_tp", "ref_none"),
    ("false_address_rate", "false_addr", "ref_none"),
    ("missed_address_rate", "missed", "ref_main"),
    ("reason_acc", "reason_ok", "na_tp"),
    ("role_acc", "role_ok", "both_main"),
    ("geocode_fail", "geo_fail", "pred_main"),
    ("geocode_missing", "geo_missing", "pred_main"),
    ("hallucination", "halluc", "ev_n"),
    ("failed", "fail", "ref"),
]


# ---------------------------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------------------------


def item_cost(u: dict, meta: dict) -> dict:
    tin, cin, tout = (
        u.get("prompt_tokens", 0) or 0,
        u.get("cached_prompt_tokens", 0) or 0,
        u.get("completion_tokens", 0) or 0,
    )
    out = {"C": tin - cin + OUT_W * tout}
    if meta.get("usd_per_mtok_in") is not None:
        p_in = meta["usd_per_mtok_in"]
        out["usd"] = (
            (tin - cin) * p_in
            + cin * meta.get("usd_per_mtok_cached", p_in)
            + tout * meta.get("usd_per_mtok_out", p_in)
        ) / 1e6
    return out


def usage_vectors(sample, ps) -> dict:
    n = len(sample)
    keys = (
        "attempted",
        "fail",
        "calls",
        "call_den",
        "tok_in",
        "cached_in",
        "tok_out",
        "reasoning",
        "C",
        "usd",
        "s",
        "trunc",
    )
    v = {k: np.zeros(n) for k in keys}
    v["s"][:] = np.nan
    for i, it in enumerate(sample.items):
        row = ps.rows.get(it["key"])
        st = pred_state(row)
        if st == "no_input":
            continue
        v["attempted"][i] = 1
        v["fail"][i] = st in ("failed", "missing")
        if row is None:
            v["call_den"][i] = 1
            continue
        u = row.get("usage") or {}
        v["calls"][i] = u.get("calls", 0) or 0
        v["call_den"][i] = max(v["calls"][i], 1)
        v["tok_in"][i] = u.get("prompt_tokens", 0) or 0
        v["cached_in"][i] = u.get("cached_prompt_tokens", 0) or 0
        v["tok_out"][i] = u.get("completion_tokens", 0) or 0
        v["reasoning"][i] = u.get("reasoning_tokens", 0) or 0
        v["trunc"][i] = u.get("truncated", 0) or 0
        c = item_cost(u, ps.meta)
        v["C"][i] = c["C"]
        v["usd"][i] = c.get("usd", np.nan)
        s = row.get("latency_s", u.get("latency_s"))
        v["s"][i] = np.nan if s is None else float(s)
    return v


def efficiency(design, v: dict, meta: dict, method: str = "taylor") -> dict:
    """Weighted efficiency summary for one prediction set. Cost per 1M hosts: proxy C always; USD from
    token prices, or GPU-hours (measured throughput) x USD per GPU-hour (shadow price) if given.
    """
    att = v["attempted"]
    out = {}
    e = design.estimate(v["fail"], v["call_den"], method)
    out["failed_per_1000_calls"] = None if e.est is None else 1000 * e.est
    out["failed_rate"] = e.est
    out["failed_rate_items"] = design.ratio(v["fail"], att)
    for k in ("tok_in", "tok_out", "cached_in", "reasoning", "calls", "C"):
        out[f"{k}_mean"] = design.ratio(v[k], att)
        out[f"{k}_p95"] = design.quantile(v[k], 0.95, att)
    out["s_median"] = design.quantile(v["s"], 0.5, att)
    out["s_p95"] = design.quantile(v["s"], 0.95, att)
    out["truncated_rate"] = design.ratio((v["trunc"] > 0).astype(float), att)
    out["C_per_1M"] = None if out["C_mean"] is None else out["C_mean"] * 1e6
    if (
        not np.isnan(v["usd"][att > 0]).any()
        and meta.get("usd_per_mtok_in") is not None
    ):
        m = design.ratio(np.nan_to_num(v["usd"]), att)
        out["usd_per_1M"] = None if m is None else m * 1e6
    if meta.get("gpu_hours_per_mhost") is not None:
        out["gpu_hours_per_1M"] = float(meta["gpu_hours_per_mhost"])
        if meta.get("usd_per_gpu_hour") is not None:
            out["usd_per_1M"] = out.get("usd_per_1M", 0.0) + out[
                "gpu_hours_per_1M"
            ] * float(meta["usd_per_gpu_hour"])
    return out
