#!/usr/bin/env python3
"""E40 parking / for-sale / placeholder domain filter. Stdlib only, read-only.

Library (detect, site_flags, ...) plus commands:

  scan DIR [TARGET_HOST ...]     one fetch output dir -> flagged rows on stdout (runs on a VM as
                                 `ssh -o BatchMode=yes VM nice -n 19 ionice -c3 python3 - scan DIR < parking_filter.py`)
  apply --in E31_INDIR --scan FILE [FILE ...] --targets TARGETS.tsv --out OUTDIR
                                 combine scan rows with the E31 D34 canonical sites (see apply_filter)

Detection works on the home page record ("main": title, description, main_content) of imprints_batch*.jsonl.gz.
Categories: sale (domain for sale / broker), park (parked, registrar/registry placeholder), host (hosting
default page), constr (under construction). Core filter = sale + park; extended = + host + constr.
Weak patterns (brand names, short phrases) only count on pages with little text (content_length <= WEAK_MAX).
"""

import argparse
import gzip
import hashlib
import json
import re
import sys
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

WEAK_MAX = 1500  # max content_length for weak patterns
STRONG_MAX = 20000  # pages longer than this are never flagged
WINDOW = 3000  # text window: title + description + first WINDOW chars of main_content
SAMPLE_MOD = 10000  # scan emits a snippet row for md5(SALT + host) % SAMPLE_MOD == 0 (precision/recall sample)
SAMPLE_SALT = "E40"

_FOR_SALE = (
    r"(?:zum verkauf|zu verkaufen|for sale|available for purchase|zum kauf|käuflich|zu haben|zum erwerb|verkäuflich)"
)
# (category, label, regex, strong)
_P = [
    # ---- domain for sale ----
    (
        "sale",
        "domain_zum_verkauf",
        r"(?:domain|webseite|website|internetadresse)(?:\s+name)?\s+(?:ist\s+|is\s+|steht\s+|wird\s+|may be\s+|can be\s+|könnte\s+)?"
        r"(?:jetzt\s+|currently\s+|derzeit\s+|aktuell\s+)?" + _FOR_SALE,
        True,
    ),
    (
        "sale",
        "buy_this_domain",
        r"(?:buy|purchase|kaufen sie|erwerben sie|acquire|inquire about)\s+(?:this|diese|the|die|dieser)\s+(?:domain|domainname|premium)",
        True,
    ),
    ("sale", "domain_kaufen", r"(?:diese\s+)?domain\s+(?:jetzt\s+)?(?:kaufen|erwerben|anfragen)\b|domain(?:name)?\s+zum\s+kauf", False),
    ("sale", "for_sale_title", r"\bdomain\s+(?:for sale|zu verkaufen)\b", False),
    (
        "sale",
        "make_offer",
        r"(?:make|submit|place)\s+an?\s+(?:offer|bid)\s+(?:on|for)\s+(?:this|the)\s+domain|(?:preis|kaufpreis|gebot)\s+für\s+(?:diese|dieser)\s+domain",
        True,
    ),
    (
        "sale",
        "broker_brand",
        r"\b(?:sedo(?:parking)?\.com|sedo\s+(?:domain|gmbh|parking)|dan\.com|afternic|hugedomains|undeveloped\.com|squadhelp|brandbucket|atom\.com|sav\.com"
        r"|godaddy\s+auctions?|domainmarkt(?:platz)?\.|aftermarket\.(?:eu|pl|de|com)|domain-akquise|namex\.de|domainkontor24|domaincatcher|domainkompetenz"
        r"|domain[- ]rebellen|domainhandel|ts\.domainname|fruits\.co|domainprofi|domain-anfrage)",
        False,
    ),
    ("sale", "domain_investment", r"\b(?:premium[- ]domain|domain\s+(?:broker|marketplace|portfolio)|domainhändler)\b", False),
    # ---- parked / registrar and registry placeholder ----
    (
        "park",
        "parked",
        r"(?:domain\s+(?:ist\s+|wurde\s+)?(?:geparkt|parked)|(?:is|ist|wurde|been|currently)\s+(?:parked|geparkt)|parked\s+(?:domain|free|page|by|at|with)"
        r"|domain\s*park(?:ing)?\b|parkingcrew|parking\s*crew|bodis\.com|domainsponsor|domain\s+reserviert|domain\s+(?:is\s+)?(?:now\s+)?reserved"
        r"|abovedomains|fabulous\.com|sedoparking|parklogic|voodoo\.com)",
        False,
    ),
    (
        "park",
        "registrar_placeholder",
        r"(?:domain\s+(?:registration\s+)?(?:has\s+)?expired|domain\s+is\s+expired|domain\s+(?:ist\s+)?abgelaufen"
        r"|(?:has\s+been\s+)?recently\s+registered\s+(?:with|at|by)|diese\s+domain\s+wurde\s+(?:bei\s+\S+\s+)?(?:für\s+einen\s+kunden\s+)?registriert"
        r"|domain\s+(?:not\s+available|nicht\s+(?:verfügbar|eingerichtet|konfiguriert|zugewiesen))|domain\s+noch\s+nicht\s+zugewiesen"
        r"|domain\s+(?:ist\s+)?unkonfiguriert|diese\s+domain\s+ist\s+(?:noch\s+)?(?:nicht|unkonfiguriert)|keine\s+website\s+hinterlegt"
        r"|dieser\s+domain\s+ist\s+noch\s+kein\s+ziel|noch\s+keine\s+(?:website|webseite|inhalte)\s+(?:hinterlegt|vorhanden|eingerichtet)"
        r"|no\s+website\s+(?:configured|connected)|domain\s+details\s+page|domain\s+gesperrt|neue\s+domain\s+bei\s+(?:der\s+)?\w+|keine\s+inhalte\s+hinterlegt|no\s+content\s+has\s+been\s+uploaded"
        r"|domain\s+(?:requires\s+configuration|not\s+configured)|no\s+website\s+is\s+configured|domain\s+nicht\s+aktiv|domain\s+deactivated"
        r"|noch\s+mit\s+keinem\s+hosting\s+verbunden|nom\s+de\s+domaine\s+est\s+enregistré|(?:web\s*site|webseite)\s+is\s+now\s+reserved)",
        False,
    ),
    # ---- hosting default / account pages ----
    (
        "host",
        "hosting_default",
        r"(?:web\s+server'?s\s+default\s+page|welcome\s+to\s+nginx|apache2?\s+(?:ubuntu\s+|debian\s+)?default\s+page|test\s+page\s+for\s+the\s+(?:apache|nginx)"
        r"|^\s*it\s+works!?\s*$|standard-index-seite|this\s+is\s+the\s+default\s+(?:web\s*)?page|default\s+(?:web\s*site\s+)?page|iis\s+windows\s+server"
        r"|account\s+(?:has\s+been\s+)?suspended|dieser\s+account\s+ist\s+zur\s+zeit\s+nicht|ihr\s+account\s+wurde\s+freigeschaltet|soeben\s+freigeschaltete"
        r"|you\s+are\s+all\s+set\s+to\s+go|congratulations[!,]?\s+your\s+(?:web\s*site|domain|hosting)|webspace\s+nicht\s+erreichbar"
        r"|php\s+version\s+not\s+supported|domain\s+hosted\s+by|there\s+is\s+no\s+web\s+site\s+at\s+this\s+address|you\s+see\s+this\s+page\s+because"
        r"|default[- ]index|dies\s+ist\s+ein\s+platzhalter|this\s+is\s+a\s+placeholder|apache\s+is\s+functioning\s+normally|nginx\s+proxy\s+manager|your\s+new\s+web\s+server\s+is\s+ready|site\s+is\s+created\s+successfully"
        r"|sorry,\s+no\s+host\s+found|unknown\s+address|hosted\s+by\s+one\.com|(?:webseite|website|seite)\s+(?:ist\s+)?(?:zurzeit|derzeit)\s+nicht\s+(?:erreichbar|verfügbar))",
        False,
    ),
    # ---- under construction ----
    (
        "constr",
        "under_construction",
        r"(?:hier\s+(?:entsteht|entstehen|wird)\s+(?:eine?\s+)?(?:neue|ihre|unsere|bald)"
        r"|(?:website|webseite|homepage|seite|site|internetseite|internetpräsenz)\s+(?:befindet\s+sich\s+)?(?:im\s+aufbau|in\s+arbeit|in\s+bearbeitung"
        r"|wird\s+(?:zur\s+zeit\s+|derzeit\s+|gerade\s+)?(?:überarbeitet|erstellt|aufgebaut|neu\s+gestaltet))"
        r"|im\s+aufbau|under\s+construction|coming\s+soon|bald\s+verfügbar|in\s+kürze\s+(?:verfügbar|online)"
        r"|neue\s+(?:website|webseite|homepage)\s+(?:folgt|in\s+arbeit|kommt)|wir\s+arbeiten\s+(?:gerade\s+)?an\s+(?:unserer|der|einer)"
        r"|this\s+web\s*site\s+has\s+been\s+reserved|site\s+en\s+construction)",
        False,
    ),
]
# cheap substring gates (any of): a regex only runs when its gate matches the lowercased text
_GATES = {
    "domain_zum_verkauf": ("verkauf", "for sale", "purchase", "kauf", "erwerb", "zu haben"),
    "buy_this_domain": ("buy ", "purchase", "kaufen sie", "erwerben sie", "acquire", "inquire"),
    "domain_kaufen": ("kaufen", "erwerben", "anfragen", "zum kauf"),
    "for_sale_title": ("for sale", "zu verkaufen"),
    "make_offer": ("offer on", "offer for", "bid on", "bid for", "preis für", "gebot für"),
    "broker_brand": ("sedo", "dan.com", "afternic", "hugedomains", "undeveloped", "squadhelp", "brandbucket", "atom.com", "sav.com", "godaddy", "domainmarkt", "aftermarket", "akquise", "namex", "domainkontor", "domaincatcher", "domainkompetenz", "rebellen", "domainhandel", "domainname", "fruits.co", "domainprofi", "domain-anfrage"),
    "domain_investment": ("premium", "broker", "marketplace", "portfolio", "händler"),
    "parked": ("park", "reserv", "bodis", "sponsor", "above", "fabulous", "voodoo"),
    "registrar_placeholder": ("domain", "keine website", "no website", "noch keine", "keine inhalte", "no content", "reserved"),
    "hosting_default": ("default", "nginx", "it works", "standard-index", "suspended", "account", "freigeschaltet", "all set to go", "congratulations", "webspace", "php version", "hosted by", "no web site", "you see this page", "placeholder", "platzhalter", "default-index", "default index", "apache", "ready to use", "created successfully", "no host", "unknown address", "one.com", "nicht erreichbar", "nicht verfügbar"),
    "under_construction": ("entsteh", "aufbau", "in arbeit", "bearbeitung", "construction", "coming soon", "verfügbar", "kürze", "folgt", "arbeiten", "reserved", "überarbeitet", "erstellt", "aufgebaut", "neu gestaltet", "wird zur", "wird gerade", "wird derzeit", "hier wird", "en construction"),
}
PATTERNS_R1 = [(c, lab, re.compile(rx, re.I | re.M), strong, _GATES[lab]) for c, lab, rx, strong in _P]

# ----------------------------------------------------------------------------------------- round 2 (E40 r2)
# Added 2026-11-09 from the round-1 misses and from reading unflagged short found pages (E30, E33, E37, E41 L1).
# The round-1 rules above are unchanged. All r2 labels start with "r2_" and map to the same categories.
_DOM = r"[\w\-äöü]+(?:\.[\w\-äöü]+)*\.[a-z]{2,10}"  # a domain name token
_P_R2 = [
    # ---- sale ----
    (
        "sale",
        "r2_sale_template",  # fixed sentences of sale templates (kv-gmbh, "aktuell kaufen und sofort übernehmen", ...)
        r"(?:am\s+kauf\s+der\s+domain|können\s+die\s+domain\s+\S+\s+(?:aktuell\s+|jetzt\s+)?kaufen|wird\s+zum\s+kauf\s+angeboten"
        r"|diese\s+domain\s+können\s+sie\s+(?:\w+\s+)?(?:käuflich\s+)?erwerben|domain\s+names?\s+(?:are\s+|is\s+)?for\s+sale|\bnamepros\b|\b301\s*domains\b"
        r"|interested\s+in\s+(?:buying\s+)?(?:this|the)\s+domain|interesse\s+an\s+(?:dieser|einer\s+unserer)\s+(?:top-?\s*|premium-?\s*)?domains?\b"
        r"|kooperation\s+zum\s+ausbau\s+der\s+domain|zu\s+verkaufen\s*\|\s*lemmynet|zu\s+verkaufen\W+weitere\s+domains"
        r"|domains?,?\s+die\s+zum\s+verkauf\s+stehen|diese\s+domains\s+stehen\s+zum\s+verkauf)",
        True,
    ),
    (
        "sale",
        "r2_name_for_sale",  # "<domain> steht zum Verkauf", "Die Domain <domain> ist zu verkaufen", "Diese Domain, , ist zum Verkauf"
        r"(?:\b" + _DOM + r"|\bdomains?(?:\s+[„\"']?" + _DOM + r"[“\"']?|\s*,\s*,?))\s+(?:steht|ist|wird|stehen|sind)\s+"
        r"(?:jetzt\s+|aktuell\s+|derzeit\s+|ab\s+sofort\s+)?(?:zum\s+verkauf|zu\s+verkaufen|for\s+sale|zum\s+kauf|zu\s+haben)"
        r"|^\s*" + _DOM + r"\s+(?:zu\s+verkaufen|for\s+sale)\b|domain[^.\n]{0,80}\bum\s+sie\s+zu\s+erwerben",
        False,
    ),
    # ---- parked / registrar and registry placeholder ----
    (
        "park",
        "r2_park_template",  # fixed registrar / registry sentences (united-domains, IONOS, DENIC transit, BrandShelter, freenet)
        r"(?:im\s+kundenauftrag\s+(?:registriert|reserviert)|diese\s+domain\s+ist\s+bereits\s+(?:bei\s+\S+\s+)?registriert"
        r"|aufgerufene\s+domain\s+ist\s+derzeit\s+nicht\s+erreichbar|domaininhaber\s+ist\s+bereits\s+informiert"
        r"|registered\s+on\s+behalf\s+of\s+a\s+client|\bbrand\s*shelter\b|als\s+mail[- ]?domain\s+registriert"
        r"|used\s+for\s+e-?mail\s+purposes\s+only|als\s+kunde\s+von\s+\S+(?:\s+\S+){0,3}\s+können\s+sie\s+diese\s+domain"
        r"|für\s+diese\s+domain\s+ist\s+noch\s+kein\s+inhalt\s+hinterlegt|domain\s+\S+\s+kann\s+noch\s+registriert\s+werden)",
        True,
    ),
    (
        "park",
        "r2_park_phrase",  # shorter registrar phrases, only on short pages
        r"(?:für\s+(?:einen|unsere[nm]?)\s+(?:unserer\s+)?kunden(?:\s+(?:von|der|bei)\s+\S+(?:\s+\S+)?)?\s+(?:registriert|reserviert)"
        r"|domain\s+wurde\s+erfolgreich\s+registriert|domain\s+ist\s+registriert,?\s+(?:derzeit|jedoch|aber)|diese\s+domain\s+ist\s+reserviert"
        r"|^\s*reserviert\s+für\b|diese\s+domain\s+(?:ist\s+(?:derzeit\s+)?inaktiv|wurde\s+deaktiviert)"
        r"|diese\s+domain\s+wird\s+(?:derzeit|momentan|zur\s+zeit|aktuell)\s+nicht\s+(?:für\s+eine\s+(?:website|webseite)\s+)?genutzt"
        r"|domain\s+aktiv\W+technische\s+bereitstellung)",
        False,
    ),
    # ---- hosting default / account pages ----
    (
        "host",
        "r2_host_template",  # fixed hoster placeholder sentences (EUserv, Advantic, compaso, nicmanager, tralios, ...)
        r"(?:dieser\s+platzhalter\s+von|homepage,\s+webspace\s+oder\s+server\s+nicht\s+gefunden|keiner\s+aktiven\s+website\s+zugeordnet"
        r"|webhost\s+wurde\s+neu\s+eingerichtet|auf\s+diesem\s+account\s+noch\s+keine\s+daten\s+hinterlegt"
        r"|(?:\(noch\)|noch)\s+kein\s+(?:webseiten)?inhalt\s+hinterlegt|kein\s+webseiteninhalt\s+hinterlegt"
        r"|für\s+diese\s+domain\s+ist\s+keine\s+(?:webseite|website)\s+verfügbar|domain\s+zeigt\s+erfolgreich\s+auf\s+(?:den|einen|unseren)\s+server"
        r"|auf\s+diesem\s+knotenpunkt\s+nicht\s+konfiguriert|custom\s+domain\b.{0,80}?\bis\s+now\s+connected)",
        True,
    ),
    (
        "host",
        "r2_host_phrase",  # shorter hoster phrases, only on short pages
        r"(?:webserver\s+von\s+\S+(?:\s+\S+)?\s+erreicht|homepage\s+kann\s+leider\s+nicht\s+aufgerufen\s+werden"
        r"|(?:webseite|website)\s+(?:ist\s+)?aktuell\s+nicht\s+erreichbar|ist\s+lediglich\s+(?:ein\s+)?platzhalter"
        r"|domains?\s+&\s+hosting\s+von\s+helloly|in\s+3\s+minuten\s+zur\s+eigenen\s+domain|diese\s+domain\s+wird\s+bei\s+\S+(?:\s+\S+)?\s+gehostet)",
        False,
    ),
    # ---- under construction (not a drop rule) ----
    (
        "constr",
        "r2_under_construction",
        r"(?:hier\s+entsteh(?:t|en)\s+(?:in\s+kürze|demnächst|gerade|zur\s+zeit|derzeit)|befindet\s+sich\s+(?:zur\s+zeit\s+|derzeit\s+|gerade\s+)?im\s+umbau"
        r"|folgt\s+in\s+kürze|(?:website|webseite|homepage|internetseite|seite)\s+(?:ist\s+|befindet\s+sich\s+)?in\s+erstellung"
        r"|(?:website|webseite|homepage)\s+folgt\b|strona\s+w\s+przygotowaniu|currently\s+being\s+migrated)",
        False,
    ),
]
_GATES_R2 = {
    "r2_sale_template": ("kauf", "erwerben", "for sale", "namepros", "301", "interest", "interesse", "ausbau", "verkauf"),
    "r2_name_for_sale": ("verkauf", "for sale", "zum kauf", "zu haben", "erwerben"),
    "r2_park_template": ("kundenauftrag", "bereits", "nicht erreichbar", "on behalf", "shelter", "mail", "als kunde", "kein inhalt", "noch registriert"),
    "r2_park_phrase": ("kunden", "registriert", "reserviert", "inaktiv", "deaktiviert", "genutzt", "bereitstellung"),
    "r2_host_template": ("platzhalter", "nicht gefunden", "aktiven website", "webhost", "hinterlegt", "keine webseite", "keine website", "zeigt erfolgreich", "knotenpunkt", "now connected"),
    "r2_host_phrase": ("erreicht", "nicht aufgerufen", "nicht erreichbar", "platzhalter", "helloly", "eigenen domain", "gehostet"),
    "r2_under_construction": ("entsteh", "umbau", "kürze", "erstellung", "folgt", "przygotowaniu", "migrated"),
}
PATTERNS_R2 = [(c, lab, re.compile(rx, re.I | re.M), strong, _GATES_R2[lab]) for c, lab, rx, strong in _P_R2]
PATTERNS = PATTERNS_R1 + PATTERNS_R2  # default: round 1 + round 2
CAT_ORDER = {"sale": 0, "park": 1, "host": 2, "constr": 3}
CORE = ("sale", "park")


def _flat(s, n=None):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s[:n] if n else s


def detect(title, description, content, content_length=None, patterns=None):
    """-> (category, label, context) of the most severe match (sale, park, host, constr), or None.
    patterns: PATTERNS (round 1 + round 2, the default) or PATTERNS_R1 (reproduces round 1)."""
    patterns = PATTERNS if patterns is None else patterns
    clen = len(content or "") if content_length is None else content_length
    if clen > STRONG_MAX:
        return None
    text = "\n".join(x for x in ((title or ""), (description or ""), (content or "")[:WINDOW]) if x)
    best = None
    low = text.lower()
    for cat, label, rx, strong, gate in patterns:
        if not strong and clen > WEAK_MAX:
            continue
        if not any(g in low for g in gate):
            continue
        m = rx.search(text)
        if m and (best is None or CAT_ORDER[cat] < CAT_ORDER[best[0]]):
            a, b = max(0, m.start() - 50), min(len(text), m.end() + 50)
            best = (cat, label, _flat(text[a:b], 140))
    return best


def collapse(h):
    return h[4:] if h.startswith("www.") else h


def is_sample(host):
    return int(hashlib.md5((SAMPLE_SALT + host).encode()).hexdigest(), 16) % SAMPLE_MOD == 0


# ----------------------------------------------------------------------------- scan (runs on VMs)
def scan_dir(d, targets, out, stats):
    """Writes TSV rows: host, kind, cat, label, final_url, title, ctx[, desc, content_len, content_head].
    F rows decided by an r2 label carry r1_cat, r1_label, desc, content_len, content_head after ctx.
    One row per host (its last record in the dir). kind F = flagged, S = sample host (md5 rule, flagged or
    not), T = record of a listed target host. Hosts flagged by an earlier record but not by the last one are
    dropped (resume duplicates)."""
    flagged, samples, tgt = {}, {}, {}
    for p in sorted(Path(d).glob("imprints_batch*.jsonl.gz")):
        stats["files"] += 1
        try:
            with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                        h = str(r["host"]).strip().lower()
                        m = r.get("main") or {}
                    except (ValueError, KeyError, TypeError, AttributeError):
                        stats["bad_record"] += 1
                        continue
                    stats["records"] += 1
                    content = m.get("main_content") or ""
                    title, desc = m.get("title") or "", m.get("description") or ""
                    hit = detect(title, desc, content, m.get("content_length") or len(content))
                    url = _flat(m.get("url") or "", 200)
                    snip = (_flat(desc, 150), str(len(content)), _flat(content, 400))
                    if hit:
                        extra = ()
                        if hit[1].startswith("r2_"):  # r2 decides: keep the round-1 result and the page text
                            h1 = detect(title, desc, content, m.get("content_length") or len(content), PATTERNS_R1)
                            extra = (h1[0] if h1 else "", h1[1] if h1 else "", *snip)
                        flagged[h] = (hit, url, _flat(title, 80), extra)
                    else:
                        flagged.pop(h, None)
                    if is_sample(h):
                        samples[h] = (hit, url, _flat(title, 80), snip)
                    if collapse(h) in targets:
                        tgt[h] = (hit, url, _flat(title, 80), snip)
        except (EOFError, zlib.error, OSError):
            stats["truncated_gz"] += 1
    for h, (hit, url, title, extra) in flagged.items():
        out.write("\t".join([h, "F", hit[0], hit[1], url, title, hit[2], *extra]) + "\n")
        stats["flagged"] += 1
    for kind, dd in (("S", samples), ("T", tgt)):
        for h, (hit, url, title, snip) in dd.items():
            c, lab, ctx = hit if hit else ("", "", "")
            out.write("\t".join([h, kind, c, lab, url, title, ctx, *snip]) + "\n")


def cmd_scan(argv):
    d, targets = argv[0], {collapse(t) for t in argv[1:]}
    stats = dict(files=0, records=0, flagged=0, bad_record=0, truncated_gz=0)
    scan_dir(d, targets, sys.stdout, stats)
    print("#stats " + " ".join(f"{k}={v}" for k, v in stats.items()), file=sys.stderr)


# ----------------------------------------------------------------------------- apply (offline)
PARK_CLASSES = {"domain_sale": "sale", "parking": "park", "registry": "park", "hosting_placeholder": "host"}


def load_scan(paths):
    """-> ({host: (cat, label, final_url, title, ctx)} flagged hosts, {host: sample row}, {host: target row})."""
    flagged, samples, tgt = {}, {}, {}
    for p in paths:
        with open(p, encoding="utf-8", newline="") as f:
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) < 7 or c[1] not in "FST":
                    continue
                if c[1] == "F":
                    flagged[c[0]] = (c[2], c[3], c[4], c[5], c[6])
                elif c[1] == "S":
                    samples[c[0]] = c
                else:
                    tgt[c[0]] = c
    return flagged, samples, tgt


def load_targets(path):
    """classification TSV (columns target, class, ...) -> {target: category} for classes in PARK_CLASSES."""
    out = {}
    with open(path, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        for line in f:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            if r["class"] in PARK_CLASSES:
                out[r["target"]] = PARK_CLASSES[r["class"]]
    return out


def load_real_targets(path):
    """Set of targets classified 'real' (never flagged by page text when a host lands there)."""
    out = set()
    with open(path, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        for line in f:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            if r["class"] == "real":
                out.add(r["target"])
    return out


def host_category(host, target, scan_flag, target_class, real=frozenset()):
    """Category of one found host: text flag of its page (ignored if the host landed on a real target),
    else its redirect target is a parking target."""
    f = scan_flag.get(host)
    if f and collapse(urlsplit(f[2]).hostname or "") not in real:
        return f[0]
    if target:
        return target_class.get(collapse(target))
    return None


def site_flags(canon_hosts, host_cat, target_class):
    """canon_hosts: {site: [found hosts]}; host_cat: {host: category or None}; target_class: {target: category}.
    A site is flagged if it is itself a parking target, or has found hosts and all of them are flagged
    (category = most severe among its hosts)."""
    out = {}
    for site, hosts in canon_hosts.items():
        if site in target_class:
            out[site] = target_class[site]
        elif hosts and all(host_cat.get(h) for h in hosts):
            out[site] = min((host_cat[h] for h in hosts), key=CAT_ORDER.get)
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (c - h, c + h)


def apply_filter(indir, scan_paths, targets_path, outdir):
    """D34 sites of the E31 inputs, flagged sites by category, and the D34 count per source after the filter.

    Site model: for each source, each found host h (last-row rule) with target t gets canonical c = D34 rule.
    A site's found hosts are collected over all sources. "new per source" = first-source rule as in E31."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E31"))
    import release_count as rc

    flagged, _, _ = load_scan(scan_paths)
    target_class = load_targets(targets_path)
    real = load_real_targets(targets_path)
    sources = list(rc.load_manifest(indir).items())
    crawled, loaded = set(), []
    for name, paths in sources:
        n, found = rc.read_source(paths, crawled)
        loaded.append((name, found))
    canon_hosts, site_src, host_cat = {}, {}, {}
    per_source_sites = []
    for name, found in loaded:
        sites = set()
        for h, t in found.items():
            c = rc.canonical(h, t, crawled)
            sites.add(c)
            canon_hosts.setdefault(c, set()).add(h)
            cat = host_category(h, t, flagged, target_class, real)
            # a host seen in several sources: flagged if flagged in any (page text is the same fetch target)
            host_cat[h] = host_cat.get(h) or cat
        per_source_sites.append((name, sites))
    sf = site_flags(canon_hosts, host_cat, target_class)
    seen, rows = set(), []
    for name, sites in per_source_sites:
        new = sites - seen
        seen |= sites
        nf = Counter(sf[s] for s in new if s in sf)
        rows.append((name, len(new), sum(nf.values()), nf["sale"], nf["park"], nf["host"], nf["constr"]))
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    tot = Counter(sf.values())
    total_sites = len(seen)
    core = tot["sale"] + tot["park"]
    with open(out / "filter_by_source.tsv", "w") as f:
        f.write("source\tnew_d34\tflagged_all\tsale\tpark\thost\tconstr\tnew_d34_after_core\tnew_d34_after_all\n")
        for r in rows + [("TOTAL", total_sites, len(sf), tot["sale"], tot["park"], tot["host"], tot["constr"])]:
            nm, n, fa, sa, pa, ho, co = r
            f.write("\t".join(map(str, [nm, n, fa, sa, pa, ho, co, n - sa - pa, n - fa])) + "\n")
    with open(out / "flagged_sites.tsv", "w") as f:
        f.write("site\tcategory\tn_found_hosts\tsite_is_target\n")
        for s in sorted(sf):
            f.write(f"{s}\t{sf[s]}\t{len(canon_hosts.get(s, ()))}\t{int(s in target_class)}\n")
    # inputs for the precision / miss samples (E40 r2): found hosts of flagged sites, and md5-sample found hosts
    with open(out / "flagged_site_hosts.tsv", "w") as f:
        f.write("site\tsite_category\thost\thost_category\thost_label\n")
        for s in sorted(sf):
            for h in sorted(canon_hosts.get(s, ())):
                fl = flagged.get(h)
                f.write(f"{s}\t{sf[s]}\t{h}\t{host_cat.get(h) or ''}\t{fl[1] if fl else ''}\n")
    with open(out / "sample_found_hosts.tsv", "w") as f:
        f.write("host\tsite\tsite_category\n")
        for s in sorted(canon_hosts):
            for h in sorted(canon_hosts[s]):
                if is_sample(h):
                    f.write(f"{h}\t{s}\t{sf.get(s, '')}\n")
    print(f"sites {total_sites} flagged_all {len(sf)} core {core} {dict(tot)} after_core {total_sites - core} after_all {total_sites - len(sf)}")
    return sf, canon_hosts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("--in", dest="indir", required=True)
    a.add_argument("--scan", nargs="+", required=True)
    a.add_argument("--targets", required=True)
    a.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    apply_filter(a.indir, a.scan, a.targets, a.out)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "scan":
        cmd_scan(sys.argv[2:])
    else:
        sys.exit(main())
