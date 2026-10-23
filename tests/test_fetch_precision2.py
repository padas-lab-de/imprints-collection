"""More E9 precision rules: privacy URLs, long anchor labels, template placeholders."""

from resiliparse.parse.html import HTMLTree

import ic.cli.fetch as fetch
from ic.cli.fetch import discover_links, find_imprint, is_privacy_url
from ic.utils.imprint_utils import has_imprint_evidence


def test_is_privacy_url():
    assert is_privacy_url("https://h.com/de/rechtliches/datenschutz")
    assert is_privacy_url("https://h.com/legal/privacy-policy/")
    assert not is_privacy_url("https://h.com/impressum-datenschutz")
    assert not is_privacy_url("https://h.com/legal-notice-privacy")
    assert not is_privacy_url("https://h.com/impressum")


def test_privacy_final_url_after_redirect_is_rejected(monkeypatch):
    html = "<html><body><main><p>Datenschutz Angaben gemäß § 5 TMG Muster GmbH</p></main></body></html>"
    monkeypatch.setattr(
        fetch,
        "try_fetch",
        lambda url, num_redirects=10, retry=False: ("https://h.com/legal/privacy-policy/", html),
    )
    assert find_imprint("https://example.de/", "x", [("https://h.com/rechtliches", "rechtliches")]) is None


def test_long_anchor_label_does_not_match_english_term():
    html = '<body><a href="/p/pencil.html">Full Color Imprint Pencil with Eraser</a></body>'
    tree = HTMLTree.parse(html)
    assert discover_links(tree.body, "https://example.de/", "example.de")[0] == {}
    html = '<body><a href="/p/x.html">Imprint</a></body>'
    tree = HTMLTree.parse(html)
    assert discover_links(tree.body, "https://example.de/", "example.de")[0]["impressum"]


def test_template_placeholder_is_not_evidence():
    assert not has_imprint_evidence(
        "Impressum Name des Unternehmens Bitte geben Sie Ihren Firmennamen ein 91052 Erlangen"
    )
