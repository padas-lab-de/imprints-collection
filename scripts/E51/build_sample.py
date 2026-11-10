"""E51: draw 500 non-gold imprint hosts from the E16 snapshot crawl and write model inputs.

Source: `ic fetch` output of E16 (seed crawl of the snapshot), copied read-only to
/home/dinzinger/imprints-raw-vm/E16/<vm>/seeds/{fetch_status,imprints}_batch*.{tsv,jsonl.gz}.
Pool: every host with status imprint_found in a fetch_status file, minus the gold pool
(host dirs in datasets/gold, assignment.jsonl, deferred_strato.txt) and the E49 dev and
held-out hosts. Hosts are compared after lower-casing and stripping a leading "www.".
No other filter (parked, empty, non-German and no-address hosts stay in).

Sampling: sorted pool, random.Random(SEED).shuffle; walk the order and keep a host when
its record in imprints_batch*.jsonl.gz has an "impressum" page (else count it as skipped).
First 300 kept = dev2, next 200 = heldout2.

Inputs: same cleaning and budget as scripts/E49/build_dev.py (clean_text, 6,000 chars).

    python3 -I scripts/E51/build_sample.py --root . [--seed 51]
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path("/home/dinzinger/imprints-raw-vm/E16")
MAIN = Path("/home/dinzinger/GitLab/fim/imprints-collection")
BUDGET = 6_000


def clean_text(txt: str, budget: int = BUDGET) -> str:
    """Copy of scripts/E49/build_dev.py clean_text (kept identical)."""
    out, seen = [], set()
    for line in txt.splitlines():
        line = re.sub(r"[ \t ​]+", " ", line).strip()
        if not line:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    s = "\n".join(out)
    if len(s) > budget:
        s = s[:budget].rsplit("\n", 1)[0] if "\n" in s[budget - 300:budget] else s[:budget]
    return s


def norm_host(h: str) -> str:
    h = h.strip().lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def exclusion_set(main: Path) -> set[str]:
    gold = main / "datasets/gold"
    ex = {d.name for d in gold.iterdir() if d.is_dir() and d.name != "labels"}
    for l in (gold / "assignment.jsonl").open(encoding="utf-8"):
        if l.strip():
            ex.add(json.loads(l)["host"])
    for p in (gold / "deferred_strato.txt", main / "results/E49/dev_hosts.txt",
              main / "results/E49/heldout/hosts.txt"):
        ex |= {l.strip() for l in p.open(encoding="utf-8") if l.strip()}
    return {norm_host(h) for h in ex}


def pool(raw: Path) -> dict[str, tuple[Path, str]]:
    """host -> (imprints file, batch id) for imprint_found hosts (first occurrence wins, sorted files)."""
    out: dict[str, tuple[Path, str]] = {}
    for f in sorted(raw.glob("*/seeds/fetch_status_batch*.tsv")):
        b = f.name[len("fetch_status_batch"):-4]
        imp = f.parent / f"imprints_batch{b}.jsonl.gz"
        for line in f.open(encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) > 1 and p[1] == "imprint_found" and p[0] not in out:
                out[p[0]] = (imp, f"{f.parts[-3]}/{b}")
    return out


def record(r: dict, origin: str) -> dict:
    m, i = r.get("main") or {}, r.get("impressum") or {}
    home_raw, imp_raw = m.get("main_content") or "", i.get("main_content") or ""
    home, imp = clean_text(home_raw), clean_text(imp_raw)
    return {
        "host": r["host"],
        "homepage_text": home,
        "imprint_text": imp,
        "meta": {
            "source": "E16",
            "origin": origin,
            "final_url": m.get("url"),
            "imprint_url": i.get("url"),
            "title": (m.get("title") or "")[:300],
            "description": (m.get("description") or "")[:500],
            "lang": m.get("content_language") or "",
            "imprint_lang": i.get("content_language") or "",
            "found_by": i.get("found_by"),
            "fallback_extraction": i.get("fallback_extraction"),
            "has_imprint_text": bool(imp),
            "homepage_chars_raw": len(home_raw),
            "homepage_chars": len(home),
            "imprint_chars_raw": len(imp_raw),
            "imprint_chars": len(imp),
            "homepage_truncated": len(clean_text(home_raw, 10**9)) > BUDGET,
            "imprint_truncated": len(clean_text(imp_raw, 10**9)) > BUDGET,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--raw", default=str(RAW))
    ap.add_argument("--main", default=str(MAIN), help="main checkout with datasets/gold and results/E49")
    ap.add_argument("--seed", type=int, default=51)
    ap.add_argument("--n-dev", type=int, default=300)
    ap.add_argument("--n-heldout", type=int, default=200)
    a = ap.parse_args()
    root = Path(a.root)
    ex = exclusion_set(Path(a.main))
    pl = pool(Path(a.raw))
    n_pool_all = len(pl)
    hosts = sorted(h for h in pl if norm_host(h) not in ex)
    rng = random.Random(a.seed)
    rng.shuffle(hosts)
    need = a.n_dev + a.n_heldout
    # look ahead in the order: read candidates by imprints file, keep order
    cand = hosts[: need * 2]
    by_file = defaultdict(set)
    for h in cand:
        by_file[pl[h][0]].add(h)
    recs: dict[str, dict] = {}
    for f, hs in sorted(by_file.items()):
        with gzip.open(f, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not any(f'"{h}"' in line[:400] for h in hs):
                    continue
                r = json.loads(line)
                if r.get("host") in hs and r["host"] not in recs:
                    recs[r["host"]] = r
    kept, skipped = [], []
    for h in cand:
        r = recs.get(h)
        if r is None or "impressum" not in r:
            skipped.append((h, "no record" if r is None else "no impressum page"))
            continue
        kept.append(record(r, pl[h][1]))
        if len(kept) == need:
            break
    assert len(kept) == need, len(kept)
    split = {"dev2": kept[: a.n_dev], "heldout2": kept[a.n_dev:]}
    (root / "datasets/E51").mkdir(parents=True, exist_ok=True)
    (root / "results/E51").mkdir(parents=True, exist_ok=True)
    stats = {"seed": a.seed, "pool_imprint_found": n_pool_all, "excluded": n_pool_all - len(hosts),
             "pool_after_exclusion": len(hosts), "skipped_before_500": skipped}
    for name, rs in split.items():
        rs = sorted(rs, key=lambda r: r["host"])
        with open(root / f"datasets/E51/{name}_inputs.jsonl", "w", encoding="utf-8") as f:
            for r in rs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        (root / f"results/E51/{name}_hosts.txt").write_text("".join(r["host"] + "\n" for r in rs))
        hl = sorted(r["meta"]["homepage_chars"] for r in rs)
        il = sorted(r["meta"]["imprint_chars"] for r in rs)
        q = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]  # noqa: E731
        stats[name] = {
            "n": len(rs),
            "homepage_empty": sum(not r["homepage_text"] for r in rs),
            "homepage_lt300": sum(r["meta"]["homepage_chars"] < 300 for r in rs),
            "imprint_empty": sum(not r["imprint_text"] for r in rs),
            "homepage_chars_p10_p50_p90": [q(hl, .1), q(hl, .5), q(hl, .9)],
            "imprint_chars_p10_p50_p90": [q(il, .1), q(il, .5), q(il, .9)],
            "homepage_truncated": sum(r["meta"]["homepage_truncated"] for r in rs),
            "imprint_truncated": sum(r["meta"]["imprint_truncated"] for r in rs),
            "lang": Counter(r["meta"]["lang"] or "?" for r in rs).most_common(8),
            "tld": Counter(r["host"].rsplit(".", 1)[-1] for r in rs).most_common(8),
            "found_by": Counter(str(r["meta"]["found_by"]) for r in rs).most_common(),
        }
    out = json.dumps(stats, ensure_ascii=False, indent=1)
    (root / "results/E51/sample_stats.json").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    sys.exit(main())
