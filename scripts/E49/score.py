"""E49: score prediction files against reference labels, per hierarchy level.

Reference labels (results/E49/labelling_spec.md), one line per host and schema:
  {host, schema, main: <node id or null>, extra: [<= 2 ids], path: [root..main], confidence, note}
Predictions: run.py output ({host, main, ranked, usage, error, ...}).

Paths are canonical: a node with exactly one child is extended down the chain (WZ 56.1 -> 56.11 when
56.11 is the only class), so levels L and L+1 are the same decision there.

Per level L (1 = roots):
  n_ref     hosts whose reference reaches level L (canonical depth >= L)
  coverage  share of those where the prediction reaches level L (abstain / stop higher = not covered)
  precision share of the covered where pred[:L] == ref[:L]
  acc       share of n_ref where pred[:L] == ref[:L]    (strict: abstain or stopping higher = wrong)
  acc_trunc share of ALL scored hosts where pred[:L] == ref[:L] after truncating both paths to L
            (a reference that ends above L is compared on its full path)
  lenient   acc_trunc where any of main + extra counts
  near      acc_trunc where a sibling whose title contains (or is contained in) the reference title also
            counts (general vs specific siblings such as Restaurant / Italienisches Restaurant)
  top3      acc_trunc where any of the first 3 ranked predictions counts
Hosts with a null reference main (nothing fits) are listed separately (pred abstained or not).
Hosts whose prediction has error "no_input" are not scored (imprint-only runs on hosts without imprint).

    python3 scripts/E49/score.py --refs results/E49/refs/poi.jsonl results/E49/preds/poi/*.jsonl
    python3 scripts/E49/score.py --refs ... --common --md results/E49/score_poi.md preds...
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import Tree, load_schema  # noqa: E402


def load_jsonl(p) -> list[dict]:
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def _near(tree: Tree, a: str, b: str) -> bool:
    if a == b:
        return True
    if a not in tree or b not in tree or tree[a].parent != tree[b].parent:
        return False
    ta, tb = tree[a].title.lower(), tree[b].title.lower()
    return ta in tb or tb in ta


def score(tree: Tree, refs: dict[str, dict], preds: list[dict]) -> dict:
    """refs: host -> label. Returns metrics dict with a per-level table."""
    P = lambda i: tree.canonical_path(i) if i in tree else []  # noqa: E731
    rows = []
    unresolved_refs = 0
    for p in preds:
        r = refs.get(p["host"])
        if r is None or p.get("error") == "no_input":
            continue
        if r.get("main") is not None and r["main"] not in tree:
            unresolved_refs += 1
            continue
        rows.append((r, p))
    ok_rows = [(r, p) for r, p in rows if r.get("main") is not None]
    none_rows = [(r, p) for r, p in rows if r.get("main") is None]
    out = {"n_scored": len(ok_rows), "n_ref_none": len(none_rows),
           "ref_none_pred_abstained": sum(p.get("main") is None for _, p in none_rows),
           "unresolved_refs": unresolved_refs,
           "abstain": sum(p.get("main") is None for _, p in ok_rows),
           "errors": sum(bool(p.get("error")) for _, p in ok_rows),
           "levels": []}
    n = len(ok_rows)
    for L in range(1, tree.max_level + 1):
        n_ref = cov = hit = acc_t = len_t = near_t = top3_t = 0
        for r, p in ok_rows:
            rp = P(r["main"])
            pp = P(p.get("main"))
            same = lambda q: bool(q) and q[:L] == rp[:L]  # noqa: E731
            if len(rp) >= L:
                n_ref += 1
                if len(pp) >= L:
                    cov += 1
                    hit += pp[:L] == rp[:L]
            acc_t += same(pp)
            alts = [r["main"]] + [e for e in (r.get("extra") or []) if e in tree]
            len_t += any(bool(pp) and pp[:L] == P(e)[:L] for e in alts)
            near_ok = same(pp) or (len(rp) <= L and p.get("main") in tree and _near(tree, tree.extend(p["main"]), rp[-1]))
            near_t += near_ok
            top3_t += any(same(P(q)) for q in (p.get("ranked") or [p.get("main")])[:3])
        f = lambda a, b: round(a / b, 3) if b else None  # noqa: E731
        out["levels"].append({"level": L, "n_ref": n_ref, "coverage": f(cov, n_ref), "precision": f(hit, cov),
                              "acc": f(hit, n_ref), "acc_trunc": f(acc_t, n), "lenient": f(len_t, n),
                              "near": f(near_t, n), "top3": f(top3_t, n)})
    u = [p.get("usage") or {} for _, p in rows]
    k = max(len(u), 1)
    out["cost_per_host"] = {
        "calls": round(sum(x.get("calls", 0) for x in u) / k, 2),
        "prompt_tokens": round(sum(x.get("prompt_tokens", 0) for x in u) / k),
        "completion_tokens": round(sum(x.get("completion_tokens", 0) for x in u) / k),
        "embed_tokens": round(sum(x.get("embed_tokens", 0) for x in u) / k),
        "latency_s": round(sum(p.get("latency_s", 0) for _, p in rows) / k, 2),
    }
    return out


def deepest_reliable(m: dict, min_precision: float) -> int | None:
    best = None
    for lv in m["levels"]:
        if lv["precision"] is not None and lv["precision"] >= min_precision:
            best = lv["level"]
        else:
            break
    return best


def to_md(results: list[tuple[str, dict]], min_precision: float) -> str:
    lines = []
    if not results:
        return ""
    levels = [lv["level"] for lv in results[0][1]["levels"]]
    hdr = ["run", "n", "abst", "calls", "tok in", "tok out", "s/host"] + [f"P@{L}" for L in levels] + \
          [f"cov@{L}" for L in levels] + [f"acc@{L}" for L in levels] + [f"len@{L}" for L in levels] + \
          [f"near@{L}" for L in levels] + [f"top3@{L}" for L in levels] + [f"deepest P>={min_precision}"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for name, m in results:
        c = m["cost_per_host"]
        lv = m["levels"]
        cell = lambda v: "" if v is None else f"{v:.3f}"  # noqa: E731
        row = [name, str(m["n_scored"]), str(m["abstain"]), str(c["calls"]), str(c["prompt_tokens"]),
               str(c["completion_tokens"]), str(c["latency_s"])]
        for key in ("precision", "coverage", "acc_trunc", "lenient", "near", "top3"):
            row += [cell(x[key]) for x in lv]
        row.append(str(deepest_reliable(m, min_precision)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("P = precision among hosts whose prediction reaches level L; cov = coverage; acc = accuracy with both "
                 "paths truncated to L; len = lenient (main + extra); near = general/specific sibling counts; "
                 "top3 = any of 3 ranked. Paths extended through single-child chains.")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--refs", required=True, nargs="+", help="reference label files (jsonl)")
    ap.add_argument("--schema", default=None, help="poi | wz | path (default: from the prediction files)")
    ap.add_argument("--common", action="store_true", help="score only hosts present (and with input) in all files")
    ap.add_argument("--min-precision", type=float, default=0.8)
    ap.add_argument("--md", default=None, help="write a markdown table here")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    preds = {f: load_jsonl(f) for f in a.preds}
    schema = a.schema or next(p["schema"] for ps in preds.values() for p in ps)
    tree = load_schema(schema)
    refs = {r["host"]: r for f in a.refs for r in load_jsonl(f) if r.get("schema", schema) == tree.name}
    if a.common:
        keep = set(refs)
        for ps in preds.values():
            keep &= {p["host"] for p in ps if p.get("error") != "no_input"}
        preds = {f: [p for p in ps if p["host"] in keep] for f, ps in preds.items()}
    results = [(Path(f).stem, score(tree, refs, ps)) for f, ps in preds.items()]
    md = to_md(results, a.min_precision)
    print(md)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(md)
    if a.json:
        Path(a.json).write_text(json.dumps(dict(results), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
