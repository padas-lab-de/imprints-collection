"""ens2 from stored single predictions (protocol 4, 7.5; E49 level majority).

The vote descends the tree while both members agree (strict majority of two voters), so the ens2
answer is the longest common prefix of the two canonical paths. No model calls; cost and latency are
the sums of both members. A host where a member failed or has no line is failed in ens2; ``no_input``
only if both members had no input.
"""

from __future__ import annotations

from ic.eval._legacy import vote
from ic.eval.io import PredSet
from ic.eval.metrics import pred_state

USAGE_SUM = (
    "calls",
    "cached",
    "prompt_tokens",
    "completion_tokens",
    "embed_tokens",
    "rerank_tokens",
    "latency_s",
    "cached_prompt_tokens",
    "reasoning_tokens",
    "truncated",
    "fast_calls",
)


def ens2(
    a: PredSet, b: PredSet, tree, name: str | None = None, member_fail: str = "fail"
) -> PredSet:
    """member_fail: "fail" (default; the ens2 line is failed) or "abstain" (E49 ensemble.py: the failed
    member votes None, so with two voters the ens2 answer is empty but not an error)."""
    assert (
        a.task == b.task == "topic" and a.schema == b.schema
    ), "ens2 needs two topic sets of one schema"
    lm = vote().level_majority
    rows = {}
    for k in sorted(set(a.rows) | set(b.rows)):
        ra, rb = a.rows.get(k), b.rows.get(k)
        sa, sb = pred_state(ra), pred_state(rb)
        host = (ra or rb)["host"]
        u = {
            f: (((ra or {}).get("usage") or {}).get(f, 0) or 0)
            + (((rb or {}).get("usage") or {}).get(f, 0) or 0)
            for f in USAGE_SUM
        }
        lat = ((ra or {}).get("latency_s") or 0) + ((rb or {}).get("latency_s") or 0)
        row = {
            "host": host,
            "schema": a.schema,
            "task": "topic",
            "model": "ensemble",
            "usage": u,
            "latency_s": lat,
            "members": [a.name, b.name],
            "samples": [(ra or {}).get("main"), (rb or {}).get("main")],
        }
        if sa == "no_input" and sb == "no_input":
            row.update(main=None, error="no_input")
        elif (sa != "ok" or sb != "ok") and member_fail == "fail":
            row.update(main=None, error="member_failed")
        elif sa != "ok" or sb != "ok":
            row.update(main=None, error=None)
        else:
            row.update(main=lm(tree, [ra.get("main"), rb.get("main")]), error=None)
        rows[k] = row
    nm = name or f"ens2[{a.name}+{b.name}]"
    meta = {
        "ens2": True,
        "members": [a.name, b.name],
        "screen": bool(a.meta.get("screen") or b.meta.get("screen")),
        "suggestion": bool(a.meta.get("suggestion") or b.meta.get("suggestion")),
    }
    for k in ("gpu_hours_per_mhost",):
        if a.meta.get(k) is not None and b.meta.get(k) is not None:
            meta[k] = a.meta[k] + b.meta[k]
    if a.meta.get("usd_per_gpu_hour") is not None and a.meta.get(
        "usd_per_gpu_hour"
    ) == b.meta.get("usd_per_gpu_hour"):
        meta["usd_per_gpu_hour"] = a.meta["usd_per_gpu_hour"]
    return PredSet(
        nm, "topic", a.schema, "ensemble", f"{a.name}+{b.name}", rows, "", meta
    )


def ens2_usd_per_1M(eff_a: dict, eff_b: dict) -> float | None:
    """ens2 USD per 1M hosts = sum of the members (token prices differ by member)."""
    if eff_a.get("usd_per_1M") is None or eff_b.get("usd_per_1M") is None:
        return None
    return eff_a["usd_per_1M"] + eff_b["usd_per_1M"]
