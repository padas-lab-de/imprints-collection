"""Shared helpers for E10: strict DACH address detector, Wilson interval, TLD grouping."""
import math
import re

# Strict DACH address: postcode + town with a country-consistent signal.
DE_PLZ = re.compile(r"(?<![\d.,/-])(?:D-|DE-)?\d{5}\s+[A-ZÄÖÜ][a-zäöüß]{2,}")
ATCH_PLZ = re.compile(r"(?<![\d.,/-])(?:A-|AT-|CH-)\d{4}\s+[A-ZÄÖÜ][a-zäöüß]{2,}|(?<![\d.,/-])\d{4}\s+[A-ZÄÖÜ][a-zäöüß]{2,}")
DE_HINT = re.compile(r"deutschland|germany|stra(?:ß|ss)e|\bstr\.|geschäftsführer|angaben gemäß|amtsgericht|\bTMG\b|\bDDG\b|handelsregister|inhaber|verantwortlich", re.I)
AT_HINT = re.compile(r"österreich|austria|firmenbuch|\bUID\b|ATU\d|medieninhaber|\bA-\d{4}", re.I)
CH_HINT = re.compile(r"schweiz|switzerland|suisse|svizzera|\bCH-\d{4}|CHE-\d|\bMWST", re.I)
# Non-DACH signals that make a 4/5-digit postcode ambiguous
FOREIGN = re.compile(r"\b(?:france|españa|spain|italia|italy|united states|usa|united kingdom|nederland|belgi|polska|danmark|sverige|norge|brasil)\b", re.I)


def dach_country(text):
    """Return 'DE', 'AT', 'CH' or None. Strict: postcode+town AND a country-consistent hint."""
    if not text:
        return None
    t = text
    if DE_PLZ.search(t) and (DE_HINT.search(t) or re.search(r"\bD-\d{5}", t)):
        if not FOREIGN.search(t) or re.search(r"deutschland|germany", t, re.I):
            return "DE"
    if ATCH_PLZ.search(t):
        if CH_HINT.search(t):
            return "CH"
        if AT_HINT.search(t):
            return "AT"
    return None


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def grp(host):
    t = host.rsplit(".", 1)[-1]
    return t if t in ("de", "at", "ch", "eu", "com", "net", "org") else "other"
