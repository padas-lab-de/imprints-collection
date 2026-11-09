"""E49: summarise pilot runs without reference labels: cost, failures and agreement with a baseline run.

    python3 scripts/E49/pilot_summary.py --schema poi --base flat__qwen__home__dmax__nt-path results/E49/pilot/preds/poi/*.jsonl

Columns: n, errors, abstain (main null), unresolved answers (id not in schema), answers outside the offered
candidates, mean stop level, calls/host, prompt and completion tokens/host, embed/rerank tokens/host,
latency s/host, agreement with the baseline at level 1 and at the full path (canonical paths).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import load_schema  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--schema", required=True)
    ap.add_argument("--base", required=True, help="stem of the baseline file")
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    tree = load_schema(a.schema)
    runs = {Path(f).stem: {(r := json.loads(l))["host"]: r for l in open(f, encoding="utf-8") if l.strip()}
            for f in a.preds}
    base = runs.get(a.base, {})
    P = lambda i: tree.canonical_path(i) if i in tree else []  # noqa: E731
    hdr = ["run", "n", "err", "abst", "unres", "outside", "lvl", "calls", "tok in", "tok out", "emb+rr tok",
           "s/host", "agree L1", "agree full"]
    lines = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for name, rs in runs.items():
        v = list(rs.values())
        n = len(v)
        how = Counter(h for r in v for t in r.get("trace", []) for h in (t.get("how") or []))
        lv = [len(r.get("path") or []) for r in v if r.get("main")]
        u = lambda k: round(sum((r.get("usage") or {}).get(k, 0) for r in v) / max(n, 1))  # noqa: E731
        common = [h for h in rs if h in base and not rs[h].get("error") and not base[h].get("error")]
        a1 = sum(P(rs[h].get("main"))[:1] == P(base[h].get("main"))[:1] for h in common)
        af = sum(P(rs[h].get("main")) == P(base[h].get("main")) for h in common)
        row = [name, n, sum(bool(r.get("error")) for r in v), sum(r.get("main") is None for r in v),
               how["none"] + how["fuzzy"], how["outside_candidates"], round(sum(lv) / len(lv), 2) if lv else "",
               round(sum((r.get("usage") or {}).get("calls", 0) for r in v) / max(n, 1), 2), u("prompt_tokens"),
               u("completion_tokens"), u("embed_tokens") + u("rerank_tokens"),
               round(sum(r.get("latency_s", 0) for r in v) / max(n, 1), 1),
               f"{a1}/{len(common)}", f"{af}/{len(common)}"]
        lines.append("| " + " | ".join(map(str, row)) + " |")
    errs = Counter(r["error"][:60] for rs in runs.values() for r in rs.values() if r.get("error"))
    md = "\n".join(lines) + "\n\nErrors: " + json.dumps(errs.most_common(10), ensure_ascii=False) + "\n"
    print(md)
    if a.md:
        Path(a.md).write_text(md)


if __name__ == "__main__":
    main()
