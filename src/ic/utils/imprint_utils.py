import re
from typing import Optional

# Words that only appear on a real legal notice, beyond the bare word "Impressum"
_EVIDENCE_WORDS = [
    r"angaben gem(?:ä|ae)ß",
    r"§\s*5\s*(?:abs\.?\s*\d\s*)?(?:tmg|ddg|ecg|dsg)",
    r"§\s*5\b",
    r"§\s*55\b",
    r"§\s*25\s+mediengesetz",
    r"inhaber",
    r"gesch(?:ä|ae)ftsf(?:ü|ue)hr",
    r"handelsregister",
    r"registergericht",
    r"registernummer",
    r"ust[\s.-]*id",
    r"umsatzsteuer",
    r"vertreten durch",
    r"vertretungsberechtigt",
    r"diensteanbieter",
    r"anbieterkennzeichnung",
    r"medieninhaber",
    r"firmenbuch",
    r"represented by",
    r"managing director",
    r"commercial register",
    r"register(?:ed)? (?:court|number|office)",
    r"vat (?:id|no|number|reg)",
    r"responsible for (?:the )?content",
    r"information pursuant",
    r"pursuant to (?:sect|§|section)",
    r"according to (?:sect|§|section)",
    r"company registration",
    r"registered office",
    r"mentions l[ée]gales",
    r"[ée]diteur",
    r"verlag",
    r"siret|siren\b|num[ée]ro d.enregistrement|capital social",
]
# Postcode + town (D/A/CH), optionally with country prefix: "91052 Erlangen", "A-1010 Wien"
_POSTCODE = r"(?<![\d.,/-])(?:d-|a-|ch-|at-)?\d{4,5}\s+[A-ZÄÖÜ][a-zäöüß]{2,}"

_EVIDENCE_RE = re.compile("|".join(_EVIDENCE_WORDS), re.I)
_POSTCODE_RE = re.compile(_POSTCODE)
_ERROR_RE = re.compile(
    r"bad requests? from your ip|rate.?limit|too many requests|access denied|"
    r"seite nicht gefunden|page not found|404 (?:not found|error|fehler)|"
    r"not found\b.{0,40}\b404|checking your browser|enable javascript and cookies|"
    r"verify you are (?:a )?human|just a moment",
    re.I,
)


def looks_like_error_page(text: str) -> bool:
    """True for rate-limit, bot-challenge and error pages with little text."""
    return len(text) < 2000 and bool(_ERROR_RE.search(text))


def has_imprint_evidence(text: Optional[str]) -> bool:
    """
    True if the text contains legal-notice evidence beyond the word "Impressum":
    a typical imprint phrase (Angaben gemäß, § 5 TMG, Inhaber, Geschäftsführer,
    Handelsregister, USt-ID, ...) or a postcode plus town.
    """
    if not text or looks_like_error_page(text):
        return False
    return bool(_EVIDENCE_RE.search(text) or _POSTCODE_RE.search(text))
