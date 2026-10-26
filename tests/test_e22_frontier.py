import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "E22"))

import frontier  # noqa: E402


def test_build_and_count(tmp_path):
    d = tmp_path / "vm"
    d.mkdir()
    (d / "discovered_external_hosts.txt").write_text(
        "Seed.de\nwww.a-new.de\na-new.de\nb.com\nb.com\nfacebook.com\nin-seed-www.de\n\n"
    )
    (d / "fetch_status_batch000000.tsv").write_text("host\tstatus\nx.de\tok\ny.de\tok\nz.de\tpart")
    seeds = {"seed.de", "www.in-seed-www.de"}
    final, st, _ = frontier.build(seeds, [d], n_checkpoints=2)
    assert final == {"a-new.de", "b.com"}  # www pair collapsed, platform and seeds dropped
    assert st["in_seed"] == 2 and st["www_collapsed"] == 1
    fetched, per_file = frontier.count_fetched([d])
    assert fetched == {"x.de", "y.de"} and per_file["fetch_status_batch000000.tsv"] == 2
    assert frontier.tld_group("a.de") == "de" and frontier.tld_group("a.io") == "other"
