import gzip
import importlib.util
import json
from pathlib import Path

_root = Path(__file__).resolve().parents[1] / "scripts/E31"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _root / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


rc = _load("release_count")
ex = _load("extract")


def test_redirect_to_known_host_gives_target():
    crawled = {"new.de", "old.de"}
    assert rc.canonical("old.de", "new.de", crawled) == "new.de"
    assert rc.canonical("old.de", "www.new.de", crawled) == "new.de"  # www-collapsed match


def test_redirect_to_unknown_host_gives_own_non_www():
    assert rc.canonical("www.old.de", "elsewhere.com", {"old.de"}) == "old.de"
    assert rc.canonical("old.de", "", {"old.de"}) == "old.de"


def test_www_twins_collapse():
    crawled = {"x.de"}
    assert rc.canonical("www.x.de", "", crawled) == rc.canonical("x.de", "", crawled) == "x.de"


def _status(d, name, rows):
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text("".join(f"{h}\t{s}\t\t\t1\t1\t0\t0.0\t0\n" for h, s in rows))


def _manifest(tmp_path, entries):
    lines = ["source\tvm\tdir\tfile\trows\tsha256\tstats"]
    for src, fn, rows in entries:
        (tmp_path / fn).write_text("".join(f"{h}\t{s}\t{t}\n" for h, s, t in rows))
        lines.append(f"{src}\tv\td\t{fn}\t0\t0\t")
    (tmp_path / "manifest.tsv").write_text("\n".join(lines) + "\n")
    return rc.load_manifest(tmp_path)


def test_last_row_wins_and_counts(tmp_path):
    m = _manifest(
        tmp_path,
        [
            (
                "A",
                "a.tsv",
                [
                    ("x.de", "imprint_found", ""),
                    ("www.x.de", "imprint_found", ""),
                    ("gone.de", "imprint_found", ""),
                    ("gone.de", "host_not_found", ""),  # last row: not found
                    ("a.de", "imprint_found", "b.de"),  # redirects to crawled b.de
                    ("b.de", "host_not_found", ""),
                    ("c.de", "imprint_found", "unknown.com"),  # unknown target -> own form
                ],
            ),
            (
                "B",
                "b.tsv",
                [("b.de", "imprint_found", ""), ("x.de", "imprint_found", ""), ("n.de", "imprint_found", "")],
            ),
        ],
    )
    table, st, sites, cases = rc.compute(list(m.items()))
    a, b, total = table
    assert a["imprint_found"] == 4  # x.de, www.x.de, a.de, c.de
    assert a["new_exact"] == 4 and a["new_www"] == 3 and a["new_d34"] == 3  # x.de, b.de (via a.de), c.de
    assert b["new_exact"] == 2 and b["new_www"] == 2  # b.de, n.de
    assert b["new_d34"] == 1  # b.de already a canonical site of A; n.de new
    assert total["cum_exact"] == 6 and total["cum_www"] == 5 and total["cum_d34"] == 4
    assert sites == {"x.de", "b.de", "c.de", "n.de"}
    assert st["changed_by_d34"] == 1 and st["target_site_known"] == 1 and st["target_site_unknown"] == 1


def test_variant_folds_only_into_found_target(tmp_path):
    m = _manifest(
        tmp_path,
        [
            (
                "A",
                "a.tsv",
                [
                    ("a.de", "imprint_found", "b.de"),  # b.de is crawled but not found
                    ("b.de", "host_not_found", ""),
                    ("c.de", "imprint_found", "d.de"),  # d.de is found
                    ("d.de", "imprint_found", ""),
                ],
            )
        ],
    )
    table, st, sites, cases = rc.compute(list(m.items()))
    assert sites == {"b.de", "d.de"}  # D34: a.de -> b.de, c.de -> d.de
    assert rc.compute.d34f_sites == {"a.de", "d.de"}  # variant: a.de stays, c.de -> d.de
    assert table[-1]["cum_d34"] == 2 and table[-1]["cum_d34f"] == 2


def test_extract_reads_status_and_redirect(tmp_path):
    d = tmp_path / "src"
    _status(
        d,
        "fetch_status_batch000000.tsv",
        [("Old.de", "imprint_found"), ("nf.de", "host_not_found"), ("w.de", "imprint_found")],
    )
    (d / "fetch_status_batch000000.tsv").open("a").write("half\twritten\n")  # skipped
    with gzip.open(d / "imprints_batch000000.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write(json.dumps({"host": "old.de", "main": {"url": "https://WWW.New.de:443/start"}}) + "\n")
    import contextlib
    import io

    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        ex.main(str(d))
    rows = [l.split("\t") for l in buf.getvalue().splitlines()]
    assert rows == [
        ["old.de", "imprint_found", "www.new.de"],
        ["nf.de", "host_not_found", ""],
        ["w.de", "imprint_found", ""],
    ]
    assert "no_record=1" in err.getvalue() and "rows=3" in err.getvalue()
