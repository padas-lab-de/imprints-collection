"""E21-gold-prefill: suggested labels for the labelling tool.

Rule part, from each capture's meta.json (no model): site status, imprint URL and location.
Model part, from the captured landing and imprint text: addresses (role, fields, verbatim
evidence), main address, operator type, topic. The model is one that the paper does NOT
compare (D24), so the pre-fill cannot favour a compared model.

Writes <data-dir>/prefill.jsonl, one line per host: {"host", "source", "label", "error"}.
Resumable: hosts already in the output are skipped. Stdlib only.

    python3 scripts/gold/e21_prefill.py --model qwen-agentworld-35b-a3b --workers 8
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from ic.gold.annotate import schema  # noqa: E402

PROMPT_VERSION = "e21-v1+filter1"
LANDING_CHARS = 8_000
IMPRINT_CHARS = 16_000

SYSTEM = """You pre-fill labels for German website imprints (Impressum). Answer with one JSON object only.
Copy every address field VERBATIM from the text (same spelling, no corrections, no expansion).
Fields:
- imprint_present: true if the text contains an imprint / legal notice (Impressum, Anbieterkennzeichnung, legal notice), else false.
- addresses: postal addresses in the imprint, in order of appearance. Each:
  {"role": one of operator, operator_other_site, representative, editor, agency, host, other,
   "street", "number", "postcode", "town", "country" (only if written; else ""),
   "po_box": true for Postfach / P.O. box,
   "evidence": the address lines exactly as written, one line per line}.
  operator = the site's provider (Anbieter, Betreiber, Diensteanbieter). representative = Vertretungsberechtigter,
  Geschäftsführer, Vorstand with own address. editor = V.i.S.d.P. / redaktionell verantwortlich.
  agency = web designer, host = hosting company, other = anything else (data protection officer, chamber, ...).
  Do NOT list banks, courts, register courts, supervisory authorities or chambers mentioned only by name.
- main_address: index (0-based) of the operator's address in addresses, or null.
- operator_type: one of corporate, association, public_body, sole_trader, private_person, unclear.
- topic: the website's topic, judged on the landing page, one of: %s.
""" % ", ".join(schema.TOPICS)


def load_env(path: Path) -> dict:
    env = {}
    for line in path.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Z_]+)\s*=\s*(.*)", line)
        if m:
            env[m.group(1)] = m.group(2).strip().strip("'\"")
    return {k: re.sub(r"\$\{(\w+)\}", lambda m: env.get(m.group(1), ""), v) for k, v in env.items()}


def reg_domain(host: str) -> str:
    parts = (host or "").lower().removeprefix("www.").split(".")
    return ".".join(parts[-2:])


def rule_part(host: str, meta: dict) -> dict:
    """Suggestions that need no model."""
    out: dict = {}
    st = meta.get("site_status_at_capture")
    if st in schema.SITE_STATUS:
        out["site_status"] = st
    imp = meta.get("imprint") if isinstance(meta.get("imprint"), dict) else None
    if meta.get("outcome") == "landing+imprint" and imp:
        url = imp.get("final_url") or imp.get("url") or ""
        out["imprint_present"] = True
        out["imprint_url"] = url
        if imp.get("pdf"):
            out["imprint_location"] = "pdf"
        elif url and reg_domain(urlparse(url).hostname or "") != reg_domain(host):
            out["imprint_location"] = "other_domain"
        else:
            out["imprint_location"] = "separate_page"
    return out


def ask(env: dict, model: str, user: str) -> dict:
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 2_000,
        "reasoning_effort": "none",  # otherwise the reasoning uses up max_tokens
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        env["MODEL_API_ENDPOINT"].rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + env["MODEL_API_KEY"], "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                txt = json.load(r)["choices"][0]["message"]["content"] or ""
            # first object only (the model sometimes repeats it), raw tabs/newlines in strings allowed
            return json.JSONDecoder(strict=False).raw_decode(txt[max(txt.find("{"), 0):])[0]
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    return {}


def _n(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def verbatim(b: dict, texts: str) -> list[str]:
    """Make the address verbatim where the text allows it; return fields still not found.
    Evidence: only lines found in the text, cut after the postcode line (plus a country line).
    Town: re-read from the evidence's postcode line (the model sometimes expands it)."""
    hay = _n(texts)
    lines = [l.strip() for l in b["evidence"].splitlines() if l.strip() and _n(l) in hay]
    cut = next((i for i, l in enumerate(lines) if b["postcode"] and b["postcode"] in l), None)
    if cut is not None:
        keep = lines[: cut + 1]
        if cut + 1 < len(lines) and b["country"] and _n(lines[cut + 1]) == _n(b["country"]):
            keep.append(lines[cut + 1])
        lines = keep
    b["evidence"] = "\n".join(lines)
    pm = next((re.search(r"\b(\d{4,5})\s+(.+?)\s*$", l) for l in lines if b["postcode"] and b["postcode"] in l), None)
    if pm and pm.group(1) == b["postcode"]:  # the town as written in the address itself
        b["town"] = pm.group(2).split(",")[0].strip()
    return [k for k in ("street", "number", "postcode", "town", "country", "evidence") if b[k] and _n(b[k]) not in hay] + (
        ["evidence"] if not b["evidence"] else [])


THIRD_PARTY = ("bank", "sparkasse", "volksbank", "bafin", "bundesanstalt", "ihk", "industrie- und handelskammer",
               "handwerkskammer", "schlichtungsstelle", "ombudsmann", "amtsgericht", "google")


def filter_addresses(addrs: list[dict], mi, counts: dict | None = None) -> tuple[list[dict], int | None]:
    """Drop junk rows (no postcode unless po_box or a street with a house number, exact duplicates, non-operator-role rows whose evidence names a third party).
    Return the kept rows and the remapped main index (fallback: first kept row with a main role)."""
    counts = counts if counts is not None else {}
    kept, seen, new_mi = [], {}, None
    for i, b in enumerate(addrs):
        key = tuple(_n(b[k]) for k in ("street", "number", "postcode", "town"))
        if not b["postcode"] and not b["po_box"] and not (b["street"] and (b["number"] or re.search(r"\d", b["street"]))):
            rule = "no_postcode"
        elif key in seen:
            rule = "duplicate"
            if i == mi:  # the main row's twin stays; it takes over the main role
                new_mi = seen[key]
                if kept[new_mi]["role"] not in schema.MAIN_ROLES and b["role"] in schema.MAIN_ROLES:
                    kept[new_mi]["role"] = b["role"]
        elif b["role"] not in schema.MAIN_ROLES and any(t in b["evidence"].lower() for t in THIRD_PARTY):
            rule = "third_party"
        else:
            rule = None
        if rule:
            counts[rule] = counts.get(rule, 0) + 1
            continue
        seen[key] = len(kept)
        if i == mi:
            new_mi = len(kept)
        kept.append(b)
    if mi is not None and new_mi is None:
        new_mi = next((j for j, b in enumerate(kept) if b["role"] in schema.MAIN_ROLES), None)
    return kept, new_mi


def clean_model(ans: dict, texts: str) -> dict:
    """Keep only schema-valid values; drop addresses with nothing usable."""
    out: dict = {}
    if isinstance(ans.get("imprint_present"), bool):
        out["imprint_present"] = ans["imprint_present"]
    addrs = []
    for a in ans.get("addresses") or []:
        if not isinstance(a, dict):
            continue
        b = schema.empty_address()
        for k in ("street", "number", "postcode", "town", "country"):
            b[k] = str(a.get(k) or "").strip()
        ev = a.get("evidence") or ""
        b["evidence"] = "\n".join(ev) if isinstance(ev, list) else str(ev).strip()
        b["role"] = a.get("role") if a.get("role") in schema.ROLES else "other"
        b["po_box"] = bool(a.get("po_box"))
        if b["street"] or b["postcode"] or b["town"]:
            b["check"] = verbatim(b, texts)
            addrs.append(b)
    mi = ans.get("main_address")
    if not (isinstance(mi, int) and not isinstance(mi, bool) and 0 <= mi < len(addrs) and addrs[mi]["role"] in schema.MAIN_ROLES):
        mi = None
    out["addresses"], mi = filter_addresses(addrs, mi)
    if mi is not None:
        out["main_address_index"] = mi
    if ans.get("operator_type") in schema.OPERATOR_TYPE:
        out["operator_type"] = ans["operator_type"]
    if ans.get("topic") in schema.TOPICS:
        out["topic"] = ans["topic"]
    return out


def one(env: dict, model: str, d: Path) -> dict:
    host = d.name
    meta = {}
    if (d / "meta.json").is_file():
        try:
            meta = json.loads((d / "meta.json").read_text())
        except json.JSONDecodeError:
            pass
    label = rule_part(host, meta)
    rec = {"host": host, "source": {"model": model, "prompt": PROMPT_VERSION,
                                    "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
           "label": label, "error": None}
    if label.get("site_status") not in schema.LIVE_LIKE:
        return rec
    land = (d / "landing.txt").read_text(errors="replace")[:LANDING_CHARS] if (d / "landing.txt").is_file() else ""
    imp = (d / "imprint.txt").read_text(errors="replace")[:IMPRINT_CHARS] if (d / "imprint.txt").is_file() else ""
    if not (land or imp):
        return rec
    user = f"Host: {host}\n\n=== LANDING PAGE TEXT ===\n{land}\n\n=== IMPRINT PAGE TEXT ===\n{imp or '(no separate imprint page captured; the imprint may be on the landing page)'}"
    try:
        m = clean_model(ask(env, model, user), land + "\n" + imp)
    except Exception as e:  # keep the rule part; the labeller fills the rest
        rec["error"] = f"{type(e).__name__}: {e}"[:300]
        return rec
    if "imprint_present" in label:  # the capture found an imprint page: trust the capture
        m.pop("imprint_present", None)
    elif m.get("imprint_present") is True:
        label["imprint_location"] = "landing_page"
    elif m.get("imprint_present") is False:
        label["imprint_location"] = "none"
        m["addresses"] = []
    label.update(m)
    return rec


def refilter(path: Path) -> None:
    """Apply filter_addresses to an existing prefill file in place (atomic), without calling the model."""
    counts: dict = {}
    before = [0, 0]  # hosts with an address, rows
    after = [0, 0]
    changed, vanished = [], []
    lines = []
    for l in path.open(encoding="utf-8"):
        if not l.strip():
            continue
        rec = json.loads(l)
        lab = rec["label"]
        old = lab.get("addresses") or []
        before[0] += bool(old)
        before[1] += len(old)
        if old:
            omi = lab.get("main_address_index")
            kept, mi = filter_addresses(old, omi, counts)
            lab["addresses"] = kept
            if mi is None:
                lab.pop("main_address_index", None)
            else:
                lab["main_address_index"] = mi
            if omi is not None and (mi is None or kept[mi] != old[omi]):
                (vanished if mi is None else changed).append(rec["host"])
        after[0] += bool(lab.get("addresses"))
        after[1] += len(lab.get("addresses") or [])
        rec["source"]["prompt"] = PROMPT_VERSION
        lines.append(json.dumps(rec, ensure_ascii=False))
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(json.dumps({"hosts_with_address": [before[0], after[0]], "rows": [before[1], after[1]], "dropped": counts,
                      "main_changed": len(changed), "main_vanished": len(vanished),
                      "changed_hosts": changed, "vanished_hosts": vanished}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="datasets/gold")
    ap.add_argument("--model", default="qwen-agentworld-35b-a3b")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--env", default=".env")
    ap.add_argument("--refilter", action="store_true", help="re-apply the address filters to prefill.jsonl, no model calls")
    a = ap.parse_args()
    if a.refilter:
        refilter(Path(a.data_dir) / "prefill.jsonl")
        return
    env = load_env(Path(a.env))
    data = Path(a.data_dir)
    out = data / "prefill.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["host"] for l in out.open() if l.strip()}
    hosts = sorted({json.loads(l)["host"] for l in (data / "assignment.jsonl").open() if l.strip()} - done)
    if a.limit:
        hosts = hosts[: a.limit]
    print(f"{len(hosts)} hosts to do ({len(done)} done), model {a.model}", flush=True)
    lock = threading.Lock()
    n = [0, 0]
    with open(out, "a", encoding="utf-8") as f, ThreadPoolExecutor(a.workers) as ex:
        for rec in ex.map(lambda h: one(env, a.model, data / h), hosts):
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                n[0] += 1
                n[1] += bool(rec["error"])
                if n[0] % 50 == 0:
                    print(f"{n[0]}/{len(hosts)} errors {n[1]}", flush=True)
    print(f"done {n[0]}, errors {n[1]} -> {out}", flush=True)


if __name__ == "__main__":
    main()
