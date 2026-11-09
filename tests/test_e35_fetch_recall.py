"""E35: fetch recall patch from E32 (probe paths, probe after failed links, Kontakt rule, query-only links)."""

import json
import threading
import types

from resiliparse.parse.html import HTMLTree

import ic.cli.fetch as fetch
from ic.cli.fetch import discover_links, find_imprint, kontakt_as_imprint

ADDRESS = "Impressum Max Mustermann Hauptstr. 1 12345 Musterstadt"


def _page(text):
    return f"<html><body><p>{text}</p></body></html>"


def _fake_fetch(monkeypatch, pages):
    """Replace try_fetch; returns the list of requested URLs."""
    calls = []

    def fake(url, num_redirects=10, retry=False):
        calls.append(url)
        html = pages.get(url)
        return (url, html) if html else (None, None)

    monkeypatch.setattr(fetch, "try_fetch", fake)
    return calls


def _kontakt(text, url="https://example.de/kontakt"):
    return fetch.parse_html(_page(text))[1] | {"url": url}


# --- probe paths ---


def test_probe_paths_contain_php_and_htm():
    assert "/impressum.php" in fetch.IMPRINT_PROBE_PATHS
    assert "/impressum.htm" in fetch.IMPRINT_PROBE_PATHS


def test_probe_finds_impressum_php(monkeypatch):
    _fake_fetch(monkeypatch, {"https://example.de/impressum.php": _page(ADDRESS)})
    result = find_imprint("https://example.de/", "landing", [])
    assert result["found_by"] == "probe" and result["found_keyword"] == "/impressum.php"


def test_probe_finds_impressum_htm(monkeypatch):
    _fake_fetch(monkeypatch, {"https://example.de/impressum.htm": _page(ADDRESS)})
    result = find_imprint("https://example.de/", "landing", [])
    assert result["found_by"] == "probe" and result["found_keyword"] == "/impressum.htm"


def test_probe_redirecting_to_landing_page_is_rejected(monkeypatch):
    """A SPA answers every path with the landing page (text differs by a live ticker)."""
    page = _page("Impressum Bitcoin 69.470 Euro Hauptstr. 1 12345 Musterstadt")
    monkeypatch.setattr(
        fetch,
        "try_fetch",
        lambda url, num_redirects=10, retry=False: ("https://example.de/", page),
    )
    assert find_imprint("https://example.de/", "Bitcoin 69.471 Euro", []) is None


def test_probe_redirect_to_privacy_page_is_rejected(monkeypatch):
    page = _page("Datenschutz Impressum Max Mustermann Hauptstr. 1 12345 Musterstadt")
    monkeypatch.setattr(
        fetch,
        "try_fetch",
        lambda url, num_redirects=10, retry=False: (
            "https://example.de/datenschutz",
            page,
        ),
    )
    assert find_imprint("https://example.de/", "landing", []) is None


# --- probe after failed candidates ---


def test_probe_runs_after_failed_candidate(monkeypatch):
    calls = _fake_fetch(
        monkeypatch, {"https://example.de/impressum.htm": _page(ADDRESS)}
    )
    cand = [("https://example.de/rechtliches-x", "impressum")]
    result = find_imprint("https://example.de/", "landing", cand)
    assert result["found_by"] == "probe" and result["found_keyword"] == "/impressum.htm"
    assert calls[0] == "https://example.de/rechtliches-x"


def test_failed_candidate_is_not_probed_again(monkeypatch):
    calls = _fake_fetch(monkeypatch, {})
    cand = [("https://example.de/impressum", "impressum")]
    assert find_imprint("https://example.de/", "landing", cand) is None
    assert calls == [
        "https://example.de/impressum",
        "https://example.de/impressum.html",
        "https://example.de/imprint",
        "https://example.de/impressum.php",
        "https://example.de/impressum.htm",
    ]


def test_no_probe_when_candidate_is_imprint(monkeypatch):
    calls = _fake_fetch(monkeypatch, {"https://example.de/legal": _page(ADDRESS)})
    cand = [("https://example.de/legal", "impressum")]
    result = find_imprint("https://example.de/", "landing", cand)
    assert result["found_by"] == "link"
    assert calls == ["https://example.de/legal"]


# --- Kontakt rule ---


def test_kontakt_with_imprint_word_and_evidence_is_accepted():
    rec = kontakt_as_imprint(
        _kontakt("Kontakt / " + ADDRESS), "landing", "https://example.de/"
    )
    assert rec["found_by"] == "kontakt" and rec["url"] == "https://example.de/kontakt"


def test_kontakt_without_evidence_is_rejected():
    k = _kontakt("Kontakt Impressum Telefon 031 781")
    assert kontakt_as_imprint(k, "landing") is None


def test_kontakt_with_address_but_no_imprint_word_is_rejected():
    k = _kontakt("Kontakt Biohof Dorfstrasse 7 3629 Oppligen Telefon 031 781 09 09")
    assert kontakt_as_imprint(k, "landing") is None


def test_kontakt_equal_to_landing_text_is_rejected():
    k = _kontakt(ADDRESS)
    assert kontakt_as_imprint(k, k["main_content"]) is None


def test_kontakt_redirected_to_landing_url_is_rejected():
    k = _kontakt("Kontakt / " + ADDRESS, url="https://example.de/")
    assert kontakt_as_imprint(k, "landing", "https://example.de/") is None


def test_kontakt_privacy_url_is_rejected():
    k = _kontakt("Kontakt / " + ADDRESS, url="https://example.de/datenschutz")
    assert kontakt_as_imprint(k, "landing", "https://example.de/") is None


# --- query-only links ---


def test_pathless_query_link_is_a_candidate():
    tree = HTMLTree.parse(
        '<body><a href="https://example.de?page=impressum">Impressum</a></body>'
    )
    links, _ = discover_links(tree.body, "https://example.de/", "example.de")
    assert [u for u, _ in links["impressum"]] == ["https://example.de?page=impressum"]


def test_pathless_link_without_query_is_still_skipped():
    tree = HTMLTree.parse('<body><a href="https://example.de">Impressum</a></body>')
    links, _ = discover_links(tree.body, "https://example.de/", "example.de")
    assert links.get("impressum", []) == []


# --- process_host level ---


def _run_host(monkeypatch, tmp_path, pages):
    """Run process_host for example.de on fake HTTP pages; returns (status, requested URLs, record)."""
    urls = []

    def fake_get(url, *args, **kwargs):
        urls.append(url)
        body = pages.get(url)
        if body is None:
            return types.SimpleNamespace(status_code=404, content=b"", headers={})
        return types.SimpleNamespace(status_code=200, content=body.encode(), headers={})

    monkeypatch.setattr(fetch, "requests_get_with_timeout", fake_get)
    monkeypatch.setattr(fetch, "LIMITER", None)
    monkeypatch.setattr(fetch, "SKIP_GROUPS", frozenset())
    monkeypatch.setattr(fetch, "OUTPUT_DIR", str(tmp_path))
    out = tmp_path / "out.jsonl"
    pbar = types.SimpleNamespace(update=lambda n=1: None)
    with open(out, "w", encoding="utf-8") as f:
        status = fetch.process_host(
            "example.de", f, threading.Lock(), pbar, {"example.de": {}}
        )
    lines = out.read_text(encoding="utf-8").splitlines()
    return status, urls, (json.loads(lines[0]) if lines else None)


def test_no_extra_request_when_landing_links_imprint(monkeypatch, tmp_path):
    pages = {
        "https://example.de": '<html><body><p>Willkommen</p><a href="/impressum">Impressum</a></body></html>',
        "https://example.de/impressum": _page(ADDRESS),
    }
    status, urls, rec = _run_host(monkeypatch, tmp_path, pages)
    assert status == fetch.CrawlStatus.IMPRINT_FOUND
    assert rec["impressum"]["found_by"] == "link"
    assert len(urls) == 2  # landing + imprint, no probe


def test_kontakt_page_becomes_imprint_and_is_not_refetched(monkeypatch, tmp_path):
    pages = {
        "https://example.de": '<html><body><p>Willkommen</p><a href="/kontakt">Kontakt</a></body></html>',
        "https://example.de/kontakt": _page("Kontakt / " + ADDRESS),
    }
    status, urls, rec = _run_host(monkeypatch, tmp_path, pages)
    assert status == fetch.CrawlStatus.IMPRINT_FOUND
    assert rec["impressum"]["found_by"] == "kontakt"
    assert urls.count("https://example.de/kontakt") == 1
