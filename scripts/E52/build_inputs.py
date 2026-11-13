"""E52: model inputs for the gold items from the same-day `ic fetch` text (D56 A).

    python3 -I scripts/E52/build_inputs.py --gold-dir <E53 gold dir> --sample <gold_sample.jsonl> \
        --out datasets/E52/gold_inputs.jsonl

One line per gold item, in gold_sample.jsonl order, made by scripts/E53/prefill.py read_ic_fetch (last line of
<host>/ic_fetch.jsonl, E51 clean_text, 6000 chars per field). The output has the e50_run.py --dev format.
Prints counts: items, no_ic_fetch, empty imprint text, empty landing-page text. Reads only; writes --out.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E53"))
import prefill as P  # noqa: E402


def counts(recs: list[dict]) -> dict:
    m = lambda r: r.get("meta") or {}  # noqa: E731
    return {
        "items": len(recs),
        "no_ic_fetch": sum(bool(m(r).get("no_ic_fetch")) for r in recs),
        "empty_imprint": sum(not (r.get("imprint_text") or "").strip() for r in recs),
        "empty_homepage": sum(not (r.get("homepage_text") or "").strip() for r in recs),
        "empty_both": sum(
            not (r.get("imprint_text") or "").strip()
            and not (r.get("homepage_text") or "").strip()
            for r in recs
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold-dir", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    hosts = [
        json.loads(l)["host"] for l in open(a.sample, encoding="utf-8") if l.strip()
    ]
    if len(set(hosts)) != len(hosts):
        sys.exit("duplicate hosts in the sample")
    recs = P.read_ic_fetch(Path(a.gold_dir), hosts)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(counts(recs)))


if __name__ == "__main__":
    main()
