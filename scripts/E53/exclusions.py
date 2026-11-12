"""E53 step 1: exclusion lists (every host used before in a gold, pilot or prompt study).

    python3 -I scripts/E53/exclusions.py

Reads (read only): main repo evaluation/, datasets/gold/, results/E49/, results/E51/; the aspe copies in
datasets/E53/exclusions/raw/aspe/ (scp from aspe:GitHub/imprints-collection/datasets/{E8,E12}).
Writes datasets/E53/exclusions/<list>.txt (normalised keys, sorted), union.txt, manifest.tsv
(list, raw hosts, keys, source files, sha256).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, MAIN, keys, sha256_file  # noqa: E402

OUT = DATA / "exclusions"
ASPE = OUT / "raw/aspe"


def lines(p: Path) -> list[str]:
    return [l.strip() for l in p.open(encoding="utf-8") if l.strip()]


def jsonl_field(p: Path, field: str) -> list[str]:
    return [json.loads(l)[field] for l in p.open(encoding="utf-8") if l.strip()]


def lists() -> dict[str, tuple[list[str], list[Path]]]:
    g = MAIN / "datasets/gold"
    old = MAIN / "evaluation/gold_standard_data.jsonl"
    cap_dirs = sorted(d.name for d in g.iterdir() if d.is_dir() and d.name != "labels")
    out = {
        "old_gold": (jsonl_field(old, "url"), [old]),
        "e8": (lines(ASPE / "E8_hosts.txt"), [ASPE / "E8_hosts.txt"]),
        "e12_screen": (lines(ASPE / "E12_hosts.txt"), [ASPE / "E12_hosts.txt"]),
        "e12_sample": (jsonl_field(ASPE / "gold_sample.jsonl", "host") + jsonl_field(g / "assignment.jsonl", "host")
                       + jsonl_field(g / "prefill.jsonl", "host") + cap_dirs + lines(g / "deferred_strato.txt"),
                       [ASPE / "gold_sample.jsonl", g / "assignment.jsonl", g / "prefill.jsonl",
                        g / "deferred_strato.txt"]),
        "e49": (lines(MAIN / "results/E49/dev_hosts.txt") + lines(MAIN / "results/E49/heldout/hosts.txt"),
                [MAIN / "results/E49/dev_hosts.txt", MAIN / "results/E49/heldout/hosts.txt"]),
        "e51": (lines(MAIN / "results/E51/dev2_hosts.txt") + lines(MAIN / "results/E51/heldout2_hosts.txt"),
                [MAIN / "results/E51/dev2_hosts.txt", MAIN / "results/E51/heldout2_hosts.txt"]),
    }
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, union = [], set()
    for name, (hosts, srcs) in lists().items():
        ks = keys(hosts)
        union |= ks
        (OUT / f"{name}.txt").write_text("".join(k + "\n" for k in sorted(ks)), encoding="utf-8")
        rows.append([name, str(len(hosts)), str(len(ks)), ";".join(str(s) for s in srcs),
                     ";".join(sha256_file(s)[:16] for s in srcs)])
    (OUT / "union.txt").write_text("".join(k + "\n" for k in sorted(union)), encoding="utf-8")
    rows.append(["union", "", str(len(union)), "", ""])
    (OUT / "manifest.tsv").write_text("list\traw_entries\tkeys\tsources\tsha256_16\n"
                                      + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
    for r in rows:
        print("\t".join(r[:3]))


if __name__ == "__main__":
    main()
