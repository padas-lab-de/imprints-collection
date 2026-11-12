"""E53 step 3c: one screen record per S1 site (both models' predictions, detector flags, free fields, strata).

    python3 -I scripts/E53/features.py [--preds datasets/E53/screen/preds]

Reads datasets/E53/screen/inputs.jsonl and the six prediction files of screen_run.sh. Sites count as screened
when all six predictions exist (partial runs: only those sites). Writes datasets/E53/screen/screen_features.jsonl.

Strata (memberships; "union" = either model):
  poi1:<L1>  poi2:<L2>               POI v3 path of the model's main node
  wz1:<section> wz2:<division> wz3:<group>   WZ 2025 canonical path (single-child chains extended)
  addr:at addr:ch   model main address with AT/CH country word, or a 4-digit postcode resolved to AT/CH by a country
                    word in the imprint text or the TLD; or a detector address with country hint AT/CH
  addr:po_box       detector P.O. box, or a model street "Postfach"/"P.O. Box"
  addr:none         imprint text present, no model main address (both models) and no detector address
  addr:multi        detector finds >= 2 distinct postal locations
  addr:non_dach     a model main address with a country word outside DE/AT/CH
  lang:non_de       content_language of the landing page or the imprint known and not German
  input:no_imprint_text  (descriptive) imprint text empty
Model-specific membership lists are kept per model (m:gemma, m:qwen) for the coverage report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/E49"))
sys.path.insert(0, str(ROOT / "src"))
from common import DATA  # noqa: E402
from tree import load_schema  # noqa: E402

from ic.gold.detectors import address_flags, find_addresses, tld_class  # noqa: E402

MODELS = {"gemma": "gemma4-31b-it", "qwen": "qwen38-27b"}
TAGS = {
    "poi3": {"gemma": "retrieve__gemma__r-short", "qwen": "retrieve__qwen__r-low"},
    "wz": {"gemma": "retrieve__gemma__r-none__c1500", "qwen": "retrieve__qwen__r-none__c1500"},
    "address": {"gemma": "address__gemma__r-none__f-schema__mode-main",
                "qwen": "address__qwen__r-none__f-schema__mode-main"},
}
AT_WORDS = re.compile(r"(ö|oe)sterreich|austria|\bAT\b|\bA\b", re.I)
CH_WORDS = re.compile(r"schweiz|switzerland|suisse|svizzera|\bCH\b", re.I)
DE_WORDS = re.compile(r"deutschland|germany|\bDE\b|\bD\b|\bBRD\b|allemagne", re.I)
POBOX = re.compile(r"postfach|p\.?\s?o\.?\s?box|postbox|postlagernd", re.I)
GERMAN = {"deu", "de", "ger", "german"}


def read_preds(p: Path) -> dict:
    out = {}
    if p.exists():
        with p.open(encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    r = json.loads(l)
                    out[r["host"]] = r
    return out


def country_of(addr: dict, imprint: str, host: str) -> str:
    """DE | AT | CH | OTHER | '' (unknown) for a model main address."""
    c = (addr.get("country") or "").strip()
    if c:
        if CH_WORDS.search(c):
            return "CH"
        if AT_WORDS.search(c):
            return "AT"
        if DE_WORDS.search(c):
            return "DE"
        return "OTHER"
    pc = re.sub(r"\D", "", addr.get("postcode") or "")
    if len(pc) == 5:
        return "DE"
    if len(pc) == 4:
        at, ch = bool(re.search(r"(ö|oe)sterreich|austria", imprint, re.I)), bool(
            re.search(r"schweiz|switzerland|suisse|svizzera", imprint, re.I))
        if at != ch:
            return "AT" if at else "CH"
        t = tld_class(host)
        if t in ("at", "ch"):
            return t.upper()
        return "AT_or_CH"
    return ""


def topic_classes(pred: dict | None, tree, kind: str) -> list[str]:
    if not pred or not pred.get("main"):
        return []
    path = tree.canonical_path(pred["main"]) if kind == "wz" else tree.path(pred["main"])
    pre = "poi" if kind == "poi3" else "wz"
    depth = 2 if kind == "poi3" else 3
    return [f"{pre}{i + 1}:{n}" for i, n in enumerate(path[:depth])]


def main_address(pred: dict | None) -> dict | None:
    if not pred or pred.get("main_index") is None:
        return None
    a = pred.get("addresses") or []
    i = pred["main_index"]
    return a[i] if 0 <= i < len(a) else None


def site_record(inp: dict, preds: dict, trees: dict) -> dict:
    h = inp["host"]
    imp = inp.get("imprint_text") or ""
    meta = inp.get("meta") or {}
    hits = find_addresses(imp)
    fl = address_flags(hits)
    det_c = set(fl["address_countries"])
    per_model, errors, addr_out = {}, {}, {}
    for s, m in MODELS.items():
        ms = []
        ms += topic_classes(preds["poi3"][s].get(h), trees["poi3"], "poi3")
        ms += topic_classes(preds["wz"][s].get(h), trees["wz"], "wz")
        pa = preds["address"][s].get(h) or {}
        a = main_address(pa)
        c = country_of(a, imp, h) if a else ""
        if c in ("AT", "CH"):
            ms.append("addr:" + c.lower())
        if c == "OTHER":
            ms.append("addr:non_dach")
        if a and (POBOX.search(a.get("street") or "") or POBOX.search(a.get("number") or "")):
            ms.append("addr:po_box")
        per_model[s] = ms
        errors[s] = {k: (preds[k][s].get(h) or {}).get("error") for k in ("poi3", "wz", "address")}
        addr_out[s] = {"main": a, "country": c, "no_address_reason": pa.get("no_address_reason")}
    det = []
    if "AT" in det_c:
        det.append("addr:at")
    if "CH" in det_c:
        det.append("addr:ch")
    if "AT_or_CH" in det_c:
        t = tld_class(h)
        if t in ("at", "ch"):
            det.append("addr:" + t)
    if fl["po_box"]:
        det.append("addr:po_box")
    if fl["multi_address"]:
        det.append("addr:multi")
    if imp and not hits and not any(addr_out[s]["main"] for s in MODELS):
        det.append("addr:none")
    if not imp:
        det.append("input:no_imprint_text")
    langs = [meta.get("lang") or "", meta.get("imprint_lang") or ""]
    if any(l and l.lower() not in GERMAN for l in langs):
        det.append("lang:non_de")
    union = sorted(set(per_model["gemma"]) | set(per_model["qwen"]) | set(det))
    return {
        "host": h, "strata": union, "strata_model": per_model, "strata_detector": sorted(set(det)),
        "errors": errors, "address": addr_out,
        "detector": {k: fl[k] for k in ("n_addresses", "n_distinct_locations", "multi_address", "po_box",
                                        "address_countries")},
        "free": {"tld": tld_class(h), "source": meta.get("source"), "lang": meta.get("lang"),
                 "imprint_lang": meta.get("imprint_lang"), "homepage_chars": meta.get("homepage_chars"),
                 "imprint_chars": meta.get("imprint_chars"), "found_by": meta.get("found_by"),
                 "match": meta.get("match")},
        "pred": {k: {s: (preds[k][s].get(h) or {}).get("main") for s in MODELS} for k in ("poi3", "wz")},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=str(DATA / "screen/inputs.jsonl"))
    ap.add_argument("--preds", default=str(DATA / "screen/preds"))
    ap.add_argument("--out", default=str(DATA / "screen/screen_features.jsonl"))
    a = ap.parse_args()
    trees = {"poi3": load_schema("poi3"), "wz": load_schema("wz")}
    preds = {k: {s: read_preds(Path(a.preds) / k / f"{t}.jsonl") for s, t in v.items()} for k, v in TAGS.items()}
    n_in = n_out = 0
    with open(a.inputs, encoding="utf-8") as f, open(a.out, "w", encoding="utf-8") as g:
        for l in f:
            if not l.strip():
                continue
            inp = json.loads(l)
            n_in += 1
            if not all(inp["host"] in preds[k][s] for k in TAGS for s in MODELS):
                continue
            g.write(json.dumps(site_record(inp, preds, trees), ensure_ascii=False) + "\n")
            n_out += 1
    print(json.dumps({"inputs": n_in, "screened": n_out, **{f"{k}_{s}": len(preds[k][s]) for k in TAGS
                                                            for s in MODELS}}))


if __name__ == "__main__":
    main()
