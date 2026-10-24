"""E14 analysis: per-round yield, frontier, novelty. Usage: PYTHONPATH=src python scripts/E14/analyze.py > results/E14/analysis.txt
Rounds: 0 = E9 random 20k seeds, 1 = E10 expansion, 2/3 = datasets/E14/round{2,3}.
Frontier files (candidates.py output) are expected in datasets/E14/frontier{0,1,2,3}/ (frontier k = candidates from round k's
discovered hosts, excluding seed list and hosts fetched in rounds <= k).
"""
import gzip
import json
import math
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "E10"))
from analyze_lib import dach_country, grp, wilson

R = Path("/home/dinzinger/GitHub/imprints-collection")
ROUNDS = {
    0: (R / "datasets/E9/random20k/imprints_batch000000.jsonl.gz", R / "datasets/E4/random20k_seed_hosts.txt", R / "datasets/E9/random20k/discovered_external_hosts.txt"),
    1: (R / "datasets/E10/expansion/imprints_batch000000.jsonl.gz", R / "datasets/E10/candidate_hosts.txt", R / "datasets/E10/expansion/discovered_external_hosts.txt"),
}
for k in (2, 3):
    d = R / f"datasets/E14/round{k}"
    if d.exists():
        ROUNDS[k] = tuple([d / f for f in ("imprints_batch000000.jsonl.gz", "fetch_hosts.txt", "discovered_external_hosts.txt")])


def load_records(p):
    recs = {}
    # round dirs may hold several batch files
    files = sorted(p.parent.glob("imprints_batch*.jsonl.gz"))
    for fp in files:
        with gzip.open(fp, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                recs[r["host"]] = r
    return recs


STREET = re.compile(r"([A-ZÄÖÜ][A-Za-zäöüßÄÖÜ.\- ]{2,40}?(?:stra(?:ß|ss)e|str\.|weg|platz|allee|gasse|ring|damm|ufer|hof|markt|chaussee))\s*(\d+\s?[a-zA-Z]?)\b")
PLZ = re.compile(r"(?<!\d)(\d{4,5})\s+[A-ZÄÖÜ][a-zäöüß]{2,}")


def opkey(text):
    """Rough operator key: (postcode, street, house number); None if either is missing."""
    p = PLZ.search(text)
    s = STREET.search(text)
    if not p or not s:
        return None
    st = s.group(1).lower().replace("ß", "ss").replace("straße", "strasse").replace("str.", "strasse").replace(" ", "")
    return (p.group(1), st, s.group(2).replace(" ", "").lower())


def y(k, n):
    lo, hi = wilson(k, n)
    return f"{1000*k/n:.0f} ({1000*lo:.0f}-{1000*hi:.0f})"


seen_keys = set()
summary = {}
print("== Per round ==")
print("| Round | Fetched | Reachable | Found | Found/reach | Strict DACH | DACH/1,000 fetched (CI) | cc fetched | cc DACH | cc DACH/1,000 | other fetched | other DACH | other DACH/1,000 | .de | .at | .ch |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
novelty = []
for k, (jp, hp, dp) in sorted(ROUNDS.items()):
    fetched = [l.strip() for l in open(hp) if l.strip()]
    recs = load_records(jp)
    rows = []
    keys_here = []
    for h in fetched:
        r = recs.get(h)
        imp = r.get("impressum") if r else None
        text = imp.get("main_content", "") if imp else ""
        d = dach_country(text) if imp else None
        rows.append((h, grp(h), r is not None, imp is not None, d))
        if d:
            keys_here.append((h, opkey(text)))
    n = len(rows)
    reach = sum(x[2] for x in rows)
    found = sum(x[3] for x in rows)
    dach = sum(x[4] is not None for x in rows)
    cc = [x for x in rows if x[1] in ("de", "at", "ch")]
    ot = [x for x in rows if x[1] not in ("de", "at", "ch")]
    ccd = sum(x[4] is not None for x in cc)
    otd = sum(x[4] is not None for x in ot)
    per = {t: sum(1 for x in rows if x[1] == t and x[4] is not None) for t in ("de", "at", "ch")}
    print(f"| {k} | {n} | {reach} ({reach/n:.1%}) | {found} | {found/max(reach,1):.1%} | {dach} | {y(dach, n)} | {len(cc)} | {ccd} | {y(ccd, len(cc)) if cc else '-'} | {len(ot)} | {otd} | {y(otd, len(ot))} | {per['de']} | {per['at']} | {per['ch']} |")
    # novelty
    keyed = [kk for _, kk in keys_here if kk]
    dup_earlier = sum(1 for kk in keyed if kk in seen_keys)
    within = len(keyed) - len(set(keyed))
    novelty.append((k, dach, len(keyed), dup_earlier, within))
    summary[k] = dict(fetched=n, reach=reach, found=found, dach=dach)
    seen_keys |= set(keyed)
    # ccTLD vs other novelty of reached imprints skipped

print("\n== Novelty: round-k strict-DACH imprints vs operators seen in earlier rounds (same postcode + street + house number) ==")
print("| Round | DACH imprints | with key | key seen in earlier rounds | share | key repeated inside the round | new (no key or unseen) |")
print("|---|---|---|---|---|---|---|")
for k, dach, nk, de_, wi in novelty:
    print(f"| {k} | {dach} | {nk} ({nk/max(dach,1):.0%}) | {de_} | {de_/max(nk,1):.1%} | {wi} | {dach-de_} |")

print("\n== Frontier (new candidate hosts found from a round's landing pages) ==")
print("| Round k | Fetched | Reachable | Link lines | Unique hosts | In seed list | Already fetched earlier | New candidates (after platform/www) | per fetched host | per reachable host | cc share of candidates |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for k in range(4):
    fd = R / f"datasets/E14/frontier{k}/stats.json"
    if not fd.exists() or k not in summary:
        continue
    st = json.loads(fd.read_text())
    cands = [l.strip() for l in open(R / f"datasets/E14/frontier{k}/candidate_hosts.txt") if l.strip()]
    ccs = sum(1 for h in cands if grp(h) in ("de", "at", "ch"))
    s = summary[k]
    print(f"| {k} | {s['fetched']} | {s['reach']} | {st['lines']} | {st['unique']} | {st['in_seed']} | {st['already_fetched_earlier_rounds']} | {st['candidates']} | {st['candidates']/s['fetched']:.3f} | {st['candidates']/s['reach']:.3f} | {ccs/len(cands):.1%} ({ccs}) |")

print("\n== Heaps fit of unique new hosts vs parents fetched (per round) ==")
for k in range(4):
    fd = R / f"datasets/E14/frontier{k}"
    if not (fd / "candidate_hosts.txt").exists() or k not in summary:
        continue
    cset = {l.strip() for l in open(fd / "candidate_hosts.txt") if l.strip()}
    lines = [l.strip().lower() for l in open(ROUNDS[k][2]) if l.strip()]
    lines = [h for h in lines if h in cset]
    cnt = Counter(lines)
    single = sum(1 for c in cnt.values() if c == 1)
    double = sum(1 for c in cnt.values() if c == 2)
    chao = len(cnt) + single * single / (2 * max(double, 1))
    random.seed(1)
    random.shuffle(lines)
    N = summary[k]["fetched"]
    pts = []
    for fr in (0.0625, 0.125, 0.25, 0.5, 1.0):
        pts.append((N * fr, len(set(lines[: int(len(lines) * fr)]))))
    xs = [math.log(a) for a, _ in pts]
    ys = [math.log(b) for _, b in pts]
    mx, my = sum(xs) / 5, sum(ys) / 5
    beta = sum((x - mx) * (y_ - my) for x, y_ in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    c = math.exp(my - beta * mx)
    print(f"round {k}: {len(cnt)} unique candidates, singletons {single} ({single/len(cnt):.0%}), doubletons {double}, Chao1 {chao:,.0f}; "
          f"U = {c:.4f} * N^{beta:.3f}; points {[(int(a), b) for a, b in pts]}")
    summary[k].update(beta=beta, c=c, chao=chao, unique=len(cnt))
json.dump(summary, open(R / "results/E14/summary.json", "w"), indent=1)
