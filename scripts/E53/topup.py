"""E53 step 15: r5 top-up of the gold set (docs/gold_set_design.md 2.3).

Three subcommands, run from the repository root:

    python3 -I scripts/E53/topup.py draw --r5 <r5 canonical_sites_after_filter.txt>
    python3 -I scripts/E53/topup.py merge --capture-dir D --fetch-dir F1 [--fetch-dir F2] --fetch-vm aralie --fetch-tree 88b162a
    python3 -I scripts/E53/topup.py assign

draw
  F_A = r5 sites whose key is not in the frame source (r4 + E40 r2), minus the exclusion lists (union.txt).
  n_A = round(n_gold x N_A / N0) (lead 2026-11-14: the mean sampling fraction of the 1,869 gold items; the design
  text had 1,000). SRS of n_A from F_A: the first n_A of F_A sorted by sha256(f"{seed}:{key}") (common.permute),
  seed 20261114. pi = n_A / N_A, weight N_A / n_A, stratum "topup", the fields of gold_sample.jsonl.
  Folds: the top-up items go, in seeded random order, to the fold with the fewest remaining gold items (dropped
  items not counted), so the 5 folds stay even.
  Dropped: gold items whose key is not in r5. They leave the set (not replaced) and stay in gold_sample.jsonl;
  they are listed in dropped_r5.jsonl.
  Writes datasets/E53/topup_sample.jsonl, datasets/E53/dropped_r5.jsonl, datasets/E53/topup/hosts.txt,
  datasets/E53/topup/draw.json.

merge
  Copies the top-up capture dirs (<capture-dir>/<host>/, made by scripts/E53/capture.py) into datasets/E53/gold/<host>/
  (new dirs only; an existing item dir is an error), then adds the same-day `ic fetch` record and the "ic_fetch" meta
  block with scripts/E53/merge_fetch.py merge_item. Keeps the old manifest as manifest_pre_topup.sha256 and writes a
  new recursive manifest over all item dirs (scripts/E53/recapture_merge.py manifest).

assign
  Primary labels only for the top-up items (ic.gold.assignment.extend_assignment): no calibration, no second labels;
  lightest load relative to 2:1:1 first (dropped items not counted). Keeps the old file as assignment_pre_topup.jsonl;
  the new assignment.jsonl = old rows unchanged + new rows. Item numbers continue after the last gold item.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
from common import DATA, FRAME_SRC, norm_host, permute, sha256_file  # noqa: E402

SEED = 20261114
FOLDS = 5
STRATUM = "topup"


# ------------------------------------------------------------------------------------------------ draw (pure)
def read_lines(p: Path) -> list[str]:
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip()]


def added_frame(r5: list[str], frame_src: list[str], excl_keys: set[str]) -> list[str]:
    """F_A: r5 hosts whose key is neither in the frame source nor in the exclusion keys (first host per key)."""
    old = {norm_host(h) for h in frame_src}
    out, seen = [], set()
    for h in r5:
        k = norm_host(h)
        if k and k not in old and k not in excl_keys and k not in seen:
            seen.add(k)
            out.append(h)
    return out


def topup_size(n_gold: int, N_A: int, N0: int) -> int:
    """n_A = round(n_gold x N_A / N0), at most N_A (Python round: half to even)."""
    return min(N_A, round(n_gold * N_A / N0))


def draw_srs(F_A: list[str], n: int, seed: int = SEED) -> list[str]:
    """SRS of size n: the first n of the seeded permutation (any prefix of a uniform permutation is an SRS)."""
    return permute(F_A, seed)[:n]


def dropped_items(gold: list[dict], r5_keys: set[str]) -> list[dict]:
    return [g for g in gold if norm_host(g["host"]) not in r5_keys]


def topup_folds(
    hosts: list[str], fold_counts: Counter, seed: int = SEED, k: int = FOLDS
) -> dict[str, int]:
    """Deal hosts (seeded random order) to the fold with the fewest items; ties: lower fold number."""
    cnt = Counter({f: fold_counts.get(f, 0) for f in range(k)})
    order = sorted(hosts)
    random.Random(seed + 7).shuffle(order)
    out = {}
    for h in order:
        f = min(range(k), key=lambda x: (cnt[x], x))
        out[h] = f
        cnt[f] += 1
    return out


def topup_records(sample: list[str], N_A: int, folds: dict[str, int]) -> list[dict]:
    """Records with the fields of gold_sample.jsonl, sorted by host."""
    n = len(sample)
    pi = n / N_A
    return [
        {
            "M_h": N_A,
            "classes": [],
            "core": False,
            "fold": folds[h],
            "fold_group": STRATUM,
            "host": h,
            "m_h": n,
            "pi": pi,
            "selected_for": [STRATUM],
            "stratum": STRATUM,
            "weight": N_A / n,
        }
        for h in sorted(sample)
    ]


def cmd_draw(a) -> None:
    fr = json.load(open(a.frame_json))
    N0 = fr["N0"]
    r5_path = Path(a.r5)
    r5_sha = sha256_file(r5_path)
    if a.r5_sha256_prefix and not r5_sha.startswith(a.r5_sha256_prefix):
        sys.exit(f"r5 sha256 {r5_sha} does not start with {a.r5_sha256_prefix}")
    r5 = read_lines(r5_path)
    src = read_lines(Path(a.frame_src))
    excl = set(read_lines(Path(a.exclusions)))
    gold = [json.loads(l) for l in open(a.gold_sample, encoding="utf-8") if l.strip()]
    F_A = added_frame(r5, src, excl)
    N_A = len(F_A)
    n_A = topup_size(len(gold), N_A, N0)
    sample = draw_srs(F_A, n_A, a.seed)
    r5_keys = {norm_host(h) for h in r5}
    drop = dropped_items(gold, r5_keys)
    drop_hosts = {g["host"] for g in drop}
    folds = topup_folds(
        sample, Counter(g["fold"] for g in gold if g["host"] not in drop_hosts), a.seed
    )
    recs = topup_records(sample, N_A, folds)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    with open(a.dropped, "w", encoding="utf-8") as f:
        for g in sorted(drop, key=lambda g: g["host"]):
            f.write(
                json.dumps(
                    {
                        "host": g["host"],
                        "reason": "not_in_r5",
                        "stratum": g["stratum"],
                        "core": g["core"],
                        "fold": g["fold"],
                        "weight": g["weight"],
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    hosts_txt = Path(a.hosts_out)
    hosts_txt.parent.mkdir(parents=True, exist_ok=True)
    hosts_txt.write_text("".join(r["host"] + "\n" for r in recs), encoding="utf-8")
    old_keys = {norm_host(h) for h in src}
    info = {
        "r5_sha256": r5_sha,
        "r5_sites": len(r5),
        "frame_source_sha256": fr["frame_source_sha256"],
        "frame_source_sites": len(src),
        "r5_keys_not_in_frame_source": len(r5_keys - old_keys),
        "frame_source_keys_not_in_r5": len(old_keys - r5_keys),
        "excluded_from_added": len((r5_keys - old_keys) & excl),
        "N0": N0,
        "N_A": N_A,
        "n_gold": len(gold),
        "n_A": n_A,
        "n_A_exact": len(gold) * N_A / N0,
        "pi": n_A / N_A if N_A else None,
        "weight": N_A / n_A if n_A else None,
        "seed": a.seed,
        "permutation": "sort by sha256(f'{seed}:{key}'), key = lower-case host without leading www.",
        "dropped": len(drop),
        "dropped_hosts": sorted(drop_hosts),
        "topup_hosts": [r["host"] for r in recs],
        "topup_folds": dict(Counter(r["fold"] for r in recs)),
        "folds_after": dict(
            sorted(
                (
                    Counter(g["fold"] for g in gold if g["host"] not in drop_hosts)
                    + Counter(r["fold"] for r in recs)
                ).items()
            )
        ),
        "sha256": {
            "topup_sample.jsonl": sha256_file(out),
            "dropped_r5.jsonl": sha256_file(Path(a.dropped)),
            "gold_sample.jsonl": sha256_file(Path(a.gold_sample)),
        },
    }
    Path(a.info).parent.mkdir(parents=True, exist_ok=True)
    Path(a.info).write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in info.items() if k != "topup_hosts"}, indent=1))


# ------------------------------------------------------------------------------------------------ merge
def cmd_merge(a) -> None:
    import merge_fetch as MF
    import recapture_merge as RM

    gold, cap = Path(a.gold), Path(a.capture_dir)
    hosts = [
        json.loads(l)["host"] for l in open(a.sample, encoding="utf-8") if l.strip()
    ]
    clash = [h for h in hosts if (gold / MF.safe(h)).exists()]
    if clash:
        sys.exit(f"item dirs exist already: {clash}")
    man_old = gold / "manifest.sha256"
    keep = gold / "manifest_pre_topup.sha256"
    if keep.exists():
        sys.exit(f"{keep} exists; the top-up merge has run before")
    shutil.copy2(man_old, keep)
    dirs = [Path(d) for d in a.fetch_dir]
    rows, recs = MF.read_status(dirs), MF.read_records(dirs)
    c: Counter = Counter()
    for h in hosts:
        src, dst = cap / MF.safe(h), gold / MF.safe(h)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.mkdir(parents=True)
        mp = dst / "meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else None
        line, m = MF.merge_item(
            h, rows.get(h), recs.get(h), meta, a.fetch_vm, a.fetch_tree
        )
        (dst / "ic_fetch.jsonl").write_text(json.dumps(line) + "\n", encoding="utf-8")
        mp.write_text(
            json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8"
        )
        s = (
            "strato"
            if m.get("strato") or (m.get("dns") or {}).get("strato")
            else "other"
        )
        c[f"fetch:{m['ic_fetch']['class']}"] += 1
        c[f"fetch_status:{m['ic_fetch']['status']}"] += 1
        c[f"capture:{m.get('outcome', 'missing')}"] += 1
        c[f"{s}:n"] += 1
        c["input_day_mismatch"] += m["input_day_mismatch"]
        for b in m.get("consent_banner") or []:
            c[f"banner:{b.get('page')}:{b.get('action')}"] += 1
    all_hosts = sorted(p.parent.name for p in gold.glob("*/meta.json"))
    man = RM.manifest(gold, all_hosts)
    man_old.write_text(man)
    out = {
        "topup_items": len(hosts),
        "counts": dict(sorted(c.items())),
        "item_dirs": len(all_hosts),
        "manifest_files": man.count("\n"),
        "manifest_sha256": hashlib.sha256(man.encode()).hexdigest(),
        "manifest_pre_topup_sha256": sha256_file(keep),
    }
    if a.summary:
        Path(a.summary).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


# ------------------------------------------------------------------------------------------------ assign
def cmd_assign(a) -> None:
    from ic.gold.assignment import LABELLERS, extend_assignment, labeller_loads

    gold = Path(a.gold)
    cur, keep = gold / "assignment.jsonl", gold / "assignment_pre_topup.jsonl"
    if keep.exists():
        sys.exit(f"{keep} exists; the top-up assignment has run before")
    rows = [json.loads(l) for l in open(cur, encoding="utf-8") if l.strip()]
    top = [json.loads(l)["host"] for l in open(a.sample, encoding="utf-8") if l.strip()]
    drop = [
        json.loads(l)["host"] for l in open(a.dropped, encoding="utf-8") if l.strip()
    ]
    first = max(r["item"] for r in rows) + 1
    new_items = [{"item": first + k, "host": h} for k, h in enumerate(top)]
    new = extend_assignment(rows, new_items, a.seed, skip_hosts=drop)
    shutil.copy2(cur, keep)
    with open(cur, "w", encoding="utf-8", newline="\n") as f:
        for r in sorted(rows + new, key=lambda r: (r["labeller"], r["order"])):
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    before = labeller_loads(rows)
    before_net = labeller_loads(rows, drop)
    after_net = labeller_loads(rows + new, drop)
    out = {
        "seed": a.seed,
        "new_rows": len(new),
        "items": [first, first + len(top) - 1] if top else [],
        "new_per_labeller": dict(Counter(r["labeller"] for r in new)),
        "loads_before": before,
        "loads_before_without_dropped": before_net,
        "loads_after_without_dropped": after_net,
        "loads_after_all_rows": labeller_loads(rows + new),
        "dropped_rows": {lab: before[lab] - before_net[lab] for lab in LABELLERS},
        "sha256": {
            "assignment.jsonl": sha256_file(cur),
            "assignment_pre_topup.jsonl": sha256_file(keep),
        },
    }
    if a.summary:
        Path(a.summary).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draw")
    d.add_argument(
        "--r5", required=True, help="final r5 canonical_sites_after_filter.txt"
    )
    d.add_argument("--r5-sha256-prefix", default="93bd4d30")
    d.add_argument("--frame-src", default=str(FRAME_SRC))
    d.add_argument("--frame-json", default=str(DATA / "frame/frame.json"))
    d.add_argument("--exclusions", default=str(DATA / "exclusions/union.txt"))
    d.add_argument("--gold-sample", default=str(DATA / "phase2/gold_sample.jsonl"))
    d.add_argument("--seed", type=int, default=SEED)
    d.add_argument("--out", default=str(DATA / "topup_sample.jsonl"))
    d.add_argument("--dropped", default=str(DATA / "dropped_r5.jsonl"))
    d.add_argument("--hosts-out", default=str(DATA / "topup/hosts.txt"))
    d.add_argument("--info", default=str(DATA / "topup/draw.json"))
    m = sub.add_parser("merge")
    m.add_argument("--sample", default=str(DATA / "topup_sample.jsonl"))
    m.add_argument("--gold", default=str(DATA / "gold"))
    m.add_argument("--capture-dir", required=True)
    m.add_argument("--fetch-dir", action="append", required=True)
    m.add_argument("--fetch-vm", required=True)
    m.add_argument("--fetch-tree", required=True)
    m.add_argument("--summary", default=str(DATA / "topup/merge_summary.json"))
    s = sub.add_parser("assign")
    s.add_argument("--sample", default=str(DATA / "topup_sample.jsonl"))
    s.add_argument("--dropped", default=str(DATA / "dropped_r5.jsonl"))
    s.add_argument("--gold", default=str(DATA / "gold"))
    s.add_argument("--seed", type=int, default=SEED)
    s.add_argument("--summary", default=str(DATA / "topup/assign_summary.json"))
    a = ap.parse_args()
    {"draw": cmd_draw, "merge": cmd_merge, "assign": cmd_assign}[a.cmd](a)


if __name__ == "__main__":
    main()
