"""E12: screening prevalences (vs. E8) and the 1,000-item gold sample draw.

  prevalence  results/E12/screening_features.jsonl (+ results/E8/pilot_features.jsonl)
              -> results/E12/screening_prevalence.md
  draw        -> datasets/E12/gold_sample.jsonl, results/E12/gold_sample_quotas.md,
                 results/E12/gold_sample_info.json

Run from the repository root: PYTHONPATH=src python scripts/gold/e12_sample.py prevalence|draw
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from ic.gold.sampling import (
    IMAGE_ONLY,
    draw_sample,
    has_imprint,
    has_text_address,
    is_live,
    marginal_counts,
    memberships,
    newcombe_diff,
    wilson,
)

ROOT = Path(os.environ.get("IC_DATA_ROOT", "/home/dinzinger/GitHub/imprints-collection"))
DATA = ROOT / "datasets" / "E12"
RES = ROOT / "results" / "E12"
E8_FEATURES = ROOT / "results" / "E8" / "pilot_features.jsonl"
DRAW_SEED = 20261025
N_TOTAL = 1000
CORE_RANGE = (600, 700)
TARGET_RANGE = (20, 30)
CAPS = {IMAGE_ONLY: 20}


def load(p: Path) -> list:
    return [json.loads(l) for l in open(p) if l.strip()]


def image_only_confirmed() -> set:
    p = DATA / "image_only_confirmed.txt"
    if not p.exists():
        return set()
    return {l.split("#")[0].strip() for l in open(p) if l.split("#")[0].strip()}


# ---------------------------------------------------------------------------
def _neg(r):
    if not has_imprint(r):
        return "no_imprint"
    return "imprint_with_address" if has_text_address(r) else "imprint_no_address"


def _country(r):
    cs = set(r.get("address_countries") or [])
    if "DE" in cs:
        return "DE"
    if cs & {"AT", "CH", "AT_or_CH"}:
        return "AT/CH"
    return "none"


SECTIONS = [
    ("site_status", "all", lambda r: r["site_status"]),
    ("tld", "all", lambda r: r["tld"]),
    ("tld", "live", lambda r: r["tld"]),
    ("tech_family", "live", lambda r: r["tech_family"]),
    ("tech", "live", lambda r: r["tech"]),
    ("server_lang", "live", lambda r: r["server_lang"]),
    ("age_bin", "all", lambda r: r["age_bin"]),
    ("age_bin", "live", lambda r: r["age_bin"]),
    ("rendering_need", "live", lambda r: r["rendering_need"]),
    ("imprint_location", "live", lambda r: r["imprint_location"]),
    ("imprint_pdf", "live", lambda r: r["imprint_pdf"]),
    ("negatives: imprint / address", "live", _neg),
    ("model_operator_type", "imp", lambda r: r["model_operator_type"]),
    ("model_topic", "live", lambda r: r["model_topic"]),
    ("model_topic", "imp", lambda r: r["model_topic"]),
    ("model multi (>=2 addresses)", "imp", lambda r: (r.get("model_n_addresses") or 0) >= 2),
    ("rule multi_address", "imp", lambda r: r["multi_address"]),
    ("multi (rule or model)", "imp", lambda r: bool(r["multi_address"] or (r.get("model_n_addresses") or 0) >= 2)),
    ("rule po_box", "imp", lambda r: r["po_box"]),
    ("obfuscation any", "imp", lambda r: bool(r["obfuscation"])),
    ("country_group", "imp", _country),
    ("screenshot_candidate", "imp", lambda r: r["screenshot_candidate"]),
    ("image_only_address (vision, unchecked)", "imp", lambda r: r["image_only_address"]),
    ("no imprint by TLD group", "live_dach", lambda r: not has_imprint(r)),
    ("no imprint by TLD group", "live_other", lambda r: not has_imprint(r)),
]
BASES = {
    "all": ("all", lambda r: True),
    "live": ("live", is_live),
    "imp": ("live w/ imprint", has_imprint),
    "live_dach": ("live .de/.at/.ch", lambda r: is_live(r) and r["tld"] in ("de", "at", "ch")),
    "live_other": ("live other TLDs", lambda r: is_live(r) and r["tld"] not in ("de", "at", "ch")),
}


def stage_prevalence(_args):
    a = load(RES / "screening_features.jsonl")
    b = load(E8_FEATURES)
    lines = [
        "# E12 screening prevalences (10,000 random seed hosts) vs. E8 pilot (1,000)",
        "",
        "Wilson 95% CIs. Diff = E12 - E8 in pp with Newcombe hybrid-score 95% CI; `*` marks a difference whose CI excludes 0.",
        "Bases: all hosts; live = site_status live; live w/ imprint = live and the detectors reached an imprint.",
        "E12 adds a retry of 403/429/503 hosts after a pause and runs at <= 1 concurrent request per provider (/24).",
        "Vision ran on image-only candidates only in E12 (on all imprint screenshots in E8), so `image_only_address` None counts differ by design.",
        "",
    ]
    flagged = []
    for name, base, fn in SECTIONS:
        bl, bf = BASES[base]
        sa = [r for r in a if bf(r)]
        sb = [r for r in b if bf(r)]
        ca, cb = Counter(str(fn(r)) for r in sa), Counter(str(fn(r)) for r in sb)
        lines += [f"### {name} ({bl}) (E12 N={len(sa)}, E8 N={len(sb)})", "",
                  "| value | E12 n | E12 % | E12 CI | E8 n | E8 % | diff pp | diff CI |", "|---|---|---|---|---|---|---|---|"]
        for v in sorted(set(ca) | set(cb), key=lambda v: (-ca.get(v, 0), v)):
            ka, kb = ca.get(v, 0), cb.get(v, 0)
            lo, hi = wilson(ka, len(sa))
            d, dlo, dhi = newcombe_diff(ka, len(sa), kb, len(sb))
            star = "*" if (dlo > 0 or dhi < 0) else ""
            lines.append(
                f"| {v} | {ka} | {100*ka/max(1,len(sa)):.1f} | {100*lo:.1f}-{100*hi:.1f} | {kb} | {100*kb/max(1,len(sb)):.1f} "
                f"| {100*d:+.1f}{star} | {100*dlo:+.1f} to {100*dhi:+.1f} |"
            )
            if star:
                flagged.append(f"- {name} ({bl}) = {v}: E12 {100*ka/max(1,len(sa)):.1f}% vs E8 {100*kb/max(1,len(sb)):.1f}% (diff {100*d:+.1f} pp, CI {100*dlo:+.1f} to {100*dhi:+.1f})")
        lines.append("")
    head = lines[:7] + ["## Differences vs. E8 whose CI excludes 0", ""] + (flagged or ["- none"]) + [""]
    (RES / "screening_prevalence.md").write_text("\n".join(head + lines[7:]) + "\n")
    print("\n".join(flagged))


# ---------------------------------------------------------------------------
def stage_draw(args):
    recs = load(RES / "screening_features.jsonl")
    frame = json.loads((DATA / "frame.json").read_text())
    img = image_only_confirmed()
    items, info = draw_sample(recs, CORE_RANGE, N_TOTAL, frame["frame_hosts"], DRAW_SEED, TARGET_RANGE, CAPS, img)
    feats = {r["host"]: r for r in recs}
    with open(DATA / "gold_sample.jsonl", "w") as f:
        for i, it in enumerate(items):
            r = feats[it["host"]]
            it = {"item": i, **it, "tld": r["tld"], "site_status": r["site_status"], "final_url": r["final_url"]}
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    info["image_only_confirmed"] = sorted(img)
    (RES / "gold_sample_info.json").write_text(json.dumps(info, indent=1))
    # quota table
    screened = marginal_counts([{"strata": memberships(r, img)} for r in recs])
    n_imp = sum(1 for r in recs if has_imprint(r) or (is_live(r) and r["host"] in img))
    marg = marginal_counts(items)
    core_marg = marginal_counts([it for it in items if it["core"]])
    prio_cnt = Counter(it["priority_stratum"] for it in items)
    rows = ["| Stratum | Screened (of 10,000) | % (of screened w/ imprint; negatives: of all) | Expected in core | Target | In sample | of which core | Priority-stratum items (m_h / M_h) | pi phase 2 |",
            "|---|---|---|---|---|---|---|---|---|"]
    keys = info["order"] + sorted(k for k in info["M"] if k not in info["order"])
    for s in keys:
        M = info["M"].get(s, 0)
        m = info["m"].get(s, 0)
        tgt = "core only" if s.startswith("neg:") or s.startswith("other:") else str(min(info["target"], CAPS.get(s, 10**9)))
        n_scr = screened.get(s, 0)
        base = len(recs) if s.startswith(("neg:", "other:")) else n_imp
        rows.append(
            f"| {s} | {n_scr} | {100*n_scr/max(1,base):.1f} | {n_scr*info['n_core']/len(recs):.1f} | {tgt} | {marg.get(s,0)} | {core_marg.get(s,0)} "
            f"| {m} / {M} | {m/M if M else 0:.4f} |"
        )
    txt = [
        "# E12 gold sample: quota table",
        "",
        f"Screening sample {len(recs)} hosts from a frame of {frame['frame_hosts']:,}; core {info['n_core']} (SRS); oversample {len(items)-info['n_core']}; total {len(items)}.",
        f"Common target T = {info['target']} per coverage stratum (later passes up to {info['last_pass_target']}); image-only cap {CAPS[IMAGE_ONLY]}; seed {DRAW_SEED}.",
        f"Screened hosts with an imprint: {n_imp}. 'Expected in core' = screened count x n_core / 10,000.",
        "",
    ] + rows + ["", "Items per priority stratum: " + ", ".join(f"{k} {v}" for k, v in prio_cnt.most_common())]
    (RES / "gold_sample_quotas.md").write_text("\n".join(txt) + "\n")
    print("\n".join(txt[:5]))
    print(f"n_core={info['n_core']} T={info['target']} total={len(items)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["prevalence", "draw"])
    a = ap.parse_args()
    {"prevalence": stage_prevalence, "draw": stage_draw}[a.stage](a)


if __name__ == "__main__":
    main()
