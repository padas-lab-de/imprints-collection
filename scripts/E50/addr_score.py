"""E50: address scorer. Reference and prediction rows go through one adapter (to_record), so a new reference
format (E51 address_spec.md, gold export) needs only new key aliases or a new branch in to_record.

Record = {"addresses": [{street, number, postcode, town, country, role, main, po_box}], "main_index": int | None,
          "no_address_reason": str | None}. "No address" = no main address.
E51 address_spec.md rows (role, street, number, postcode, town, country, po_box, modality, evidence;
main_address_index; no_address_reason) map directly: po_box is kept (true when the row says so or the street is a
P.O. box word such as "Postfach"), the main is main_address_index, and the reason is kept only without a main.
Accepted row shapes:
  {"addresses": [...], "main_address_index": i | "main_index": i | per-address "main"/"is_main": true, "no_address_reason"}
  {"address": {...} | null, "no_address_reason"}          (one address)
  {"street"/"streetname", "number"/"housenumber", "postcode"/"postalcode", "town"/"city", "country"} (one flat address)
  a nested "address" key holding any of these (address-task prediction lines from run.py are flat already).
Normalisation: case, whitespace, ß/ss, "str." -> "strasse", postcode digits only, country names to ISO codes for
DE/AT/CH; town compares equal when one normalised town starts with the other (Frankfurt / Frankfurt am Main).

Metrics (hosts in refs and preds; failed replies count as a predicted "no address"):
  main_*        field-level P/R/F1 on the main address (5 fields; a field counts when the ref or pred field is
                non-empty; tp = both non-empty and equal) and main_exact (street, number, postcode, town equal)
  all_*         addresses matched by key (postcode + street + number, then postcode + town), micro field P/R/F1,
                address-level P/R
  noaddr_*      P/R/F1 of "no address" (ref without main address), false_address_rate (= share of no-address refs
                with a predicted main address), missed_address_rate
  reason_acc    among refs without a main address: share of hosts whose prediction has no main address and the
                same no_address_reason (no_imprint | imprint_without_address)
  po_box_*      main_po_box_n (refs whose main is a P.O. box), main_po_box_ok (their main_ok)
  evidence      share of predicted main addresses whose postcode and street occur in the input text (needs texts)
    python3 scripts/E50/addr_score.py --refs results/E51/refs/address.jsonl results/E50/preds/dev/address/*.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

FIELDS = ("street", "number", "postcode", "town", "country")
ALIASES = {
    "street": ("street", "streetname", "street_name", "strasse", "straße"),
    "number": ("number", "housenumber", "house_number", "hausnummer", "nr"),
    "postcode": ("postcode", "postalcode", "postal_code", "zip", "plz"),
    "town": ("town", "city", "ort", "stadt", "locality"),
    "country": ("country", "land", "country_code"),
}
POBOX = re.compile(r"^\s*(postfach|pf\.?|p\.?\s*o\.?\s*box|case postale|casella postale|boite postale)\b", re.I)
COUNTRY = {"deutschland": "de", "germany": "de", "brd": "de", "d": "de", "osterreich": "at", "oesterreich": "at",
           "austria": "at", "a": "at", "schweiz": "ch", "switzerland": "ch", "suisse": "ch", "svizzera": "ch"}


def _get(d: dict, f: str) -> str:
    for k in ALIASES[f]:
        if k in d and d[k] is not None:
            return str(d[k]).strip()
    return ""


def _addr(d: dict) -> dict:
    a = {f: _get(d, f) for f in FIELDS}
    a["role"] = d.get("role") or "operator"
    a["main"] = bool(d.get("main") or d.get("is_main"))
    a["po_box"] = bool(d.get("po_box")) or bool(POBOX.match(a["street"]))
    return a


def to_record(row: dict | None) -> dict:
    if not row:
        return {"addresses": [], "main_index": None, "no_address_reason": None}
    reason = row.get("no_address_reason")
    if isinstance(row.get("addresses"), list):
        adds = [_addr(a) for a in row["addresses"] if isinstance(a, dict)]
        idx = row.get("main_index", row.get("main_address_index"))
        if not isinstance(idx, int) or not 0 <= idx < len(adds):
            idx = next((i for i, a in enumerate(adds) if a["main"]), None)
    elif "address" in row and (row["address"] is None or isinstance(row["address"], dict)):
        if isinstance(row["address"], dict) and any(k in row["address"] for k in ("addresses", "address")):
            return to_record(row["address"])
        adds = [_addr(row["address"])] if row["address"] else []
        idx = 0 if adds else None
    elif any(_get(row, f) for f in FIELDS):
        adds, idx = [_addr(row)], 0
    else:
        adds, idx = [], None
    adds = [a for a in adds if any(a[f] for f in FIELDS)] if idx is None else adds
    if idx is not None and not any(adds[idx][f] for f in FIELDS):
        idx = None
    return {"addresses": adds, "main_index": idx, "no_address_reason": None if idx is not None else reason}


def norm(f: str, v: str) -> str:
    v = unicodedata.normalize("NFKD", (v or "").lower().replace("ß", "ss"))
    v = "".join(c for c in v if not unicodedata.combining(c))
    if f == "postcode":
        return re.sub(r"\D", "", v)
    if f == "street":
        v = re.sub(r"str\.?(?=\s|$|-)", "strasse", v)
    if f == "country":
        v = re.sub(r"[^a-z]", "", v)
        return COUNTRY.get(v, v)
    return re.sub(r"[^a-z0-9]", "", v)


def field_eq(f: str, a: str, b: str) -> bool:
    x, y = norm(f, a), norm(f, b)
    if f == "town" and x and y:
        return x.startswith(y) or y.startswith(x)
    return x == y


def _fields(ref: dict | None, pred: dict | None, c: dict) -> None:
    for f in FIELDS:
        r, p = (ref or {}).get(f, ""), (pred or {}).get(f, "")
        c["ref"] += bool(norm(f, r))
        c["pred"] += bool(norm(f, p))
        c["tp"] += bool(norm(f, r)) and bool(norm(f, p)) and field_eq(f, r, p)


def _prf(tp, npred, nref) -> tuple:
    p = tp / npred if npred else None
    r = tp / nref if nref else None
    f = 2 * p * r / (p + r) if p and r else 0.0 if p is not None and r is not None else None
    return p, r, f


def _match(refs: list[dict], preds: list[dict]) -> list[tuple[int, int]]:
    pairs, used = [], set()
    for keys in (("postcode", "street", "number"), ("postcode", "town")):
        for i, r in enumerate(refs):
            if any(i == a for a, _ in pairs) or not norm("postcode", r["postcode"]):
                continue
            for j, p in enumerate(preds):
                if j not in used and all(field_eq(k, r[k], p[k]) for k in keys):
                    pairs.append((i, j))
                    used.add(j)
                    break
    return pairs


def score(refs: dict[str, dict], preds: dict[str, dict], texts: dict[str, str] | None = None) -> dict:
    hosts = sorted(set(refs) & set(preds))
    mc = {"tp": 0, "pred": 0, "ref": 0}
    ac = {"tp": 0, "pred": 0, "ref": 0}
    exact = n_both = 0
    a_tp = a_pred = a_ref = 0
    na = {"tp": 0, "fp": 0, "fn": 0, "ref_none": 0, "ref_some": 0}
    ev = [0, 0]
    per_host = {}
    for h in hosts:
        r, p = refs[h], preds[h]
        rm = r["addresses"][r["main_index"]] if r["main_index"] is not None else None
        pm = p["addresses"][p["main_index"]] if p["main_index"] is not None else None
        _fields(rm, pm, mc)
        ok = None
        if rm and pm:
            n_both += 1
            ok = all(field_eq(f, rm[f], pm[f]) for f in ("street", "number", "postcode", "town"))
            exact += ok
        na["ref_none"] += rm is None
        na["ref_some"] += rm is not None
        na["tp"] += rm is None and pm is None
        na["fp"] += rm is not None and pm is None
        na["fn"] += rm is None and pm is not None
        pairs = _match(r["addresses"], p["addresses"])
        for i, j in pairs:
            _fields(r["addresses"][i], p["addresses"][j], ac)
        for i in set(range(len(r["addresses"]))) - {i for i, _ in pairs}:
            _fields(r["addresses"][i], None, ac)
        for j in set(range(len(p["addresses"]))) - {j for _, j in pairs}:
            _fields(None, p["addresses"][j], ac)
        a_tp += len(pairs)
        a_pred += len(p["addresses"])
        a_ref += len(r["addresses"])
        if pm and texts and h in texts:
            t = norm("street", texts[h])
            ev[1] += 1
            ev[0] += (not pm["postcode"] or norm("postcode", pm["postcode"]) in re.sub(r"\D", "", texts[h])) and \
                (not pm["street"] or norm("street", pm["street"]).split("strasse")[0][:6] in t)
        per_host[h] = {"main_ok": bool(ok) if rm else pm is None, "ref_none": rm is None, "pred_none": pm is None,
                       "both_main": rm is not None and pm is not None, "exact": bool(ok),
                       "reason_ok": rm is None and pm is None and r["no_address_reason"] == p["no_address_reason"],
                       "ref_po_box": bool(rm and rm.get("po_box"))}
    mp, mr, mf = _prf(mc["tp"], mc["pred"], mc["ref"])
    ap_, ar, af = _prf(ac["tp"], ac["pred"], ac["ref"])
    npp, npr, npf = _prf(na["tp"], na["tp"] + na["fp"], na["tp"] + na["fn"])
    rnd = lambda v: None if v is None else round(v, 3)  # noqa: E731
    return {"n": len(hosts), "main_P": rnd(mp), "main_R": rnd(mr), "main_F1": rnd(mf),
            "main_exact": rnd(exact / n_both) if n_both else None,
            "main_ok": rnd(sum(v["main_ok"] for v in per_host.values()) / len(hosts)) if hosts else None,
            "all_P": rnd(ap_), "all_R": rnd(ar), "all_F1": rnd(af),
            "addr_P": rnd(a_tp / a_pred) if a_pred else None, "addr_R": rnd(a_tp / a_ref) if a_ref else None,
            "noaddr_P": rnd(npp), "noaddr_R": rnd(npr), "noaddr_F1": rnd(npf),
            "false_address_rate": rnd(na["fn"] / na["ref_none"]) if na["ref_none"] else None,
            "missed_address_rate": rnd(na["fp"] / na["ref_some"]) if na["ref_some"] else None,
            "reason_acc": rnd(sum(v["reason_ok"] for v in per_host.values()) / na["ref_none"]) if na["ref_none"] else None,
            "main_po_box_n": sum(v["ref_po_box"] for v in per_host.values()),
            "main_po_box_ok": rnd(sum(v["main_ok"] for v in per_host.values() if v["ref_po_box"]) /
                                  sum(v["ref_po_box"] for v in per_host.values()))
            if any(v["ref_po_box"] for v in per_host.values()) else None,
            "evidence": rnd(ev[0] / ev[1]) if ev[1] else None, "per_host": per_host}


def load(path, key: str | None = None) -> dict[str, dict]:
    out = {}
    for l in Path(path).read_text(encoding="utf-8").split("\n"):
        if l.strip():
            row = json.loads(l)
            out[row["host"]] = to_record(row.get(key) if key else row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--refs", required=True)
    ap.add_argument("--ref-key", default=None, help="key that holds the address part in a reference row")
    ap.add_argument("--pred-key", default=None, help="e.g. address for joint-run lines")
    ap.add_argument("--hosts", default=None, help="file with one host per line: score only these hosts")
    a = ap.parse_args()
    refs = load(a.refs, a.ref_key)
    if a.hosts:
        want = {l.strip() for l in Path(a.hosts).read_text(encoding="utf-8").splitlines() if l.strip()}
        refs = {h: r for h, r in refs.items() if h in want}
    for f in a.preds:
        m = score(refs, load(f, a.pred_key))
        m.pop("per_host")
        print(json.dumps({"run": Path(f).stem, **m}, ensure_ascii=False))


if __name__ == "__main__":
    main()
