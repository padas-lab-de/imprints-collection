"""Unit tests for imprint link discovery and imprint selection in ic.cli.fetch (no network)."""

from resiliparse.parse.html import HTMLTree

import ic.cli.fetch as fetch
from ic.cli.fetch import discover_links, find_imprint, get_base_href


def links(html, base_url="https://example.de/", host="example.de", use_base=False):
    tree = HTMLTree.parse(html)
    base_href = get_base_href(tree) if use_base else None
    return discover_links(tree.body, base_url, host, base_href=base_href)


def imprint_urls(html, **kw):
    keyword_links, _ = links(html, **kw)
    return [u for u, _ in keyword_links.get("impressum", [])]


def test_plain_impressum_link():
    html = '<body><a href="/impressum">Impressum</a></body>'
    assert imprint_urls(html) == ["https://example.de/impressum"]


def test_query_string_link():
    html = '<body><a href="/index.php?site=imprint">Kontakt</a></body>'
    assert imprint_urls(html) == ["https://example.de/index.php?site=imprint"]


def test_shared_path_keeps_all_links():
    html = (
        '<body><a href="/?id=1">Start</a><a href="/?id=183">Impressum</a>'
        '<a href="/?id=2">Galerie</a></body>'
    )
    assert imprint_urls(html) == ["https://example.de/?id=183"]


def test_shared_path_later_link_does_not_overwrite_anchor():
    html = (
        '<body><a href="/index.php?page_id=21">Impressum</a>'
        '<a href="/index.php?page_id=22">Home</a></body>'
    )
    assert imprint_urls(html) == ["https://example.de/index.php?page_id=21"]


def test_other_labels():
    for label in [
        "Imprint",
        "Legal Notice",
        "Rechtliche Hinweise",
        "Rechtliches",
        "Anbieterkennzeichnung",
    ]:
        html = f'<body><a href="/x/page">{label}</a></body>'
        assert imprint_urls(html) == ["https://example.de/x/page"], label


def test_impressum_has_priority_over_other_labels():
    html = (
        '<body><a href="/a">Imprint</a><a href="/bbbbbb">Impressum</a></body>'
    )
    assert imprint_urls(html) == [
        "https://example.de/bbbbbb",
        "https://example.de/a",
    ]


def test_own_host_before_external_then_shortest():
    html = (
        '<body><a href="https://other.com/impressum">Impressum</a>'
        '<a href="/long/path/impressum">Impressum</a>'
        '<a href="/impressum">Impressum</a></body>'
    )
    assert imprint_urls(html) == [
        "https://example.de/impressum",
        "https://example.de/long/path/impressum",
        "https://other.com/impressum",
    ]


def test_base_href():
    html = (
        '<html><head><base href="https://example.de/"></head>'
        '<body><a href="de/impressum.html">Impressum</a></body></html>'
    )
    assert imprint_urls(html, base_url="https://example.de/de/start/", use_base=True) == [
        "https://example.de/de/impressum.html"
    ]
    # without base href the link resolves relative to the page
    assert imprint_urls(html, base_url="https://example.de/de/start/") == [
        "https://example.de/de/start/de/impressum.html"
    ]


def test_img_alt_title_aria_label():
    for anchor in [
        '<a href="/p1"><img src="x.png" alt="Impressum"></a>',
        '<a href="/p1" title="Impressum">i</a>',
        '<a href="/p1" aria-label="Impressum"><svg></svg></a>',
    ]:
        assert imprint_urls(f"<body>{anchor}</body>") == ["https://example.de/p1"], anchor


def test_no_match():
    html = '<body><a href="/about">Ueber</a><a href="/team">Team</a></body>'
    assert imprint_urls(html) == []


def test_other_keywords_and_external_hosts():
    html = (
        '<body><a href="/kontakt">Kontakt</a><a href="https://other.com/">x</a>'
        "</body>"
    )
    keyword_links, external = links(html)
    assert keyword_links["kontakt"] == [("https://example.de/kontakt", "kontakt")]
    assert external == {"other.com"}


def test_matched_keyword_is_reported():
    html = '<body><a href="/legal">Legal Notice</a></body>'
    keyword_links, _ = links(html)
    assert keyword_links["impressum"] == [("https://example.de/legal", "legal notice")]


def _page(text):
    return f"<html><body><main><p>{text}</p></main></body></html>"


def test_find_imprint_tries_next_candidate(monkeypatch):
    pages = {"https://example.de/a": None, "https://example.de/b": _page("Impressum Anbieter " * 5)}
    monkeypatch.setattr(
        fetch, "try_fetch", lambda url, num_redirects=10, retry=False: (url, pages.get(url))
    )
    result = find_imprint(
        "https://example.de/",
        "landing",
        [("https://example.de/a", "impressum"), ("https://example.de/b", "imprint")],
    )
    assert result["url"] == "https://example.de/b"
    assert result["found_by"] == "link"
    assert result["found_keyword"] == "imprint"
    assert result["candidate_rank"] == 1


def test_find_imprint_probe_accepts_imprint_text(monkeypatch):
    pages = {"https://example.de/impressum": _page("Angaben gemäß § 5 TMG: Max Mustermann")}
    monkeypatch.setattr(
        fetch, "try_fetch", lambda url, num_redirects=10, retry=False: (url, pages.get(url))
    )
    result = find_imprint("https://example.de/", "landing text", [])
    assert result["found_by"] == "probe"
    assert result["found_keyword"] == "/impressum"


def test_find_imprint_probe_rejects_landing_copy_and_unrelated_text(monkeypatch):
    landing = _page("Willkommen Impressum")
    pages = {
        "https://example.de/impressum": landing,  # same text as landing page
        "https://example.de/impressum.html": _page("Seite nicht gefunden"),
    }
    monkeypatch.setattr(
        fetch, "try_fetch", lambda url, num_redirects=10, retry=False: (url, pages.get(url))
    )
    landing_text = fetch.parse_html(landing)[1]["main_content"]
    assert find_imprint("https://example.de/", landing_text, []) is None


def test_find_imprint_no_probe_when_candidates_exist(monkeypatch):
    calls = []

    def fake(url, num_redirects=10, retry=False):
        calls.append(url)
        return None, None

    monkeypatch.setattr(fetch, "try_fetch", fake)
    assert find_imprint("https://example.de/", "x", [("https://example.de/i", "impressum")]) is None
    assert calls == ["https://example.de/i"]


def test_fetch_imprint_page_falls_back_to_full_text(monkeypatch):
    html = "<html><body><nav>Impressum Muster GmbH Musterstr. 1</nav></body></html>"
    monkeypatch.setattr(
        fetch, "try_fetch", lambda url, num_redirects=10, retry=False: (url, html)
    )
    # Only meaningful if main-content extraction is really empty for this page
    main = fetch.parse_html(html)[1]
    url, result, fallback = fetch.fetch_imprint_page("https://example.de/i")
    assert result is not None and result["content_length"] > 0
    assert fallback == (main["content_length"] == 0)
