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


def test_write_list_and_priority_split(tmp_path):
    pri, rest = frontier.split_priority({"a.de", "b.com", "c.info", "d.ch"}, {"de", "ch", "info"})
    assert pri == {"a.de", "c.info", "d.ch"} and rest == {"b.com"}
    digest = frontier.write_list(tmp_path / "x.txt", {"b.de", "a.de"})
    assert (tmp_path / "x.txt").read_text() == "a.de\nb.de\n"
    assert (tmp_path / "x.txt.sha256").read_text() == f"{digest}  x.txt\n"


def test_main_known_and_split(tmp_path, monkeypatch):
    d = tmp_path / "vm"
    d.mkdir()
    (d / "discovered_external_hosts.txt").write_text("seed.de\nold.com\nnew.de\nnew.com\nwww.old.com\n")
    (d / "fetch_status_batch000000.tsv").write_text("host\tstatus\nx.de\tok\n")
    (tmp_path / "seeds.txt").write_text("seed.de\n")
    (tmp_path / "a.txt").write_text("old.com\n")
    out = tmp_path / "out"
    argv = ["frontier.py", "--seeds", str(tmp_path / "seeds.txt"), "--input-dir", str(d),
            "--out-dir", str(out), "--known", str(tmp_path / "a.txt"), "--name", "r2"]
    monkeypatch.setattr(sys, "argv", argv)
    frontier.main()
    assert (out / "r2.txt").read_text() == "new.com\nnew.de\n"
    assert (out / "r2_priority.txt").read_text() == "new.de\n"
    assert (out / "r2_rest.txt").read_text() == "new.com\n"
    assert (out / "r2_rest.txt.sha256").exists()
