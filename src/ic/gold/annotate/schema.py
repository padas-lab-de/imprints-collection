"""Label schema (docs/gold_set_design.md section 4) and validation.

Pure functions, no I/O. ``validate_label`` returns a list of error strings
(empty list = valid); ``normalise_label`` returns a cleaned copy.
"""

from __future__ import annotations

import re

SITE_STATUS = (
    "live",
    "unreachable",
    "http_error",
    "parked",
    "redirect_other_domain",
    "not_a_website",
)
IMPRINT_LOCATION = (
    "separate_page",
    "landing_page",
    "modal",
    "other_domain",
    "pdf",
    "none",
)
ROLES = (
    "operator",
    "operator_other_site",
    "representative",
    "editor",
    "agency",
    "host",
    "other",
)
# roles that may be the main address (the party responsible for the site)
MAIN_ROLES = ("operator", "operator_other_site", "representative", "editor")
MODALITY = ("text", "image", "pdf", "js_only")
NO_ADDRESS_REASON = ("no_imprint", "imprint_without_address", "site_dead")
OPERATOR_TYPE = (
    "corporate",
    "association",
    "public_body",
    "sole_trader",
    "private_person",
    "unclear",
)
TOPICS = (
    "Arts and Entertainment",
    "Business and Professional Services",
    "Community and Government",
    "Dining and Drinking",
    "Event",
    "Health and Medicine",
    "Landmarks and Outdoors",
    "Nightlife Spot",
    "Retail",
    "Sports and Recreation",
    "Travel and Transportation",
)
FLAGS = (
    "multi_address",
    "po_box",
    "obfuscated",
    "non_dach",
    "capture_problem",  # capture broken or incomplete
    "used_live_site",  # had to open the live site (say why in comment)
)
LABELLERS = ("L1", "L2", "L3")
# statuses labelled in full (a real website is shown; redirect: label the site you land on)
LIVE_LIKE = ("live", "redirect_other_domain")

ADDRESS_TEXT_FIELDS = ("street", "number", "postcode", "town", "country", "evidence")
_LABELLER_RE = re.compile(r"^L\d+$")


def empty_address() -> dict:
    return {
        "role": "operator",
        "street": "",
        "number": "",
        "postcode": "",
        "town": "",
        "country": "",
        "po_box": False,
        "modality": "text",
        "evidence": "",
    }


def _s(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalise_label(label: dict) -> dict:
    """Return a cleaned copy: strings stripped, addresses reduced to known keys.
    Does not validate."""
    out = dict(label)
    addrs = []
    for a in label.get("addresses") or []:
        b = empty_address()
        for k in ADDRESS_TEXT_FIELDS:
            b[k] = _s(a.get(k))
        b["role"] = a.get("role", b["role"])
        b["modality"] = a.get("modality", b["modality"])
        b["po_box"] = bool(a.get("po_box", False))
        if b["modality"] == "image" and not b["evidence"]:
            b["evidence"] = "image"
        addrs.append(b)
    out["addresses"] = addrs
    out["comment"] = _s(label.get("comment"))
    out["imprint_url"] = _s(label.get("imprint_url")) or None
    out["flags"] = list(label.get("flags") or [])
    return out


def validate_label(label: dict) -> list[str]:
    """Check a label against the schema; return error messages (empty = ok)."""
    errs: list[str] = []
    if not isinstance(label, dict):
        return ["label is not an object"]
    if not _s(label.get("host")):
        errs.append("host missing")

    status = label.get("site_status")
    if status not in SITE_STATUS:
        errs.append(f"site_status must be one of {SITE_STATUS}")
    live = status in LIVE_LIKE

    present = label.get("imprint_present")
    loc = label.get("imprint_location")
    if live:
        if not isinstance(present, bool):
            errs.append("imprint_present must be true or false")
        if loc not in IMPRINT_LOCATION:
            errs.append(f"imprint_location must be one of {IMPRINT_LOCATION}")
        elif present is True and loc == "none":
            errs.append("imprint_present is true but imprint_location is none")
        elif present is False and loc != "none":
            errs.append("imprint_present is false, so imprint_location must be none")
    else:
        if present not in (False, None):
            errs.append("imprint_present must be false when the site is not live")

    addrs = label.get("addresses")
    if not isinstance(addrs, list):
        errs.append("addresses must be a list")
        addrs = []
    for i, a in enumerate(addrs):
        pre = f"address {i + 1}: "
        if not isinstance(a, dict):
            errs.append(pre + "not an object")
            continue
        if a.get("role") not in ROLES:
            errs.append(pre + f"role must be one of {ROLES}")
        if a.get("modality") not in MODALITY:
            errs.append(pre + f"modality must be one of {MODALITY}")
        if not isinstance(a.get("po_box", False), bool):
            errs.append(pre + "po_box must be true or false")
        if not (_s(a.get("street")) or _s(a.get("postcode")) or _s(a.get("town"))):
            errs.append(pre + "needs at least a street, postcode or town")
        if a.get("modality") != "image" and not _s(a.get("evidence")):
            errs.append(pre + "evidence (verbatim span) required unless modality is image")
        for k in ADDRESS_TEXT_FIELDS:
            if not isinstance(a.get(k, ""), str):
                errs.append(pre + f"{k} must be a string")

    reason = label.get("no_address_reason")
    main = label.get("main_address_index")
    if addrs and not (live and present is True):
        errs.append("addresses are listed, but the site is not live or has no imprint")
    if addrs:
        if reason is not None and reason != "imprint_without_address":
            errs.append("no_address_reason must be empty when addresses are listed")
        if reason == "imprint_without_address":
            # only allowed when none of the listed addresses can be the main one
            if main is not None:
                errs.append("main_address_index must be empty with imprint_without_address")
            if any(isinstance(a, dict) and a.get("role") in MAIN_ROLES for a in addrs):
                errs.append("imprint_without_address, but a listed address has an operator role")
        else:
            if (
                not isinstance(main, int)
                or isinstance(main, bool)
                or not (0 <= main < len(addrs))
            ):
                errs.append("main_address_index must point to a listed address")
            elif isinstance(addrs[main], dict) and addrs[main].get("role") not in MAIN_ROLES:
                errs.append(f"main address must have a role in {MAIN_ROLES}")
    else:
        if main is not None:
            errs.append("main_address_index must be empty without addresses")
        if reason not in NO_ADDRESS_REASON:
            errs.append(f"no_address_reason required without addresses: {NO_ADDRESS_REASON}")
        elif not live and reason != "site_dead":
            errs.append("a site that is not live has no_address_reason site_dead")
        elif live and present is False and reason != "no_imprint":
            errs.append("no imprint, so no_address_reason must be no_imprint")
        elif live and present is True and reason != "imprint_without_address":
            errs.append("imprint present without address: use imprint_without_address")

    if live:
        if label.get("operator_type") not in OPERATOR_TYPE:
            errs.append(f"operator_type must be one of {OPERATOR_TYPE}")
        if label.get("topic") not in TOPICS:
            errs.append("topic must be one of the 11 classes")
    else:
        if label.get("operator_type") not in (None, "") + OPERATOR_TYPE:
            errs.append("operator_type invalid")
        if label.get("topic") not in (None, "") + TOPICS:
            errs.append("topic invalid")
    if not isinstance(label.get("topic_ambiguous", False), bool):
        errs.append("topic_ambiguous must be true or false")

    flags = label.get("flags", [])
    if not isinstance(flags, list) or any(f not in FLAGS for f in flags):
        errs.append(f"flags must be a list drawn from {FLAGS}")

    ann = label.get("annotator")
    if ann is not None and not (isinstance(ann, str) and _LABELLER_RE.match(ann)):
        errs.append("annotator must look like L1")
    return errs


def text_warnings(label: dict, texts: list[str]) -> list[str]:
    """Soft checks of verbatim fields against the capture text (whitespace-normalised).
    Returns warnings only; never blocks saving."""

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    hay = norm(" ".join(texts))
    out = []
    if not hay:
        return out
    for i, a in enumerate(label.get("addresses") or []):
        if a.get("modality") != "text":
            continue
        for k in ("evidence", "street", "postcode", "town"):
            v = _s(a.get(k))
            if v and norm(v) not in hay:
                out.append(f"address {i + 1}: {k} '{v[:40]}' not found in the DOM text")
    return out
