"""D39 B: the crawler identifies itself with a contact URL (no network)."""

import ic.cli.fetch as fetch


def test_user_agent_identifies_crawler():
    ua = fetch.HEADERS["User-Agent"]
    assert "ImprintsCollectionBot" in ua
    assert "https://www.fim.uni-passau.de/data-science" in ua
