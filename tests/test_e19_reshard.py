import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "E19"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import merge_report  # noqa: E402
import reshard  # noqa: E402
from test_e19_recovery import row, write_tsv  # noqa: E402


def lines(p):
    return [l for l in Path(p).read_text().split("\n") if l]


def test_shard_of_is_stable_and_in_range():
    assert reshard.shard_of("example.de", 4) == reshard.shard_of("example.de", 4)
    assert all(0 <= reshard.shard_of(f"h{i}.de", 4) < 4 for i in range(50))
    # fixed values: sha1 is the same in every process and on every machine
    assert [reshard.shard_of(f"h{i}.de", 4) for i in range(6)] == [2, 2, 2, 2, 1, 2]


def test_reshard_end_to_end(tmp_path):
    hosts = [f"h{i}.de" for i in range(40)]
    (tmp_path / "in.txt").write_text("\n".join(hosts + ["h1.de", ""]) + "\n")  # duplicate + blank
    st = tmp_path / "st"
    st.mkdir()
    write_tsv(
        st / "fetch_status_batch000000.tsv",
        [
            row("h0.de", "imprint_found"),
            row("h1.de", "host_not_found"),  # failed again: still final for ic fetch
            row("h2.de", "error"),  # final too
            row("h3.de", "deferred"),  # never written by ic fetch; defensive: not final
            row("other.de", "imprint_found"),  # not in input: ignored
        ],
        partial_line="h4.de\timprint_fo",
    )
    write_tsv(st / "fetch_status_batch000001.tsv", [row("h5.de", "filtered")])
    out = tmp_path / "out"
    reshard.main(["--input", str(tmp_path / "in.txt"), "--status-dir", str(st), "--out-dir", str(out)])
    parts = [lines(out / f"remaining_shard{i}.txt") for i in range(4)]
    allr = [h for p in parts for h in p]
    assert len(allr) == len(set(allr)) == 40 - 4  # h0, h1, h2, h5 done
    assert not {"h0.de", "h1.de", "h2.de", "h5.de"} & set(allr)
    assert {"h3.de", "h4.de"} <= set(allr)
    for i, p in enumerate(parts):
        assert all(reshard.shard_of(h, 4) == i for h in p)
        assert p == [h for h in hosts if h in set(p)]  # input order kept


def test_summary_line(tmp_path, capsys):
    (tmp_path / "in.txt").write_text("a.de\nb.de\nc.de\n")
    st = tmp_path / "st"
    st.mkdir()
    write_tsv(st / "fetch_status_batch000000.tsv", [row("a.de", "imprint_found")])
    reshard.main(
        ["--input", str(tmp_path / "in.txt"), "--status-dir", str(st), "--shards", "2", "--out-dir", str(tmp_path / "o")]
    )
    assert capsys.readouterr().out.startswith("total 3 done 1 remaining 2 shards 0:")
    n = sum(len(lines(tmp_path / "o" / f"remaining_shard{i}.txt")) for i in range(2))
    assert n == 2


def total_row(text):
    return [l for l in text.split("\n") if l.startswith("total")][0].split("\t")


def test_merge_report_several_recovery_dirs(tmp_path, capsys):
    e16 = tmp_path / "e16"
    e16.mkdir()
    write_tsv(
        e16 / "fetch_status_batch000000.tsv",
        [row("a.de", detail="https:http403;http:http403"), row("b.de", detail="https:timeout;http:timeout")],
    )
    d1, d2 = tmp_path / "r1", tmp_path / "r2"
    d1.mkdir()
    d2.mkdir()
    write_tsv(d1 / "fetch_status_batch000000.tsv", [row("a.de", "imprint_found")])
    write_tsv(d2 / "fetch_status_batch000000.tsv", [row("b.de", "host_not_found")])
    merge_report.main(["--e16-dir", str(e16), "--recovery-dir", str(d1), "--recovery-dir", str(d2)])
    t = total_row(capsys.readouterr().out)
    assert t[1:5] == ["2", "1", "0", "1"]  # hosts, imprint_found, imprint_not_found, still_failing
    merge_report.main(["--e16-dir", str(e16), "--recovery-dir", str(d1)])
    assert total_row(capsys.readouterr().out)[1] == "1"
