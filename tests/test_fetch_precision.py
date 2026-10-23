"""E9 precision rules: URL-first ranking, word-boundary keywords, imprint evidence (no network)."""

from resiliparse.parse.html import HTMLTree

import ic.cli.fetch as fetch
from ic.cli.fetch import discover_links, find_imprint
from ic.utils.imprint_utils import has_imprint_evidence, looks_like_error_page


def _imprint_links(html, base="https://example.de/", host="example.de"):
    tree = HTMLTree.parse(html)
    return discover_links(tree.body, base, host)[0].get("impressum", [])


def _page(text):
    return f"<html><body><main><p>{text}</p></main></body></html>"


def _patch(monkeypatch, pages):
    calls = []

    def fake(url, num_redirects=10, retry=False):
        calls.append(url)
        return url, pages.get(url)

    monkeypatch.setattr(fetch, "try_fetch", fake)
    return calls


def test_url_match_ranks_before_anchor_only_match():
    html = (
        '<body><a href="links.html">Links &amp; Partner Impressum</a>'
        '<a href="impressum.html">Impressum</a></body>'
    )
    urls = [u for u, _ in _imprint_links(html)]
    assert urls == ["https://example.de/impressum.html", "https://example.de/links.html"]


def test_url_match_group_keeps_own_host_then_shortest():
    html = (
        '<body><a href="https://other.com/impressum">x</a>'
        '<a href="/a/b/c/impressum">x</a><a href="/impressum">x</a></body>'
    )
    urls = [u for u, _ in _imprint_links(html)]
    assert urls == [
        "https://example.de/impressum",
        "https://example.de/a/b/c/impressum",
        "https://other.com/impressum",
    ]


def test_english_keywords_need_word_boundary():
    for href in ["/imprint-methods", "/custom-imprinted-pins", "/imprinted-pins", "/blueprint"]:
        assert _imprint_links(f'<body><a href="{href}">Products</a></body>') == [], href
    assert _imprint_links('<body><a href="/x">Imprinted pins</a></body>') == []
    for href in ["/imprint.html", "/en/legal-notice/", "/en-imprint", "/x?page=imprint", "/legal-notices"]:
        assert _imprint_links(f'<body><a href="{href}">x</a></body>'), href


def test_impressumspflicht_article_is_not_an_imprint_link():
    assert _imprint_links('<body><a href="/impressumspflicht">Article</a></body>') == []
    assert _imprint_links('<body><a href="/agb-impressum/">AGB</a></body>')


def test_evidence():
    assert has_imprint_evidence("Impressum Angaben gemäß § 5 TMG Max Mustermann")
    assert has_imprint_evidence("Impressum\nMusterstr. 1\n91052 Erlangen")
    assert has_imprint_evidence("Legal notice. Commercial register: HRB 1")
    assert not has_imprint_evidence("Impressum | Datenschutz | Kontakt")
    assert not has_imprint_evidence("Imprint methods for promotional products")
    assert not has_imprint_evidence("")


def test_error_pages_rejected():
    text = "** WARNING ** There are 7 bad requests from your IP address 91052 Erlangen"
    assert looks_like_error_page(text)
    assert not has_imprint_evidence(text)


def test_probe_needs_evidence(monkeypatch):
    _patch(monkeypatch, {"https://example.de/impressum": _page("Impressum | Datenschutz | Kontakt")})
    assert find_imprint("https://example.de/", "landing", []) is None


def test_probe_rejects_rate_limit_page(monkeypatch):
    text = "WARNING There are 7 bad requests from your IP address uris /impressum /imprint"
    _patch(monkeypatch, {"https://example.de/impressum": _page(text)})
    assert find_imprint("https://example.de/", "landing", []) is None


def test_imprint_keyword_page_needs_evidence_but_impressum_does_not(monkeypatch):
    pages = {
        "https://example.de/imprint": _page("Imprint methods for custom promotional products"),
        "https://example.de/impressum": _page("Impressum Max"),
    }
    _patch(monkeypatch, pages)
    assert find_imprint("https://example.de/", "landing", [("https://example.de/imprint", "imprint")]) is None
    result = find_imprint("https://example.de/", "landing", [("https://example.de/impressum", "impressum")])
    assert result["url"] == "https://example.de/impressum"


def test_fallback_extraction_needs_evidence(monkeypatch):
    html = "<html><body><nav>Home Impressum Datenschutz</nav></body></html>"
    _patch(monkeypatch, {"https://example.de/impressum": html})
    assert find_imprint("https://example.de/", "landing", [("https://example.de/impressum", "impressum")]) is None
    html = "<html><body><nav>Impressum Angaben gemäß § 5 TMG Muster GmbH</nav></body></html>"
    _patch(monkeypatch, {"https://example.de/impressum": html})
    result = find_imprint("https://example.de/", "landing", [("https://example.de/impressum", "impressum")])
    assert result["fallback_extraction"] is True


def test_privacy_url_for_weak_keyword_is_skipped(monkeypatch):
    calls = _patch(monkeypatch, {})
    find_imprint(
        "https://example.de/",
        "landing",
        [("https://host.com/legal/privacy-policy/", "rechtliches")],
    )
    assert calls[0] == "https://example.de/impressum"  # went straight to probes
