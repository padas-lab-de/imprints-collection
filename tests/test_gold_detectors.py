"""Unit tests for src/ic/gold/detectors.py on inline HTML (no network)."""

from ic.gold.detectors import (
    ImprintCandidate,
    address_flags,
    age_bin,
    copyright_years,
    detect_tech,
    find_addresses,
    find_imprint_links,
    image_only_addresses,
    imprint_location,
    is_imprint_text,
    obfuscation_signals,
    operator_type_rules,
    rendering_need,
    scan_html,
    screenshot_candidate,
    site_status,
    tld_class,
)

WP = """<html><head><meta name="generator" content="WordPress 5.2.1">
<link rel="stylesheet" href="/wp-content/themes/x/style.css"></head>
<body><a href="/impressum/">Impressum</a><a href="/datenschutz/">Datenschutz</a></body></html>"""

BLOGGER = """<html><head><meta content='blogger' name='generator'/></head><body>
<a href='https://foo.blogspot.com/p/impressum.html'>Impressum</a></body></html>"""

JIMDO = """<html><head><link href="https://assets.jimstatic.com/web.css" rel="stylesheet"></head><body></body></html>"""

TYPO3 = """<html><head><meta name="generator" content="TYPO3 CMS"></head><body>
<img src="/fileadmin/x.jpg"></body></html>"""

NEXT_SHELL = """<html><head><script src="/_next/static/chunks/main.js"></script></head>
<body><div id="__next"></div><script id="__NEXT_DATA__" type="application/json">{}</script></body></html>"""

PHP = """<html><body><a href="index.php?site=home">Home</a><a href="index.php?site=impressum">Impressum</a></body></html>"""

STATIC = """<html><body><a href="index.html">Home</a><a href="about.html">Über</a><a href="impressum.htm">Impressum</a></body></html>"""


def test_tech_wordpress_generator_and_version():
    t = detect_tech(WP, {}, "https://a.de/")
    assert t["tech"] == "wordpress"
    assert t["family"] == "cms_wordpress"
    assert "5.2.1" in t["generator"]


def test_tech_blogger_jimdo_typo3():
    assert detect_tech(BLOGGER, {}, "https://foo.blogspot.com/")["tech"] == "blogger"
    assert detect_tech(JIMDO, {}, "https://a.de/")["tech"] == "jimdo"
    assert detect_tech(TYPO3, {}, "https://a.de/")["tech"] == "typo3"


def test_tech_spa_shell():
    t = detect_tech(NEXT_SHELL, {}, "https://a.de/")
    assert t["family"] == "spa_framework"
    assert t["spa_shell"] is True


def test_tech_custom_php_and_static_html():
    assert detect_tech(PHP, {}, "https://a.de/")["tech"] == "custom_php"
    assert detect_tech("<html></html>", {"X-Powered-By": "PHP/5.6"}, "https://a.de/")["server_lang"] == "php"
    assert detect_tech(STATIC, {}, "https://a.de/")["tech"] == "static_html"


def test_tech_other_generator_and_desktop_editor():
    t = detect_tech('<meta name="generator" content="SIQUANDO Pro (#6114)">', {}, "https://a.de/")
    assert (t["tech"], t["family"]) == ("other_cms", "cms_other")
    t = detect_tech('<meta name="GENERATOR" content="Microsoft FrontPage 4.0">', {}, "https://a.de/")
    assert (t["tech"], t["family"]) == ("desktop_editor", "static_html")
    assert detect_tech('<meta name="generator" content="Site Kit by Google 1.1">', {}, "https://a.de/")["tech"] == "unknown"


def test_tech_ignores_bare_mention_in_body():
    html = "<html><body><p>Wir bauen Seiten mit WordPress und Joomla.</p></body></html>"
    assert detect_tech(html, {}, "https://a.de/")["tech"] == "unknown"


def test_imprint_links_query_base_href_and_kinds():
    html = """<html><head><base href="https://a.de/sub/"></head><body>
    <a href="index.php?id=impressum">Rechtliches</a>
    <a href="#impressum">Impressum</a>
    <a href="javascript:void(0)" onclick="openModal('impressum')">Impressum</a>
    <a href="https://agency.example/impressum">Impressum Agentur</a>
    <a href="/datenschutz">Datenschutz</a></body></html>"""
    scan = scan_html(html, "https://a.de/")
    cands = find_imprint_links(scan, "https://a.de/")
    kinds = {c.kind for c in cands}
    assert {"same_host", "fragment", "javascript", "other_host"} <= kinds
    assert cands[0].url == "https://a.de/sub/index.php?id=impressum"
    assert all("datenschutz" not in c.url for c in cands)


def test_imprint_link_by_img_alt():
    html = '<a href="/p/42"><img src="x.png" alt="Impressum"></a>'
    cands = find_imprint_links(scan_html(html, "https://a.de/"), "https://a.de/")
    assert cands and cands[0].url == "https://a.de/p/42"


def test_is_imprint_text():
    assert is_imprint_text("Impressum\nAngaben gemäß § 5 DDG\nMax Muster")
    assert is_imprint_text("Verantwortlich für den Inhalt: X. Handelsregister: HRB 123")
    assert not is_imprint_text("Willkommen auf unserer Seite. Impressum | Datenschutz")


def test_find_addresses_basic_multi_pobox_at_ch():
    text = """Muster GmbH
Hauptstraße 12a
12345 Musterstadt
Tel. 0123 456789
Niederlassung: Am Markt 3, 54321 Anderort
Postanschrift: Postfach 11 22, 12340 Musterstadt"""
    hits = find_addresses(text)
    flags = address_flags(hits)
    pcs = {h.postcode for h in hits}
    assert {"12345", "54321", "12340"} <= pcs
    assert flags["multi_address"] and flags["po_box"]
    first = [h for h in hits if h.postcode == "12345"][0]
    assert first.street.startswith("Hauptstra") and first.number == "12a" and first.town == "Musterstadt"
    at = find_addresses("Firma X\nMariahilfer Straße 1\nA-1060 Wien\nÖsterreich")
    assert at and at[0].country_hint == "AT" and at[0].town == "Wien"
    ch = find_addresses("Bahnhofstrasse 5, 8001 Zürich, Schweiz")
    assert ch and ch[0].country_hint == "CH"


def test_address_flags_collapse_spelling_variants():
    hits = find_addresses("Neuwiesen 13\n73312 Geislingen / Steige\n...\nNeuwiesen 13, 73312 Geislingen")
    assert len(hits) == 2 and not address_flags(hits)["multi_address"]
    hits = find_addresses("Buchwaldstr. 34a, 94151 Mauth. Buchwaldstraße 34a, 94151 Mauth")
    assert not address_flags(hits)["multi_address"]


def test_find_addresses_rejects_years_and_phone():
    assert find_addresses("Gegründet 2015 Jahre Erfahrung. Tel 0851 509 Passau") == []
    assert find_addresses("Öffnungszeiten 10 Uhr bis 18 Uhr") == []


def test_operator_type_rules():
    assert operator_type_rules("Muster GmbH\nHRB 1234")[0] == "corporate"
    assert operator_type_rules("Sportverein Musterdorf e.V.\nVereinsregister VR 123")[0] == "association"
    assert operator_type_rules("Stadtverwaltung Musterstadt, vertreten durch den Bürgermeister")[0] == "public_body"
    assert operator_type_rules("Inhaber: Max Muster, Kleinunternehmer gem. § 19 UStG")[0] == "sole_trader"
    assert operator_type_rules("Dies ist eine private Homepage von Max Muster")[0] == "private_person"
    assert operator_type_rules("Max Muster\nMusterweg 1")[0] == "unknown"


def test_site_status():
    assert site_status("Diese Domain kann gekauft werden. Sedo", "https://a.de/", "a.de")[0] == "parked"
    assert site_status("Hier entsteht eine neue Internetpräsenz", "https://a.de/", "a.de")[0] == "placeholder"
    assert site_status("Welcome to nginx!", "http://a.de/", "a.de")[0] == "default_page"
    assert site_status("x" * 2000, "https://b.com/", "a.de")[0] == "redirect_other_domain"
    assert site_status("x" * 2000, "https://www.a.de/", "a.de")[0] == "live"
    assert site_status("", None, "a.de")[0] == "unreachable"
    assert site_status("Service Unavailable", "http://a.de/", "a.de", 503)[0] == "http_error"
    assert site_status("x" * 2000, "http://a.de/", "a.de", 403)[0] == "live"


def test_rendering_need():
    assert rendering_need(50, 3000, False, True, False, True)[0] == "js_required"
    assert rendering_need(4000, 4100, True, True, True, True)[0] == "static_ok"
    assert rendering_need(100, 3000, True, True, True, True)[0] == "js_content"
    assert rendering_need(4000, 4000, False, False, False, False)[0] == "none"
    assert rendering_need(0, 3000, False, True, False, True, static_fetch_ok=False)[0] == "static_blocked"


def test_screenshot_candidate():
    imgs = [("/img/impressum.png", ""), ("/logo.png", "Logo")]
    assert screenshot_candidate(True, "Impressum", False, imgs)[0]
    assert not screenshot_candidate(True, "Impressum", True, imgs)[0]
    assert not screenshot_candidate(True, "x" * 3000, False, [("/a.jpg", "")])[0]


def test_obfuscation_and_location_and_age():
    assert "css_bidi_reversed_text" in obfuscation_signals('<span style="unicode-bidi:bidi-override; direction: rtl">ed.a</span>')
    assert imprint_location(None, True, False) == "landing_page"
    assert imprint_location(None, False, False) == "none"
    gen = ImprintCandidate("https://www.e-recht24.de/impressum-generator.html", "other_host", "Impressum", 5)
    assert imprint_location(gen, False, True) == "none"
    uni = ImprintCandidate("https://www.uni-saarland.de/en/legal-notice.html", "other_host", "Impressum", 5)
    assert imprint_location(uni, False, True) == "other_domain"
    assert age_bin(2005) == "<2010" and age_bin(2015) == "2010-2017" and age_bin(2024) == ">=2023"
    assert age_bin(None) == "no_capture"
    assert copyright_years("© 2009 - 2014 Muster") == [2009, 2014]
    assert tld_class("www.a.co.at") == "at" and tld_class("x.info") == "other"


def test_image_only_addresses():
    dom = "Impressum Angaben gemaess 5 TMG Kontakt"
    assert image_only_addresses([{"postcode": "94032", "town": "Passau"}], dom) == ["94032"]
    dom2 = "Impressum Musterweg 1, D-94032 Passau"
    assert image_only_addresses([{"postcode": "94032"}], dom2) == []
    assert image_only_addresses([], dom) == []
    # OCR digit slip: street is in the text, so not image-only
    assert image_only_addresses([{"street": "Musterweg", "postcode": "94023"}], dom2) == []
    assert image_only_addresses([{"street": "Geest", "postcode": "28719"}], "An der Geest 7, 28 719 Bremen") == []
