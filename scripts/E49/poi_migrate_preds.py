"""E49: migrate poi (v2) prediction files to poi3 ids through results/E49/poi_v2_to_v3.json.

    python3 scripts/E49/poi_migrate_preds.py --out-dir results/E49/poi3/migrated/poi3 preds/poi/flat__qwen....jsonl ...
Each output file keeps its name; schema becomes "poi3"; main, ranked and path are mapped (unknown id -> abstain).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import load_schema  # noqa: E402


def migrate(rec: dict, m: dict, t3) -> dict:
    mp = lambda i: m.get(i) if m.get(i) in t3 else None  # noqa: E731
    main = mp(rec.get("main"))
    ranked = []
    for i in rec.get("ranked") or []:
        j = mp(i)
        if j and j not in ranked:
            ranked.append(j)
    return {**rec, "schema": "poi3", "main": main, "ranked": ranked, "path": t3.path(main) if main else [],
            "migrated_from": rec.get("tag")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--map", default="results/E49/poi_v2_to_v3.json")
    a = ap.parse_args()
    m = json.loads(Path(a.map).read_text(encoding="utf-8"))
    t3 = load_schema("poi3")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for f in a.preds:
        rows = [json.loads(l) for l in Path(f).read_text(encoding="utf-8").splitlines() if l.strip()]
        lost = sum(r.get("main") is not None and m.get(r["main"]) not in t3 for r in rows)
        (out / Path(f).name).write_text("".join(json.dumps(migrate(r, m, t3), ensure_ascii=False) + "\n" for r in rows),
                                        encoding="utf-8")
        print(f"{Path(f).name}: {len(rows)} hosts, {lost} unmapped")


if __name__ == "__main__":
    main()
