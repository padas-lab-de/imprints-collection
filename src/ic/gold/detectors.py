"""Offline detectors for the gold-set diversity strata (docs/gold_set_design.md).

Every function here is pure: it takes HTML, text, headers or timestamps that were
fetched elsewhere (scripts/gold/e8_pilot.py) and returns a label plus the evidence
that produced it, so each label can be audited by hand. No network access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

# ---------------------------------------------------------------------------
# HTML scan: one pass collects everything the detectors need
# ---------------------------------------------------------------------------


@dataclass
class Link:
    href: str  # raw attribute value
    url: str  # absolute URL ("" for javascript:/mailto:)
    text: str  # anchor text incl. <img alt> inside the anchor
    title: str = ""
    aria_label: str = ""
    onclick: str = ""


@dataclass
class PageScan:
    base_href: Optional[str] = None
    generators: List[str] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    script_srcs: List[str] = field(default_factory=list)
    asset_urls: List[str] = field(default_factory=list)  # link href, img src
    images: List[Tuple[str, str]] = field(default_factory=list)  # (src, alt)
    n_scripts: int = 0
    inline_script_chars: int = 0
    iframes: List[str] = field(default_factory=list)
    frames: int = 0  # <frame>/<frameset> (very old sites)
    has_noscript_warning: bool = False


class _Scanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scan = PageScan()
        self._a_stack: List[Dict[str, str]] = []
        self._in_script = False
        self._in_noscript = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "base" and a.get("href") and self.scan.base_href is None:
            self.scan.base_href = a["href"].strip()
        elif tag == "meta" and a.get("name", "").lower() == "generator":
            self.scan.generators.append(a.get("content", "").strip())
        elif tag == "a":
            self._a_stack.append(
                {
                    "href": a.get("href", ""),
                    "title": a.get("title", ""),
                    "aria": a.get("aria-label", ""),
                    "onclick": a.get("onclick", ""),
                    "text": "",
                }
            )
        elif tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            alt = a.get("alt", "")
            self.scan.images.append((src, alt))
            self.scan.asset_urls.append(src)
            if self._a_stack:
                self._a_stack[-1]["text"] += " " + alt
        elif tag == "script":
            self.scan.n_scripts += 1
            self._in_script = True
            if a.get("src"):
                self.scan.script_srcs.append(a["src"])
        elif tag == "link" and a.get("href"):
            self.scan.asset_urls.append(a["href"])
        elif tag == "iframe":
            self.scan.iframes.append(a.get("src", ""))
        elif tag in ("frame", "frameset"):
            self.scan.frames += 1
        elif tag == "noscript":
            self._in_noscript = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "a":
            self.handle_endtag("a")

    def handle_endtag(self, tag):
        if tag == "a" and self._a_stack:
            d = self._a_stack.pop()
            self.scan.links.append(
                Link(
                    href=d["href"],
                    url="",
                    text=re.sub(r"\s+", " ", d["text"]).strip(),
                    title=d["title"],
                    aria_label=d["aria"],
                    onclick=d["onclick"],
                )
            )
        elif tag == "script":
            self._in_script = False
        elif tag == "noscript":
            self._in_noscript = False

    def handle_data(self, data):
        if self._in_script:
            self.scan.inline_script_chars += len(data)
            return
        if self._in_noscript and re.search(
            r"javascript|enable js|aktivieren sie", data, re.I
        ):
            self.scan.has_noscript_warning = True
        for d in self._a_stack:
            d["text"] += data


def scan_html(html: str, page_url: str) -> PageScan:
    """Parse HTML once; resolve link URLs against <base href> if present."""
    p = _Scanner()
    try:
        p.feed(html or "")
        p.close()
    except Exception:  # malformed HTML: keep what was collected
        pass
    scan = p.scan
    base = urljoin(page_url, scan.base_href) if scan.base_href else page_url
    for link in scan.links:
        href = link.href.strip()
        if not href or href.lower().startswith(("javascript:", "mailto:", "tel:")):
            link.url = ""
        else:
            try:
                link.url = urljoin(base, href)
            except ValueError:
                link.url = ""
    return scan


# ---------------------------------------------------------------------------
# Host, TLD, country
# ---------------------------------------------------------------------------

_SECOND_LEVEL = {"co.uk", "or.at", "co.at", "ac.at", "gv.at", "com.de"}


def registered_domain(host: str) -> str:
    """Cheap registered-domain approximation (last two labels, three for known 2LDs)."""
    host = (host or "").lower().strip(".").split(":")[0]
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in _SECOND_LEVEL:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def tld_class(host: str) -> str:
    """TLD stratum: de, at, ch, com, org, net, eu, other."""
    tld = (host or "").lower().rstrip(".").rsplit(".", 1)[-1]
    return tld if tld in {"de", "at", "ch", "com", "org", "net", "eu"} else "other"


# ---------------------------------------------------------------------------
# Site status (is there a real website at all?)
# ---------------------------------------------------------------------------

_PARKED = re.compile(
    r"(domain (is|may be) for sale|diese domain (steht|kann|ist) .{0,40}(verkauf|gekauft|erwerben)"
    r"|domain kaufen|buy this domain|this domain is parked|domain (ist )?geparkt"
    r"|sedo(parking)?\b|parkingcrew|bodis\.com|dan\.com|afternic|hugedomains"
    r"|this domain has (recently been|been) registered|diese domain wurde .{0,30}registriert"
    r"|domain .{0,30}reserviert|reserved domain|is available for purchase)",
    re.I,
)
_PLACEHOLDER = re.compile(
    r"(hier entsteht|under construction|im aufbau|baustelle|coming soon|demn[äa]chst online"
    r"|wartungsarbeiten|maintenance mode|website (is )?(currently )?(under|in) maintenance"
    r"|bald (verf[üu]gbar|online|ist es soweit))",
    re.I,
)
_DEFAULT_PAGE = re.compile(
    r"(welcome to nginx|apache2? (ubuntu |debian )?default page|it works!|default web site page"
    r"|plesk|test page for the apache|iis windows server|webspace (ist )?eingerichtet"
    r"|this is the default (welcome )?page|default (index|server) page|domain .{0,30}(eingerichtet|aufgeschaltet)"
    r"|ihre (neue )?(domain|homepage|webseite) .{0,40}(eingerichtet|vorbereitet))",
    re.I,
)
_CHALLENGE = re.compile(
    r"(just a moment|checking your browser|cf-browser-verification|attention required! \| cloudflare"
    r"|verify you are human|captcha|ddos-guard|access denied)",
    re.I,
)


def site_status(
    text: str,
    final_url: Optional[str],
    host: str,
    http_status: Optional[int] = None,
) -> Tuple[str, str]:
    """Return (status, evidence).

    status: unreachable | http_error | parked | placeholder | default_page |
            challenge | redirect_other_domain | live.
    http_error: the landing page answered with HTTP >= 400 and a short body
    (e.g. a hoster's 503 page or a 403 block page).
    Short pages are checked for parking/placeholder phrases; long pages that
    merely mention 'Wartungsarbeiten' stay live.
    """
    if final_url is None:
        return "unreachable", f"http_status={http_status}"
    t = (text or "")[:6000]
    short = len((text or "").strip()) < 1500
    if http_status is not None and http_status >= 400 and short:
        return "http_error", f"http_status={http_status}"
    m = _PARKED.search(t)
    if m and (short or len(_PARKED.findall(t)) >= 2):
        return "parked", m.group(0)
    m = _DEFAULT_PAGE.search(t)
    if m and short:
        return "default_page", m.group(0)
    m = _PLACEHOLDER.search(t)
    if m and short:
        return "placeholder", m.group(0)
    m = _CHALLENGE.search(t)
    if m and short:
        return "challenge", m.group(0)
    final_host = urlparse(final_url).netloc.lower()
    if final_host and registered_domain(final_host) != registered_domain(host):
        return "redirect_other_domain", final_host
    return "live", ""


# ---------------------------------------------------------------------------
# Technology / CMS
# ---------------------------------------------------------------------------

# (label, family, regex over generator + asset/script URLs + head of HTML)
_TECH_RULES: List[Tuple[str, str, re.Pattern]] = [
    ("blogger", "blog_platform", re.compile(r"blogger|blogspot\.com|www\.blogger\.com/static|bp\.blogspot", re.I)),
    ("wordpress_com", "blog_platform", re.compile(r"\.wordpress\.com/|wp\.com/(_static|i/)|s\d\.wp\.com", re.I)),
    ("wix", "site_builder", re.compile(r"wix\.com|wixstatic\.com|_wixCIDX|wix-warmup-data", re.I)),
    ("jimdo", "site_builder", re.compile(r"jimdo|jimcdn\.com|jimstatic\.com", re.I)),
    ("squarespace", "site_builder", re.compile(r"squarespace", re.I)),
    ("webflow", "site_builder", re.compile(r"webflow|website-files\.com", re.I)),
    ("weebly", "site_builder", re.compile(r"weebly|editmysite\.com", re.I)),
    ("ionos_mywebsite", "site_builder", re.compile(r"mywebsite|website-editor\.net|ionos|homepage-baukasten|1und1|1&1", re.I)),
    ("duda", "site_builder", re.compile(r"multiscreensite\.com|cdn-website\.com|dudaone", re.I)),
    ("godaddy", "site_builder", re.compile(r"img1\.wsimg\.com|godaddy", re.I)),
    ("strato_sitebuilder", "site_builder", re.compile(r"strato.{0,20}(sitebuilder|homepage-?baukasten)|sitebuilder\.strato|cm4all", re.I)),
    ("one_com", "site_builder", re.compile(r"one\.com/|onecom", re.I)),
    ("shopify", "shop_system", re.compile(r"cdn\.shopify\.com|shopify", re.I)),
    ("shopware", "shop_system", re.compile(r"shopware|/bundles/storefront/", re.I)),
    ("magento", "shop_system", re.compile(r"magento|/static/version\d+/|mage/cookies", re.I)),
    ("woocommerce", "shop_system", re.compile(r"woocommerce", re.I)),
    ("gambio", "shop_system", re.compile(r"gambio", re.I)),
    ("oxid", "shop_system", re.compile(r"oxid ?esales|/out/flow/|oxid", re.I)),
    ("jtl", "shop_system", re.compile(r"jtl-?shop|jtl-software", re.I)),
    ("prestashop", "shop_system", re.compile(r"prestashop", re.I)),
    ("wordpress", "cms_wordpress", re.compile(r"wordpress|/wp-content/|/wp-includes/|wp-json|wp-emoji", re.I)),
    ("joomla", "cms_other", re.compile(r"joomla|/media/jui/|/components/com_|option=com_|/media/system/js/", re.I)),
    ("typo3", "cms_other", re.compile(r"typo3|/typo3conf/|/typo3temp/|/fileadmin/", re.I)),
    ("drupal", "cms_other", re.compile(r"drupal|/sites/default/files/|/sites/all/(themes|modules)/", re.I)),
    ("contao", "cms_other", re.compile(r"contao|/assets/contao/|/system/modules/", re.I)),
    ("neos", "cms_other", re.compile(r"neos( cms)?\b|/_resources/static/packages/", re.I)),
    ("craft", "cms_other", re.compile(r"craft cms|craftcms", re.I)),
    ("ghost", "cms_other", re.compile(r"\bghost \d|ghost\.io", re.I)),
    ("hugo", "static_generator", re.compile(r"\bhugo \d", re.I)),
    ("jekyll", "static_generator", re.compile(r"jekyll", re.I)),
    ("gatsby", "spa_framework", re.compile(r"gatsby|___gatsby", re.I)),
    ("nextjs", "spa_framework", re.compile(r"__next_data__|/_next/static/|next\.js", re.I)),
    ("nuxt", "spa_framework", re.compile(r"__nuxt|/_nuxt/", re.I)),
    ("angular", "spa_framework", re.compile(r"ng-version=|angular(\.min)?\.js|zone\.js", re.I)),
    ("react", "spa_framework", re.compile(r"data-reactroot|react(-dom)?(\.production)?(\.min)?\.js", re.I)),
    ("vue", "spa_framework", re.compile(r"vue(\.runtime)?(\.global)?(\.prod|\.min)?\.js|data-v-[0-9a-f]{8}|data-server-rendered", re.I)),
    ("svelte", "spa_framework", re.compile(r"svelte-[0-9a-z]{5,}|__sveltekit", re.I)),
]

_SPA_SHELL = re.compile(
    r"<div[^>]+id=[\"'](root|app|__next|__nuxt|___gatsby|svelte)[\"'][^>]*>\s*</div>", re.I
)


# generator values that name an HTML editor (desktop WYSIWYG) or plug-in noise
_GEN_EDITOR = re.compile(
    r"MSHTML|FrontPage|Dreamweaver|NetObjects|GoLive|Namo|WYSIWYG Web Builder|Microsoft Word|"
    r"NetFusion|Web Studio|Website X5|RapidWeaver|iWeb|Sandvox|Freeway|Homepage ?Baukasten|"
    r"Evrsoft|Mozilla/|Microsoft Visual Studio|HTML Tidy|Serif WebPlus|Xara|Muse",
    re.I,
)
_GEN_NOISE = re.compile(
    r"^(Site Kit|Elementor|Powered by|WPML|Divi|Yoast|Slider|Visual Composer|All in One SEO|"
    r"Rank Math|WooCommerce|Gravity|Jetpack|Bootstrap|Swiper|Redux|Avada|Enfold|Astra)",
    re.I,
)


def detect_tech(
    html: str,
    headers: Optional[Dict[str, str]] = None,
    page_url: str = "",
    scan: Optional[PageScan] = None,
) -> Dict[str, object]:
    """Classify the site technology.

    Returns {"tech": label, "family": family, "server_lang": php|asp.net|java|None,
    "generator": str, "spa_shell": bool, "frameset": bool, "signals": [...]}.
    Order: generator meta wins; then asset/script URL signatures; then headers;
    falls back to custom_php / static_html / unknown.
    """
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    scan = scan or scan_html(html, page_url or "http://x/")
    gen = " | ".join(g for g in scan.generators if g)
    assets = " ".join(scan.script_srcs + scan.asset_urls)
    head = (html or "")[:200_000]
    hdr = " ".join(
        f"{k}: {headers.get(k, '')}"
        for k in ("x-powered-by", "server", "x-generator", "x-wix-request-id", "x-shopify-stage", "x-drupal-cache", "x-jimdo-instance", "set-cookie")
        if headers.get(k)
    )
    signals: List[str] = []
    found: Optional[Tuple[str, str]] = None

    for source_name, source in (("generator", gen), ("assets", assets), ("headers", hdr), ("html", head)):
        if not source:
            continue
        for label, family, rx in _TECH_RULES:
            # the full HTML is noisy (links to wordpress.org etc.): only accept
            # strong signatures there, not bare product names
            if source_name == "html" and label in {
                "wordpress", "joomla", "typo3", "drupal", "contao", "shopify", "wix",
                "jimdo", "squarespace", "webflow", "weebly", "ionos_mywebsite", "godaddy",
                "magento", "gambio", "oxid", "neos", "ghost", "one_com", "strato_sitebuilder", "jtl",
                "prestashop", "craft", "hugo", "jekyll", "react",
            }:
                strong = {
                    "wordpress": r"/wp-content/|/wp-includes/",
                    "joomla": r"/media/jui/|/components/com_|option=com_",
                    "typo3": r"/typo3conf/|/typo3temp/",
                    "drupal": r"/sites/default/files/|drupal-settings-json|Drupal\.settings",
                    "contao": r"/assets/contao/",
                    "shopify": r"cdn\.shopify\.com|Shopify\.theme",
                    "wix": r"static\.wixstatic\.com|wix-warmup-data",
                    "jimdo": r"jimcdn\.com|jimdo-?static|jimstatic",
                    "squarespace": r"static1\.squarespace\.com",
                    "webflow": r"data-wf-page|website-files\.com",
                    "weebly": r"editmysite\.com",
                    "ionos_mywebsite": r"website-editor\.net",
                    "godaddy": r"img1\.wsimg\.com",
                    "magento": r"Mage\.Cookies|/static/version\d+/",
                    "gambio": r"gambio_",
                    "strato_sitebuilder": r"cm4all",
                    "react": r"data-reactroot",
                }.get(label)
                if not strong or not re.search(strong, head, re.I):
                    continue
                m = re.search(strong, head, re.I)
            else:
                m = rx.search(source)
            if m:
                signals.append(f"{source_name}:{label}:{m.group(0)[:40]}")
                if found is None:
                    found = (label, family)
                break
        if found:
            break

    # SPA framework overlay: record even when a CMS was found
    spa_shell = bool(_SPA_SHELL.search(head))
    spa = None
    for label, family, rx in _TECH_RULES:
        if family == "spa_framework" and rx.search(head):
            spa = label
            break

    server_lang = None
    xpb = headers.get("x-powered-by", "") + " " + headers.get("set-cookie", "")
    if re.search(r"php", xpb, re.I):
        server_lang = "php"
        signals.append("header:php")
    elif re.search(r"asp\.net|aspsessionid", xpb, re.I) or headers.get("x-aspnet-version") or "__VIEWSTATE" in head:
        server_lang = "asp.net"
        signals.append("asp.net")
    elif re.search(r"jsessionid|servlet|tomcat", xpb, re.I):
        server_lang = "java"
    php_links = [l.url for l in scan.links if re.search(r"\.php(\?|$|#)", urlparse(l.url).path + "?", re.I)]
    if server_lang is None and (php_links or re.search(r"\.php(\?|$)", page_url or "")):
        server_lang = "php"
        signals.append(f"url:.php ({len(php_links)} links)")

    gen_clean = [g for g in scan.generators if g and not _GEN_NOISE.search(g)]
    if found:
        tech, family = found
    elif gen_clean and _GEN_EDITOR.search(gen_clean[0]):
        tech, family = "desktop_editor", "static_html"
        signals.append("generator:editor:" + gen_clean[0][:40])
    elif gen_clean:
        tech, family = "other_cms", "cms_other"
        signals.append("generator:other:" + gen_clean[0][:40])
    elif spa and (spa_shell or len(scan.links) < 5):
        tech, family = spa, "spa_framework"
    elif server_lang == "php":
        tech, family = "custom_php", "custom_php"
    elif server_lang in ("asp.net", "java"):
        tech, family = server_lang, "custom_other"
    else:
        same_host = [
            urlparse(l.url).path
            for l in scan.links
            if l.url and urlparse(l.url).netloc == urlparse(page_url).netloc
        ]
        html_links = [p for p in same_host if re.search(r"\.s?html?$", p, re.I)]
        if same_host and len(html_links) >= max(1, len(same_host) // 3):
            tech, family = "static_html", "static_html"
            signals.append(f"url:.html ({len(html_links)}/{len(same_host)} links)")
        elif spa:
            tech, family = spa, "spa_framework"
        else:
            tech, family = "unknown", "unknown"

    return {
        "tech": tech,
        "family": family,
        "spa_framework": spa,
        "spa_shell": spa_shell,
        "server_lang": server_lang,
        "generator": gen,
        "frameset": scan.frames > 0,
        "server": headers.get("server"),
        "signals": signals,
    }


def wordpress_version(generator: str) -> Optional[str]:
    m = re.search(r"wordpress\s+(\d+\.\d+)", generator or "", re.I)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Imprint links and imprint-like text
# ---------------------------------------------------------------------------

_IMPRINT_LABEL = re.compile(
    r"\b(impressum|imprint|legal notice|legal-notice|anbieterkennzeichnung|rechtliche hinweise"
    r"|rechtliches|offenlegung|mentions l[ée]gales|site notice|kontakt\s*(&|und|/)\s*impressum)\b",
    re.I,
)
_IMPRINT_PATH = re.compile(
    r"(?<![a-z])(impressum|imprint|legal-?notice|anbieterkennzeichnung|rechtliche-?hinweise|offenlegung|site-?notice)",
    re.I,
)


@dataclass
class ImprintCandidate:
    url: str
    kind: str  # same_host | other_host | fragment | javascript
    label: str
    score: int


def find_imprint_links(scan: PageScan, page_url: str) -> List[ImprintCandidate]:
    """Imprint link candidates, best first.

    Unlike fetch.py this matches path + query, anchor text, title, aria-label and
    <img alt>, honours <base href>, and keeps fragment/javascript links (modal
    or same-page imprints) as their own kind.
    """
    page_host = urlparse(page_url).netloc.lower()
    out: Dict[str, ImprintCandidate] = {}
    for link in scan.links:
        label_src = " ".join([link.text, link.title, link.aria_label])
        href = link.href.strip()
        parsed = urlparse(link.url) if link.url else None
        path_q = (parsed.path + "?" + parsed.query) if parsed else ""
        by_label = bool(_IMPRINT_LABEL.search(label_src))
        by_path = bool(_IMPRINT_PATH.search(path_q))
        by_js = bool(_IMPRINT_PATH.search(link.onclick + " " + href)) and not link.url
        if not (by_label or by_path or by_js):
            continue
        if href.lower().startswith("mailto:"):
            continue
        if not link.url:
            kind = "javascript"
            key = "js:" + (href or link.onclick)[:80]
        elif href.startswith("#") or (
            parsed.fragment and parsed._replace(fragment="").geturl().rstrip("/") == page_url.split("#")[0].rstrip("/")
        ):
            kind = "fragment"
            key = link.url
        elif parsed.netloc.lower() == page_host or registered_domain(parsed.netloc) == registered_domain(page_host):
            kind = "same_host"
            key = link.url.split("#")[0]
        else:
            kind = "other_host"
            key = link.url.split("#")[0]
        score = (2 if by_label else 0) + (2 if by_path else 0) + (1 if kind == "same_host" else 0)
        if re.search(r"datenschutz|privacy", label_src + path_q, re.I) and not re.search(
            r"impressum|imprint", label_src + path_q, re.I
        ):
            score -= 2
        lab = re.sub(r"\s+", " ", label_src).strip()[:60]
        if key not in out or out[key].score < score:
            out[key] = ImprintCandidate(url=key if kind != "javascript" else href, kind=kind, label=lab, score=score)
    order = {"same_host": 0, "other_host": 1, "fragment": 2, "javascript": 3}
    return sorted(out.values(), key=lambda c: (-c.score, order[c.kind], len(c.url)))


_LEGAL_MARKERS = [
    ("angaben_gemaess", r"angaben gem(ä|ae|a)(ß|ss)"),
    ("p5_tmg_ddg", r"§\s*5\s*(tmg|ddg|ecg)|§\s*5\s*abs"),
    ("p55_rstv_mstv", r"§\s*(55|18)\s*(abs\.?\s*2\s*)?(rstv|mstv)"),
    ("verantwortlich", r"verantwortlich (f(ü|ue)r den inhalt|i\.?\s?s\.?\s?d\.?|im sinne)|v\.i\.s\.d\.p"),
    ("handelsregister", r"handelsregister|registergericht|amtsgericht\s+\w+.{0,20}hrb?\s*\d"),
    ("ust_id", r"ust\.?-?\s?id|umsatzsteuer-?\s?identifikations|uid-?nr|mwst-?nr|vat (id|number)"),
    ("vertreten_durch", r"vertreten durch|vertretungsberechtigt|gesch(ä|ae)ftsf(ü|ue)hr"),
    ("offenlegung_medieng", r"offenlegung|§\s*25\s*medieng|mediengesetz"),
    ("inhaber", r"\binhaber(in)?\b|\binh\.\s"),
    ("legal_notice_en", r"legal notice|information (according|pursuant) to"),
]


def imprint_markers(text: str) -> List[str]:
    t = (text or "").lower()
    return [name for name, rx in _LEGAL_MARKERS if re.search(rx, t)]


def is_imprint_text(text: str) -> bool:
    """Imprint-like if the word Impressum/Imprint plus >=1 legal marker, or >=2 markers."""
    marks = imprint_markers(text)
    word = bool(re.search(r"\b(impressum|imprint)\b", text or "", re.I))
    return (word and len(marks) >= 1) or len(marks) >= 2


# ---------------------------------------------------------------------------
# Addresses (rule-based finder; the model check is in the pilot script)
# ---------------------------------------------------------------------------

_STREET_SUFFIX = (
    r"(?:stra(?:ß|ss)e|str\.|weg|platz|gasse|allee|ring|damm|ufer|chaussee|steig|pfad|markt|hof|berg"
    r"|graben|wall|kamp|feld|garten|park|zeile|br(?:ü|ue)cke|tor|winkel|anger|au|bogen|grund|stieg)"
)
# street line: "Hauptstr. 12a", "Am Markt 3", "Alte Gasse 4-6"
_STREET = re.compile(
    r"(?P<street>[A-ZÄÖÜ][\wäöüßÄÖÜ\.\-]*(?:[ \-][\wäöüßÄÖÜ\.\-]+){0,4}?\s*" + _STREET_SUFFIX + r"?)\s+(?P<num>\d{1,4}\s?[a-zA-Z]?(?:\s?[-/]\s?\d{1,4}[a-zA-Z]?)?)\b"
)
_POSTCODE_TOWN = re.compile(
    r"(?<![\d\-/+.,])(?:(D|DE|A|AT|CH)\s?-\s?)?(\d{5}|\d{4})\s+([A-ZÄÖÜ][\wäöüßÄÖÜ\-\.]+(?:[ /\-]+(?:[A-ZÄÖÜa-z(][\wäöüßÄÖÜ\-\.)]*)){0,3})"
)
_POBOX = re.compile(r"\b(postfach|p\.?\s?o\.?\s?box|postbox)\s*:?\s*(\d[\d \.]{1,10})", re.I)
_YEARISH = re.compile(r"^(19|20)\d\d$")


@dataclass
class AddressHit:
    street: str
    number: str
    postcode: str
    town: str
    country_hint: str  # DE, AT, CH, AT_or_CH
    po_box: bool = False


def _country_from(postcode: str, prefix: Optional[str], context: str) -> str:
    if prefix:
        return {"D": "DE", "DE": "DE", "A": "AT", "AT": "AT", "CH": "CH"}[prefix.upper()]
    if len(postcode) == 5:
        return "DE"
    if re.search(r"schweiz|switzerland|suisse|svizzera", context, re.I):
        return "CH"
    if re.search(r"(ö|oe)sterreich|austria", context, re.I):
        return "AT"
    return "AT_or_CH"


def find_addresses(text: str) -> List[AddressHit]:
    """Find postal addresses: a street line (or Postfach) within 120 chars before
    'postcode town'. Lines are joined so 'Hauptstr. 1\\n12345 Ort' matches.
    Deduplicated on (postcode, town, street)."""
    flat = re.sub(r"[ \t ]+", " ", text or "")
    hits: List[AddressHit] = []
    seen = set()
    for m in _POSTCODE_TOWN.finditer(flat):
        prefix, pc, town = m.group(1), m.group(2), m.group(3).strip(" .,-")
        if len(pc) == 4 and _YEARISH.match(pc) and not prefix:
            continue
        if len(pc) == 4 and pc.startswith("0"):
            continue
        town = re.split(r"\s+(Tel|Telefon|Fon|Fax|E-?Mail|Mail|Web|www|Internet|Mobil|Handy|Deutschland|Germany|Österreich|Schweiz)\b", town, flags=re.I)[0]
        # sentence end after the town ("... 94151 Mauth. Buchwaldstraße ...")
        town = re.split(r"(?<=[a-zäöüß]{3})\.\s", town)[0]
        town = town.strip(" .,-")
        if len(town) < 2 or town.lower() in {"uhr", "euro", "eur", "mal", "tage", "jahre", "stück", "mitglieder"}:
            continue
        window = flat[max(0, m.start() - 120) : m.start()]
        window_last = re.split(r"[\n|•]{2,}", window)[-1]
        pob = list(_POBOX.finditer(window_last))
        streets = list(_STREET.finditer(window_last))
        if pob and (not streets or pob[-1].start() >= streets[-1].start()):
            key = (pc, town.lower(), "postfach")
            if key not in seen:
                seen.add(key)
                hits.append(AddressHit("Postfach", pob[-1].group(2).strip(), pc, town, _country_from(pc, prefix, flat), po_box=True))
            continue
        if not streets:
            continue
        s = streets[-1]
        # the street must end right before the postcode (allow separators)
        gap = window_last[s.end() :]
        if len(gap) > 25 or re.search(r"\d{3,}", gap):
            continue
        street = s.group("street").strip()
        # drop a preceding sentence ("Mauth. Buchwaldstraße" -> "Buchwaldstraße")
        street = re.split(r"(?<=[a-zäöüß]{3})\.\s+(?=\S)", street)[-1]
        if _YEARISH.match(s.group("num").strip()) or street.lower() in {"tel", "fax", "telefon", "seit", "jahr"}:
            continue
        key = (pc, town.lower(), street.lower())
        if key in seen:
            continue
        seen.add(key)
        hits.append(AddressHit(street, s.group("num").strip(), pc, town, _country_from(pc, prefix, flat)))
    return hits


def address_flags(hits: List[AddressHit]) -> Dict[str, object]:
    # one location = postcode + house number (+ first letters of the street);
    # town spelling variants ("Geislingen / Steige" vs "Geislingen") and
    # Str./Straße variants of the same address collapse
    distinct = {
        (h.postcode, re.sub(r"\s", "", (h.number or "").lower()), re.sub(r"[^a-zäöü]", "", (h.street or "").lower().split("\n")[-1])[:4])
        for h in hits
        if not h.po_box
    } | {(h.postcode, "pob") for h in hits if h.po_box}
    countries = sorted({h.country_hint for h in hits})
    return {
        "n_addresses": len(hits),
        "n_distinct_locations": len(distinct),
        "multi_address": len(distinct) >= 2,
        "po_box": any(h.po_box for h in hits),
        "po_box_only": bool(hits) and all(h.po_box for h in hits),
        "address_countries": countries,
    }


# ---------------------------------------------------------------------------
# Operator type from legal-form tokens
# ---------------------------------------------------------------------------

_PUBLIC = re.compile(
    r"(k(ö|oe)rperschaft des (ö|oe)ffentlichen rechts|anstalt des (ö|oe)ffentlichen rechts|\bK[dö]ö?R\b"
    r"|\b(stadtverwaltung|gemeindeverwaltung|kreisverwaltung|landratsamt|bezirksamt|rathaus|b(ü|ue)rgermeister(in)?)\b"
    r"|\b(ministerium|bundesamt|landesamt|beh(ö|oe)rde|universit(ä|ae)t|hochschule|marktgemeinde|amtsgemeinde"
    r"|verbandsgemeinde|landkreis|kirchengemeinde|pfarrei|bistum|erzbistum|kantonale?)\b"
    r"|\b(stadt|gemeinde|markt)\s+[A-ZÄÖÜ][a-zäöüß]+\s+(vertreten durch|wird gesetzlich vertreten))",
    re.I,
)
_ASSOC = re.compile(r"(\be\.\s?V\.|\beingetragener verein\b|\bverein\b|\bstiftung\b|\bverband\b|\bvereinsregister\b|\bVR\s?\d{2,})", re.I)
_CORP = re.compile(
    r"(\bGmbH\b|\bgGmbH\b|\bmbH\b|\bAG\b|\bUG\b|\bSE\b|\bKGaA\b|\bKG\b|\bOHG\b|\bGbR\b|\bPartG|\bPartGmbB\b|\beG\b"
    r"|\bLtd\.?\b|\bLLC\b|\bInc\.?\b|\bS\.?à\.?r\.?l\b|\bGes\.?m\.?b\.?H\b|\bOG\b|\bHRB\s?\d|\bHRA\s?\d|\bFN\s?\d+\s?[a-z]\b|CHE-\d{3})"
)
_SOLE = re.compile(
    r"(\be\.\s?K\.|\beingetragene(r)? kauf(mann|frau)\b|\binhaber(in)?\b|\binh\.\s|\beinzelunternehm|\bfreiberuf"
    r"|\bkleinunternehmer|§\s*19\s*ustg|\bselbst(st)?(ä|ae)ndig|\bsteuernummer\b"
    r"|\b(rechtsanw(ä|ae)lt(in)?|steuerberater(in)?|architekt(in)?|(zahn|tier)?(ä|ae)rzt(in)?|heilpraktiker(in)?|physiotherapeut(in)?|fotograf(in)?|psychotherapeut(in)?)\b"
    r"|\bberufsbezeichnung\b|\bkammer\b)",
    re.I,
)
_PRIVATE = re.compile(
    r"(\bprivate?\s+(homepage|website|webseite|seite|blog)|\bprivatperson|\bprivates\s+(blog|projekt)|nicht[- ]kommerziell"
    r"|\bpers(ö|oe)nliche(s|r)?\s+(homepage|website|webseite|blog)|\bhobby(seite|projekt)?\b|ausschlie(ß|ss)lich private)",
    re.I,
)


def operator_type_rules(text: str) -> Tuple[str, List[str]]:
    """Rule-based operator type from imprint text.

    Returns (label, tokens); label in public_body, association, corporate,
    sole_trader, private_person, unknown. Priority: public > association >
    corporate > sole_trader > private_person (a GmbH that sponsors a Verein is
    corporate only if no association token appears near the top of the text).
    """
    t = (text or "")[:4000]
    toks = []
    for name, rx in (("public", _PUBLIC), ("assoc", _ASSOC), ("corp", _CORP), ("sole", _SOLE), ("private", _PRIVATE)):
        m = rx.search(t)
        if m:
            toks.append(f"{name}:{m.group(0).strip()[:30]}")
    names = [x.split(":")[0] for x in toks]
    if "public" in names:
        return "public_body", toks
    if "assoc" in names and ("corp" not in names or t.lower().find("e.v") < t.find(re.search(_CORP, t).group(0))):
        return "association", toks
    if "corp" in names:
        return "corporate", toks
    if "sole" in names:
        return "sole_trader", toks
    if "private" in names:
        return "private_person", toks
    return "unknown", toks


# ---------------------------------------------------------------------------
# Rendering need, modality, location
# ---------------------------------------------------------------------------


def rendering_need(
    static_landing_chars: int,
    rendered_landing_chars: int,
    static_imprint_found: bool,
    rendered_imprint_found: bool,
    static_imprint_has_address: bool,
    rendered_imprint_has_address: bool,
    static_fetch_ok: bool = True,
) -> Tuple[str, str]:
    """Label whether a plain HTTP fetch is enough to get the imprint address.

    static_blocked: the plain HTTP fetch failed (TLS error, HTTP >= 400, bot
        block, rate limit) but the browser got the address; this is a fetch
        failure, not a rendering need, and is kept apart;
    js_required: the address (or the imprint itself) is only reachable after
        rendering;
    js_content: the landing page is a JS shell (static text < 25% of rendered
        and < 300 chars), whether or not the imprint is static;
    static_ok: static fetch reaches the same address as rendering;
    none: neither variant finds an imprint address.
    """
    if rendered_imprint_has_address and not static_imprint_has_address and not static_fetch_ok:
        return "static_blocked", "static fetch failed, browser succeeded"
    if rendered_imprint_has_address and not static_imprint_has_address:
        why = "imprint only after render" if (rendered_imprint_found and not static_imprint_found) else "address only after render"
        return "js_required", why
    shell = static_landing_chars < 300 and rendered_landing_chars > max(4 * static_landing_chars, 300)
    if static_imprint_has_address:
        return ("js_content" if shell else "static_ok"), (
            f"static {static_landing_chars} vs rendered {rendered_landing_chars} chars"
        )
    if shell:
        return "js_content", f"static {static_landing_chars} vs rendered {rendered_landing_chars} chars"
    return "none", ""


def screenshot_candidate(
    imprint_found: bool,
    imprint_text: str,
    has_address_in_text: bool,
    images: Iterable[Tuple[str, str]],
) -> Tuple[bool, str]:
    """Heuristic pre-filter for 'address only in an image' (confirmed by a
    vision model in the pilot): imprint page reached, no address in rendered
    text, and the page has at least one content image or very little text."""
    if not imprint_found or has_address_in_text:
        return False, ""
    imgs = [(s, a) for s, a in images if s and not re.search(r"logo|icon|sprite|pixel|spacer|\.svg", s + a, re.I)]
    named = [s for s, a in imgs if re.search(r"impressum|imprint|adresse|anschrift|kontakt", s + " " + a, re.I)]
    if named:
        return True, f"image named {named[0][:60]}"
    if imgs and len((imprint_text or "").strip()) < 1500:
        return True, f"{len(imgs)} images, {len((imprint_text or '').strip())} chars text"
    return False, ""


_BIDI = re.compile(r"unicode-bidi\s*:\s*bidi-override|direction\s*:\s*rtl", re.I)


def obfuscation_signals(html: str) -> List[str]:
    """Anti-scraping tricks that break text extraction of imprint data."""
    out = []
    if _BIDI.search(html or ""):
        out.append("css_bidi_reversed_text")
    if re.search(r"<canvas", html or "", re.I):
        out.append("canvas")
    if re.search(r"(\[at\]|\(at\)| at |&#64;|&#x40;)", html or "", re.I) and re.search(r"impressum", html or "", re.I):
        out.append("email_obfuscation")
    return out


# Imprint links to these hosts are not the operator's imprint: registrar or
# hoster placeholder pages and imprint generators (seen in the E8 pilot).
_FOREIGN_IMPRINT_HOSTS = re.compile(
    r"(^|\.)(e-recht24\.de|united-domains\.de|ionos\.(de|com)|1und1\.de|strato\.de|hosteurope\.de|"
    r"df\.eu|checkdomain\.de|all-inkl\.com|netcup\.de|hetzner\.(de|com)|godaddy\.com|"
    r"impressum-generator\.de|datenschutz-generator\.de)$",
    re.I,
)


def imprint_location(
    best: Optional[ImprintCandidate],
    landing_is_imprint: bool,
    imprint_reached: bool,
) -> str:
    """separate_page | other_domain | landing_page | modal_or_fragment | probe_only | none."""
    if best is not None and imprint_reached:
        if best.kind == "same_host":
            return "separate_page"
        if best.kind == "other_host":
            if _FOREIGN_IMPRINT_HOSTS.search(urlparse(best.url).hostname or ""):
                return "none"
            return "other_domain"
        if best.kind in ("fragment", "javascript"):
            return "modal_or_fragment"
    if landing_is_imprint:
        return "landing_page"
    if imprint_reached:
        return "probe_only"
    return "none"


def pdf_imprint(cands: List[ImprintCandidate]) -> bool:
    return any(re.search(r"\.pdf($|\?)", c.url, re.I) for c in cands[:3])


# ---------------------------------------------------------------------------
# Age
# ---------------------------------------------------------------------------

AGE_BINS = [(0, 2009, "<2010"), (2010, 2017, "2010-2017"), (2018, 2022, "2018-2022"), (2023, 9999, ">=2023")]


def age_bin(year: Optional[int]) -> str:
    if not year:
        return "no_capture"
    for lo, hi, lab in AGE_BINS:
        if lo <= year <= hi:
            return lab
    return "no_capture"


def copyright_years(text: str) -> List[int]:
    """Years in copyright notices ('© 2009-2014', 'Copyright 2021'); used as a
    freshness signal (max year) next to Wayback first capture (site age)."""
    years: List[int] = []
    for m in re.finditer(r"(©|\(c\)|copyright)\s*(\d{4})(\s*[-–]\s*(\d{4}))?", text or "", re.I):
        for g in (m.group(2), m.group(4)):
            if g and 1994 <= int(g) <= 2030:
                years.append(int(g))
    return years


def image_only_addresses(vision_addresses: list, dom_text: str) -> list:
    """Postcodes of addresses the vision model read off the screenshot whose
    postcode AND street are both absent from the rendered DOM text: the address
    is only available as pixels (screenshot-required). Requiring both absent
    filters OCR digit slips (56170 read as 56370) and spaced postcodes ("28 719")."""
    dom = dom_text or ""
    text_digits = set(re.findall(r"(?<!\d)\d{4,5}(?!\d)", dom))
    text_digits |= {re.sub(r"\s", "", m) for m in re.findall(r"(?<!\d)\d{2} \d{3}(?!\d)", dom)}
    low = dom.lower()
    out = []
    for a in vision_addresses or []:
        a = a or {}
        pc = re.sub(r"\D", "", str(a.get("postcode") or ""))
        if len(pc) not in (4, 5) or pc in text_digits or pc in out:
            continue
        street = re.sub(r"[^a-zäöüß]", "", str(a.get("street") or "").lower())[:5]
        if len(street) >= 4 and street in re.sub(r"[^a-zäöüß]", "", low):
            continue
        out.append(pc)
    return out
