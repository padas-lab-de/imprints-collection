"""Gold-set build, step 1: exclusion lists (every host used before in a gold, pilot or prompt study).

    python3 -I goldset/exclusions.py --list NAME=FILE[,FILE...] [--list ...] [--out DIR]

FILE is a text file with one host per line, a JSONL file (``FILE.jsonl:FIELD`` reads that field of every line,
for example ``evaluation/gold_standard_data.jsonl:url``) or a capture folder (``DIR/``: one sub-folder per host;
the folder ``labels`` is ignored). All hosts of one NAME form one list.

Writes <out>/<NAME>.txt (normalised keys, sorted), <out>/union.txt and <out>/manifest.tsv (list, raw entries,
keys, source files, sha256). Default <out>: <data>/exclusions. Needs no network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, keys, sha256_file  # noqa


def lines(p: Path) -> list[str]:
    return [l.strip() for l in p.open(encoding="utf-8") if l.strip()]


def jsonl_field(p: Path, field: str) -> list[str]:
    return [json.loads(l)[field] for l in p.open(encoding="utf-8") if l.strip()]


def read_source(spec: str) -> tuple[list[str], Path | None]:
    """One source of a list -> (hosts, file to hash or None for a folder)."""
    if spec.endswith("/"):
        d = Path(spec)
        return sorted(x.name for x in d.iterdir() if x.is_dir() and x.name != "labels"), None
    if ".jsonl:" in spec:
        path, field = spec.rsplit(":", 1)
        return jsonl_field(Path(path), field), Path(path)
    return lines(Path(spec)), Path(spec)


def parse_lists(specs: list[str]) -> dict[str, tuple[list[str], list[Path]]]:
    out: dict[str, tuple[list[str], list[Path]]] = {}
    for spec in specs:
        name, _, files = spec.partition("=")
        if not name or not files:
            raise SystemExit(f"--list needs NAME=FILE[,FILE...], got {spec!r}")
        hosts, srcs = out.setdefault(name, ([], []))
        for f in files.split(","):
            h, p = read_source(f)
            hosts += h
            srcs.append(p if p is not None else Path(f))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="append", required=True, help="NAME=FILE[,FILE...], repeatable")
    ap.add_argument("--out", default=str(DATA / "exclusions"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, union = [], set()
    for name, (hosts, srcs) in parse_lists(a.list).items():
        ks = keys(hosts)
        union |= ks
        (out / f"{name}.txt").write_text("".join(k + "\n" for k in sorted(ks)), encoding="utf-8")
        rows.append([name, str(len(hosts)), str(len(ks)), ";".join(str(s) for s in srcs),
                     ";".join(sha256_file(s)[:16] if s.is_file() else "dir" for s in srcs)])
    (out / "union.txt").write_text("".join(k + "\n" for k in sorted(union)), encoding="utf-8")
    rows.append(["union", "", str(len(union)), "", ""])
    (out / "manifest.tsv").write_text("list\traw_entries\tkeys\tsources\tsha256_16\n"
                                      + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
    for r in rows:
        print("\t".join(r[:3]))


if __name__ == "__main__":
    main()
