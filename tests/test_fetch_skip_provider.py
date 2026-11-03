"""D29: --skip-provider-group sends no request to a provider group (no network)."""

import types

import ic.cli.fetch as fetch
from ic.utils.fetch_state import read_done_hosts
from ic.utils.politeness import ProviderLimiter

SKIPPED = "v4:23.227.38"
HTML = b"<html><body><p>Willkommen</p></body></html>"


def _resolver(host):
    if host.startswith("shop"):
        return SKIPPED
    return "v4:1.2.3"


def _setup(monkeypatch, tmp_path):
    urls = []

    def fake_get(url, *args, **kwargs):
        urls.append(url)
        if url.startswith("https://redirect.de"):
            return types.SimpleNamespace(
                status_code=301,
                content=b"",
                headers={"Location": "https://shop-target.de/"},
            )
        return types.SimpleNamespace(status_code=200, content=HTML, headers={})

    lim = ProviderLimiter(max_concurrent=2, min_delay=0.0, resolver=_resolver)
    monkeypatch.setattr(fetch, "requests_get_with_timeout", fake_get)
    monkeypatch.setattr(fetch, "LIMITER", lim)
    monkeypatch.setattr(fetch, "SKIP_GROUPS", frozenset({SKIPPED}))
    monkeypatch.setattr(fetch, "OUTPUT_DIR", str(tmp_path))
    return urls, lim


def _rows(tmp_path):
    lines = (tmp_path / "fetch_status_batch000000.tsv").read_text().splitlines()[1:]
    return {l.split("\t")[0]: l.split("\t") for l in lines}


def test_skipped_group_gets_status_row_and_no_request(tmp_path, monkeypatch):
    urls, lim = _setup(monkeypatch, tmp_path)
    hosts = ["shop1.de", "ok1.de", "shop2.de", "ok2.de"]
    counts = fetch.run_batch(0, hosts, 2, lim, progress_interval=60)
    assert counts["skipped_provider"] == 2
    assert not any("shop" in u for u in urls)
    assert any("ok1.de" in u for u in urls) and any("ok2.de" in u for u in urls)
    rows = _rows(tmp_path)
    for h in ("shop1.de", "shop2.de"):
        assert rows[h][1] == "skipped_provider"
        assert rows[h][2] == SKIPPED and rows[h][3] == SKIPPED
        assert rows[h][5] == "0"  # requests
    assert rows["ok1.de"][1] != "skipped_provider" and rows["ok1.de"][5] != "0"
    # Resume counts the skipped hosts as done
    assert read_done_hosts(str(tmp_path / "fetch_status_batch000000.tsv")) == set(hosts)
    n = len(urls)
    assert fetch.run_batch(0, hosts, 2, lim) == {}
    assert len(urls) == n


def test_redirect_into_skipped_group_sends_no_request(tmp_path, monkeypatch):
    urls, lim = _setup(monkeypatch, tmp_path)
    fetch._ctx.last_error = "none"
    assert fetch.try_fetch("https://redirect.de/") == (None, None)
    assert urls == ["https://redirect.de/"]  # the redirect target was not requested
    assert fetch._ctx.last_error == "skipped_provider"
