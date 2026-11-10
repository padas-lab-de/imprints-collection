"""E50: address extraction with an output that can say "no address" and can hold several addresses.

Output (mode "list"):
  {"addresses": [{"street", "number", "postcode", "town", "country", "role", "main"}], "no_address_reason": null}
Output (mode "main"):
  {"address": {"street", "number", "postcode", "town", "country"} | null, "no_address_reason": null}
no_address_reason: null | "no_imprint" | "imprint_without_address" (gold guideline 3.4; site_dead is not a model
decision). Roles and field rules follow docs/annotation_guideline.md 3.1-3.3.

cfg keys (topic.E50_DEFAULTS + these): mode list|main, addr_input imprint|both, wording base|minimal, fmt, lang,
reasoning, site_chars. Hosts without imprint text and addr_input imprint: no call, prediction no_imprint.
predict() returns {"addresses": [...], "main_index": int | None, "no_address_reason": ..., "usage", "error"}.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import topic as TP  # noqa: E402
from llm import Usage2  # noqa: E402

FIELDS = ("street", "number", "postcode", "town", "country")
ROLES = ("operator", "operator_other_site", "representative", "editor", "agency", "host", "other")
REASONS = ("no_imprint", "imprint_without_address")

TXT = {
    "de": {
        "task": "Du extrahierst Postadressen aus dem Impressum einer Website.",
        "rules_list": (
            "Liste jede Postadresse einer Partei, die im Impressum genannt ist, einmal, mit ihrer Rolle: operator "
            "(Anbieter/Betreiber nach § 5 DDG/TMG, Herausgeber, Inhaber), operator_other_site (Betreiberadresse aus "
            "einem Impressum auf einer anderen Domain), representative (Vertreter mit eigener Adresse), editor "
            "(Verantwortlicher für den Inhalt mit eigener Adresse), agency (Webagentur, Designer, Fotograf), host "
            "(Hoster), other (weiterer Standort, Filiale). Liste keine Adressen von Banken, Gerichten, Aufsichtsbehörden, "
            "Kammern, Schlichtungsstellen, Versicherungen oder Finanzämtern. Liste keine E-Mail-Adressen, Telefonnummern "
            "oder Links."),
        "rules_main": (
            "Gib nur die Hauptadresse an: die Adresse der Partei, die für die Website verantwortlich ist."),
        "main": (
            "Hauptadresse: die Adresse im Block des Anbieters (§ 5 DDG/TMG, „Angaben gemäß“, „Anbieter“); hat der "
            "Betreiber mehrere Adressen, die als Sitz markierte, sonst die erste Postanschrift (nicht das Postfach); "
            "hat der Betreiber keine Adresse: Vertreter, dann Verantwortlicher. agency, host und other sind nie die "
            "Hauptadresse."),
        "fields": (
            "Felder: Kopiere wie geschrieben, korrigiere und ergänze nichts. street = nur der Straßenname (ohne "
            "Hausnummer, ohne c/o und Firmenzeilen; bei Postfach „Postfach“); number = Hausnummer wie geschrieben "
            "(„12a“, „3-5“), leer wenn keine; postcode = nur Ziffern (ohne D-, A-, CH-); town = Ort wie geschrieben, "
            "mit Zusätzen; country = Land nur wenn genannt, sonst leer."),
        "none": (
            "Keine Adresse: no_address_reason = „no_imprint“, wenn der Text kein Impressum ist; "
            "„imprint_without_address“, wenn das Impressum keine Postadresse des Betreibers nennt (nur E-Mail, "
            "Telefon, Formular oder nur Adressen von Agentur oder Hoster). Sonst null. Eine Teiladresse (nur PLZ und "
            "Ort) ist eine Adresse."),
        "minimal": "Extrahiere die Postadresse des Betreibers der Website aus dem Impressum. Antworte nur mit einem JSON-Objekt.",
        "json": "Antworte nur mit einem JSON-Objekt.",
        "ans_list": ('Antwortformat: {{{reason}"addresses": [{{"street": "<Straße>", "number": "<Hausnummer>", '
                     '"postcode": "<PLZ>", "town": "<Ort>", "country": "<Land oder leer>", "role": "<Rolle>", '
                     '"main": <true oder false>}}], "no_address_reason": <null, "no_imprint" oder '
                     '"imprint_without_address">}}'),
        "ans_main": ('Antwortformat: {{{reason}"address": {{"street": "<Straße>", "number": "<Hausnummer>", '
                     '"postcode": "<PLZ>", "town": "<Ort>", "country": "<Land oder leer>"}} oder null, '
                     '"no_address_reason": <null, "no_imprint" oder "imprint_without_address">}}'),
    },
    "en": {
        "task": "You extract postal addresses from the imprint (Impressum) of a website.",
        "rules_list": (
            "List each postal address of a party named in the imprint once, with its role: operator (provider under "
            "§ 5 DDG/TMG, publisher, owner), operator_other_site (operator address from an imprint on another domain), "
            "representative (representative with an own address), editor (person responsible for the content with an "
            "own address), agency (web agency, designer, photographer), host (hosting provider), other (further site, "
            "branch). Do not list addresses of banks, courts, supervisory authorities, chambers, arbitration boards, "
            "insurers or tax offices. Do not list e-mail addresses, phone numbers or links."),
        "rules_main": "Give only the main address: the address of the party responsible for the website.",
        "main": (
            "Main address: the address in the provider block (§ 5 DDG/TMG, \"Angaben gemäß\", \"Anbieter\"); if the "
            "operator has several addresses, the one marked as seat (Sitz), else the first postal address (not the "
            "P.O. box); if the operator has no address: representative, then editor. agency, host and other are never "
            "the main address."),
        "fields": (
            "Fields: copy as written, do not correct or complete. street = street name only (no house number, no c/o "
            "or company lines; for a P.O. box \"Postfach\"); number = house number as written (\"12a\", \"3-5\"), empty "
            "if none; postcode = digits only (no D-, A-, CH-); town = town as written, with additions; country = "
            "country only if named, else empty."),
        "none": (
            "No address: no_address_reason = \"no_imprint\" if the text is not an imprint; \"imprint_without_address\" "
            "if the imprint gives no postal address of the operator (only e-mail, phone, form, or only agency or host "
            "addresses). Else null. A partial address (postcode and town only) is an address."),
        "minimal": "Extract the postal address of the website operator from the imprint. Answer with one JSON object only.",
        "json": "Answer with one JSON object only.",
        "ans_list": ('Answer format: {{{reason}"addresses": [{{"street": "<street>", "number": "<house number>", '
                     '"postcode": "<postcode>", "town": "<town>", "country": "<country or empty>", "role": "<role>", '
                     '"main": <true or false>}}], "no_address_reason": <null, "no_imprint" or '
                     '"imprint_without_address">}}'),
        "ans_main": ('Answer format: {{{reason}"address": {{"street": "<street>", "number": "<house number>", '
                     '"postcode": "<postcode>", "town": "<town>", "country": "<country or empty>"}} or null, '
                     '"no_address_reason": <null, "no_imprint" or "imprint_without_address">}}'),
    },
}


def full_cfg(**kw) -> dict:
    kw.setdefault("mode", "list")
    kw.setdefault("addr_input", "imprint")
    return TP.full_cfg(**kw)


def rules_text(cfg) -> str:
    """Instruction block (also used inside the joint prompt)."""
    t = TXT[cfg["lang"]]
    if cfg["wording"] == "minimal":
        return t["minimal"]
    lst = cfg["mode"] == "list"
    return "\n".join([t["task"], t["rules_list"] if lst else t["rules_main"], t["main"] if lst else "", t["fields"],
                      t["none"], t["json"]]).replace("\n\n", "\n")


def answer_spec(cfg) -> str:
    t = TXT[cfg["lang"]]
    reason = TP.S.tx(cfg, "reason") if cfg["reason"] == "short" else ""
    return t["ans_list" if cfg["mode"] == "list" else "ans_main"].format(reason=reason)


def _addr_props(with_role: bool) -> dict:
    p = {f: {"type": "string"} for f in FIELDS}
    if with_role:
        p["role"] = {"type": "string", "enum": list(ROLES)}
        p["main"] = {"type": "boolean"}
    return {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}


def schema_props(cfg) -> dict:
    """JSON-schema properties of the address part (same keys and order as the answer format)."""
    props: dict = {}
    if cfg["mode"] == "list":
        props["addresses"] = {"type": "array", "items": _addr_props(True)}
    else:
        props["address"] = {"anyOf": [_addr_props(False), {"type": "null"}]}
    props["no_address_reason"] = {"anyOf": [{"type": "string", "enum": list(REASONS)}, {"type": "null"}]}
    return props


def response_format(cfg) -> dict | None:
    if cfg["fmt"] != "schema":
        return TP.response_format(cfg, [])
    props = {"begruendung": {"type": "string"}} if cfg["reason"] == "short" else {}
    props.update(schema_props(cfg))
    return {"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": {
        "type": "object", "properties": props, "required": list(props), "additionalProperties": False}}}


def input_text(rec: dict, cfg) -> str | None:
    if cfg["addr_input"] == "both":
        return TP.site_text(rec, dict(cfg, input="both"))
    return TP.site_text(rec, dict(cfg, input="imprint"))


def messages(rec: dict, cfg) -> list[dict] | None:
    txt = input_text(rec, cfg)
    if txt is None:
        return None
    return [{"role": "system", "content": rules_text(cfg)}, {"role": "user", "content": f"{txt}\n\n{answer_spec(cfg)}"}]


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def parse(ans: dict, mode: str = "list") -> dict:
    """Model answer -> {addresses: [{fields, role, main}], main_index, no_address_reason}."""
    reason = ans.get("no_address_reason")
    reason = reason if reason in REASONS else None
    if mode == "main" or "address" in ans and "addresses" not in ans:
        a = ans.get("address")
        rows = [a] if isinstance(a, dict) else []
        out = [dict({f: _s(r.get(f)) for f in FIELDS}, role="operator", main=True) for r in rows]
    else:
        rows = [r for r in (ans.get("addresses") or []) if isinstance(r, dict)]
        out = [dict({f: _s(r.get(f)) for f in FIELDS}, role=r.get("role") if r.get("role") in ROLES else "other",
                    main=r.get("main") is True) for r in rows]
    out = [r for r in out if any(r[f] for f in FIELDS)]
    main = next((i for i, r in enumerate(out) if r["main"]), None)
    if main is None and reason is None:  # no main flag: first operator-like address
        main = next((i for i, r in enumerate(out) if r["role"] in ("operator", "operator_other_site")), None)
    if main is not None:
        for i, r in enumerate(out):
            r["main"] = i == main
    if main is not None and reason is not None:
        reason = None  # an address marked main wins over a contradicting reason
    if main is None and reason is None:
        reason = "imprint_without_address"
    return {"addresses": out, "main_index": main, "no_address_reason": reason}


def predict(llm, model: str, rec: dict, cfg) -> dict:
    usage = Usage2()
    out = {"addresses": [], "main_index": None, "no_address_reason": None, "error": None}
    try:
        msgs = messages(rec, cfg)
        if msgs is None:
            out["no_address_reason"] = "no_imprint"
        else:
            ans, _ = llm.chat2(model, msgs, usage, max_tokens=900 if cfg["reason"] == "none" else 1200,
                               reasoning=cfg["reasoning"], response_format=response_format(cfg),
                               temperature=cfg["temperature"], seed=cfg["seed"])
            out.update(parse(ans, cfg["mode"]))
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"[:300]
    out["usage"] = usage.as_dict()
    return out
