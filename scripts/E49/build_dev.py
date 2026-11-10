"""E49: draw the dev sample (200 live gold hosts with usable landing text) and write the model inputs.

Eligible: site_status_at_capture == live and cleaned landing text >= MIN_HOME chars.
Sampling (seed 49), light stratification: by the E21 pre-fill topic (old 10-topic schema), each topic
gets max(MIN_PER_TOPIC, proportional share); the rest is filled at random. Within a topic, random.

Writes
  datasets/E49/dev_inputs.jsonl  {host, homepage_text, imprint_text, meta}
  results/E49/dev_hosts.txt      one host per line (sorted)
Stdlib only.

    python3 scripts/E49/build_dev.py
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

GOLD = Path("/home/dinzinger/GitLab/fim/imprints-collection/datasets/gold")
BUDGET = 6_000
MIN_HOME = 300
MIN_PER_TOPIC = 5


def clean_text(txt: str, budget: int = BUDGET) -> str:
    """Strip lines, drop empty and repeated lines (menus repeat in footers), collapse spaces, truncate."""
    out, seen = [], set()
    for line in txt.splitlines():
        line = re.sub(r"[ \t ​]+", " ", line).strip()
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


def head_meta(p: Path) -> dict:
    """Title and meta description from a captured HTML file."""
    if not p.is_file():
        return {}
    raw = p.read_bytes()[:400_000].decode("utf-8", errors="replace")
    out = {}
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    if m:
        out["title"] = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:300]
    for m in re.finditer(r"<meta\b[^>]*>", raw, re.I):
        tag = m.group(0)
        if re.search(r"""(name|property)\s*=\s*["'](description|og:description)["']""", tag, re.I):
            c = re.search(r"""content\s*=\s*(["'])(.*?)\1""", tag, re.S | re.I)
            if c and c.group(2).strip():
                out["description"] = html.unescape(re.sub(r"\s+", " ", c.group(2))).strip()[:500]
                break
    lm = re.search(r"<html[^>]*\blang\s*=\s*[\"']?([A-Za-z-]+)", raw, re.I)
    if lm:
        out["lang"] = lm.group(1).lower()
    return out


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def build_record(d: Path, prefill: dict) -> dict | None:
    try:
        meta = json.loads(read(d / "meta.json") or "{}")
    except json.JSONDecodeError:
        return None
    if meta.get("site_status_at_capture") != "live":
        return None
    home_raw = read(d / "landing.txt")
    home = clean_text(home_raw)
    if len(home) < MIN_HOME:
        return None
    imp_raw = read(d / "imprint.txt")
    imp = clean_text(imp_raw)
    hm = head_meta(d / "landing.static.html") or head_meta(d / "landing.dom.html")
    pf = (prefill.get(d.name) or {}).get("label", {})
    land = meta.get("landing") or {}
    return {
        "host": d.name,
        "homepage_text": home,
        "imprint_text": imp,
        "meta": {
            "item": meta.get("item"),
            "final_url": land.get("render_final_url") or land.get("url"),
            "title": hm.get("title", ""),
            "description": hm.get("description", ""),
            "lang": hm.get("lang", ""),
            "outcome": meta.get("outcome"),
            "has_imprint_text": bool(imp),
            "imprint_location": pf.get("imprint_location"),
            "homepage_chars_raw": len(home_raw),
            "homepage_chars": len(home),
            "imprint_chars_raw": len(imp_raw),
            "imprint_chars": len(imp),
            "homepage_truncated": len(clean_text(home_raw, 10**9)) > BUDGET,
            "prefill_topic": pf.get("topic"),
        },
    }


def sample(recs: list[dict], n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    recs = sorted(recs, key=lambda r: r["host"])
    rng.shuffle(recs)
    by = defaultdict(list)
    for r in recs:
        by[r["meta"]["prefill_topic"] or "none"].append(r)
    total = len(recs)
    quota = {t: min(len(v), max(MIN_PER_TOPIC, round(n * len(v) / total))) for t, v in by.items()}
    while sum(quota.values()) > n:  # trim the largest quota (the minimum lifts small topics above share)
        t = max(quota, key=lambda k: (quota[k], k))
        quota[t] -= 1
    picked = [r for t in sorted(by) for r in by[t][: quota[t]]]
    hosts = {r["host"] for r in picked}
    picked += [r for r in recs if r["host"] not in hosts][: n - len(picked)]
    return sorted(picked[:n], key=lambda r: r["host"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=str(GOLD))
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=49)
    ap.add_argument("--out", default="datasets/E49/dev_inputs.jsonl")
    ap.add_argument("--hosts-out", default="results/E49/dev_hosts.txt")
    ap.add_argument("--exclude", default=None, help="file with hosts to leave out of the eligible set (held-out sample)")
    a = ap.parse_args()
    gold = Path(a.gold)
    prefill = {}
    if (gold / "prefill.jsonl").is_file():
        for l in (gold / "prefill.jsonl").open(encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                prefill[r["host"]] = r
    recs = [r for d in sorted(gold.iterdir()) if d.is_dir() and (r := build_record(d, prefill))]
    if a.exclude:
        skip = {l.strip() for l in open(a.exclude) if l.strip()}
        recs = [r for r in recs if r["host"] not in skip]
    dev = sample(recs, a.n, a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.hosts_out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in dev:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path(a.hosts_out).write_text("".join(r["host"] + "\n" for r in dev))
    hl = sorted(r["meta"]["homepage_chars"] for r in dev)
    il = sorted(r["meta"]["imprint_chars"] for r in dev if r["meta"]["has_imprint_text"])
    q = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None  # noqa: E731
    print(json.dumps({
        "eligible": len(recs), "dev": len(dev),
        "with_imprint_text": sum(r["meta"]["has_imprint_text"] for r in dev),
        "homepage_chars_p10_p50_p90": [q(hl, .1), q(hl, .5), q(hl, .9)],
        "homepage_truncated": sum(r["meta"]["homepage_truncated"] for r in dev),
        "imprint_chars_p10_p50_p90": [q(il, .1), q(il, .5), q(il, .9)],
        "lang": Counter((r["meta"]["lang"] or "?")[:2] for r in dev).most_common(8),
        "prefill_topic_dev": Counter(r["meta"]["prefill_topic"] for r in dev).most_common(),
        "prefill_topic_eligible": Counter(r["meta"]["prefill_topic"] for r in recs).most_common(),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
