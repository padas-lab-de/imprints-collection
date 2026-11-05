#!/usr/bin/env python3
"""E40: apply the hand labels to sample_items.tsv and print precision / recall numbers with Wilson 95% CIs.

Usage: label_sample.py --items OUTDIR/sample_items.tsv --out OUTDIR/sample_labeled.tsv

Labels were assigned by reading the title and text snippet of every item (ids refer to sample_items.tsv drawn with
seed 40 by sample.py). Only the exceptions are listed; every other item of a group has the group default.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parking_filter import wilson

# group -> (default label, {id: (label, note)})
CORE_NOTICE = "sale_notice_on_live_site"
LABELS = {
    "flagged_core": ("placeholder_or_for_sale", {
        35: (CORE_NOTICE, "photo site with banner 'Diese Premium-Domain steht zum Verkauf'"),
        54: (CORE_NOTICE, "terrarium site with banner 'Diese Domain steht zum Verkauf'"),
    }),
    "flagged_ext": ("real_site", {  # constr / host: default real site that only mentions construction
        i: ("placeholder_or_for_sale", "page is only a placeholder") for i in (61, 63, 74, 77, 79, 81, 82, 83, 84)
    }),
    "unflagged": ("real_site", {}),
    "flagged_host": ("placeholder_or_for_sale", {}),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = [l.rstrip("\n").split("\t") for l in open(a.items, encoding="utf-8")]
    head, rows = rows[0], rows[1:]
    out = ["\t".join(head)]
    tally = {}
    for r in rows:
        i, g = int(r[0]), r[1]
        default, exc = LABELS[g]
        lab, note = exc.get(i, (default, ""))
        r[9], r[10] = lab, note
        tally.setdefault(g, []).append(lab)
        out.append("\t".join(r))
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")

    def line(name, k, n):
        lo, hi = wilson(k, n)
        print(f"{name}: {k}/{n} = {k / n:.3f}  Wilson 95% CI [{lo:.3f}, {hi:.3f}]")

    core = tally["flagged_core"]
    line("precision core (sale+park) strict (notice-on-live-site counted wrong)", core.count("placeholder_or_for_sale"), len(core))
    line("precision core lenient (notice-on-live-site counted right)", len(core) - core.count("real_site"), len(core))
    ext = tally["flagged_ext"]
    line("precision under-construction (constr) sample", ext.count("placeholder_or_for_sale"), len(ext))
    line("precision host-only sample", tally["flagged_host"].count("placeholder_or_for_sale"), len(tally["flagged_host"]))
    un = tally["unflagged"]
    k = un.count("real_site")
    line("unflagged sample: real sites (parked/for-sale/placeholder missed = %d)" % (len(un) - k), k, len(un))
    lo, hi = wilson(len(un) - k, len(un))
    print(f"miss rate among unflagged found sites: {(len(un) - k) / len(un):.3f}  Wilson 95% CI [{lo:.3f}, {hi:.3f}]")


if __name__ == "__main__":
    main()
