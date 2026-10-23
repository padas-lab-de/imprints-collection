"""Unit tests for imprint candidate selection edge cases in ic.cli.fetch (no network)."""

from resiliparse.parse.html import HTMLTree

import ic.cli.fetch as fetch
from ic.cli.fetch import discover_links, find_imprint


def _page(text):
    return f"<html><body><main><p>{text}</p></main></body></html>"


def _links(html):
    tree = HTMLTree.parse(html)
    return discover_links(tree.body, "https://example.de/", "example.de")[0]


def _patch_fetch(monkeypatch, pages):
    calls = []

    def fake(url, num_redirects=10, retry=False):
        calls.append(url)
        return url, pages.get(url)

    monkeypatch.setattr(fetch, "try_fetch", fake)
    return calls


def test_fragment_is_dropped_from_candidates():
    html = (
        '<body><a href="/impressum/#datenschutz">Impressum</a>'
        '<a href="/impressum/">Impressum</a></body>'
    )
    urls = [u for u, _ in _links(html)["impressum"]]
    assert urls == ["https://example.de/impressum/"]


def test_landing_page_fragment_link_is_not_an_imprint(monkeypatch):
    calls = _patch_fetch(monkeypatch, {})
    # "#impressum" resolves to the landing page itself: skipped, probes run instead
    keyword_links = _links('<body><a href="#impressum">Impressum</a></body>')
    result = find_imprint("https://example.de/", "landing", keyword_links["impressum"])
    assert result is None
    assert calls[0] == "https://example.de/impressum"


def test_candidate_with_landing_text_is_skipped(monkeypatch):
    landing = _page("Willkommen Startseite")
    landing_text = fetch.parse_html(landing)[1]["main_content"]
    _patch_fetch(
        monkeypatch,
        {
            "https://example.de/a": landing,
            "https://example.de/b": _page("Impressum Anbieter " * 5),
        },
    )
    result = find_imprint(
        "https://example.de/",
        landing_text,
        [("https://example.de/a", "impressum"), ("https://example.de/b", "imprint")],
    )
    assert result["url"] == "https://example.de/b"


def test_try_fetch_rejects_binary(monkeypatch):
    class Resp:
        status_code = 200
        content = bytes(range(256)) * 4
        headers = {}

    monkeypatch.setattr(fetch, "requests_get_with_timeout", lambda *a, **k: Resp())
    assert fetch.try_fetch("https://example.de/x.pdf") == (None, None)
