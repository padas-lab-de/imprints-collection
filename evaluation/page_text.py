"""Model input from an `ic fetch` record: the static page text of the landing page and the imprint.

record() turns one `ic fetch` record into one input line (``host``, ``homepage_text``, ``imprint_text``, ``meta``):
the resiliparse ``main_content`` of each page, cleaned by clean_text() and cut at 6,000 chars. The gold-set screen,
the address suggestions and the model evaluation all use this form. Stdlib only.
"""

from __future__ import annotations

import re

BUDGET = 6_000


def clean_text(txt: str, budget: int = BUDGET) -> str:
    """Drop empty and repeated lines, collapse blanks, cut at ``budget`` chars (at a line end if one is close)."""
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


def norm_host(h: str) -> str:
    h = h.strip().lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def record(r: dict, origin: str) -> dict:
    """`ic fetch` record -> model input (homepage_text, imprint_text, meta)."""
    m, i = r.get("main") or {}, r.get("impressum") or {}
    home_raw, imp_raw = m.get("main_content") or "", i.get("main_content") or ""
    home, imp = clean_text(home_raw), clean_text(imp_raw)
    return {
        "host": r["host"],
        "homepage_text": home,
        "imprint_text": imp,
        "meta": {
            "source": "",
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
