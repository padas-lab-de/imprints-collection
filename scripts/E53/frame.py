"""E53 step 2: frame F0 = release sites (r4 + E40 r2) minus the exclusion lists; seeded permutation; S1.

    python3 -I scripts/E53/frame.py [--n1 20000] [--seed 20261112]

Writes datasets/E53/frame/F0_perm.txt (all of F0 in permutation order; line i = rank i),
datasets/E53/phase1_hosts.txt (S1 = first n1 lines), datasets/E53/frame/frame.json and results/E53/frame.md.
S1 can be extended later: take a longer prefix of F0_perm.txt (still an SRS of F0).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, FRAME_SRC, N1, SEED, norm_host, permute, sha256_file  # noqa: E402

LISTS = ("old_gold", "e8", "e12_screen", "e12_sample", "e49", "e51")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n1", type=int, default=N1)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--report", default="results/E53/frame.md")
    a = ap.parse_args()
    ex = {n: {l.strip() for l in open(DATA / f"exclusions/{n}.txt") if l.strip()} for n in LISTS}
    union = set().union(*ex.values())
    U = [l.strip() for l in open(FRAME_SRC, encoding="utf-8") if l.strip()]
    ukeys = [norm_host(h) for h in U]
    if len(set(ukeys)) != len(U):
        print(f"note: {len(U) - len(set(ukeys))} frame lines share a key", file=sys.stderr)
    removed = {n: sum(1 for k in ukeys if k in s) for n, s in ex.items()}
    F0 = [h for h, k in zip(U, ukeys) if k not in union]
    perm = permute(F0, a.seed)
    (DATA / "frame").mkdir(parents=True, exist_ok=True)
    (DATA / "frame/F0_perm.txt").write_text("".join(h + "\n" for h in perm), encoding="utf-8")
    (DATA / "phase1_hosts.txt").write_text("".join(h + "\n" for h in perm[: a.n1]), encoding="utf-8")
    info = {
        "frame_source": str(FRAME_SRC), "frame_source_sha256": sha256_file(FRAME_SRC), "U": len(U),
        "removed_per_list": removed, "removed_union": len(U) - len(F0), "exclusion_keys": len(union),
        "N0": len(F0), "n1": a.n1, "seed": a.seed,
        "permutation": "sort by sha256(f'{seed}:{key}'), key = lower-case host without leading www.",
        "F0_perm_sha256": sha256_file(DATA / "frame/F0_perm.txt"),
        "phase1_hosts_sha256": sha256_file(DATA / "phase1_hosts.txt"),
    }
    (DATA / "frame/frame.json").write_text(json.dumps(info, indent=1) + "\n")
    md = ["# E53 frame F0 and phase-1 sample S1", "",
          f"- Frame source: `{FRAME_SRC}` (sha256 `{info['frame_source_sha256']}`), U = {len(U):,} sites.",
          f"- Exclusion keys (union of the lists, www-collapsed): {len(union):,}.",
          f"- Removed from U: {info['removed_union']:,}. **N0 = {len(F0):,}.**",
          f"- Permutation: {info['permutation']}, seed {a.seed}. Stored: `datasets/E53/frame/F0_perm.txt` "
          f"(sha256 `{info['F0_perm_sha256']}`).",
          f"- S1 = first n1 = {a.n1:,} of the permutation: `datasets/E53/phase1_hosts.txt` "
          f"(sha256 `{info['phase1_hosts_sha256']}`). A longer prefix extends S1 and stays an SRS of F0.",
          "", "| list | keys | removed from U |", "|---|---:|---:|"]
    md += [f"| {n} | {len(ex[n]):,} | {removed[n]:,} |" for n in LISTS]
    md += [f"| union | {len(union):,} | {info['removed_union']:,} |", ""]
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text("\n".join(md))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
