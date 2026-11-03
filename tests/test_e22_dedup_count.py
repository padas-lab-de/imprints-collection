import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "scripts/E22/dedup_count.py"
_spec = importlib.util.spec_from_file_location("dedup_count", _p)
dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dc)

HEADER = "host\tstatus\tdetail\tprovider\tattempts\trequests\tthrottled\tseconds\tend_time\n"


def write(d, name, rows):
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(HEADER + "".join(f"{h}\t{s}\t\t\t1\t1\t0\t0.0\t0\n" for h, s in rows))


def test_last_row_wins_and_new_counts(tmp_path):
    write(tmp_path / "a", "fetch_status_batch000000.tsv",
          [("x.de", "imprint_found"), ("www.y.de", "imprint_found"), ("z.de", "imprint_found"), ("z.de", "host_not_found")])
    (tmp_path / "a" / "fetch_status_batch000001.tsv").write_text(HEADER + "bad\tline\n")  # skipped
    write(tmp_path / "b", "fetch_status_batch000000.tsv",
          [("x.de", "imprint_found"), ("y.de", "imprint_found"), ("w.de", "imprint_found"), ("v.de", "imprint_not_found")])
    srcs = [(n, *dc.read_source([str(tmp_path / n)])) for n in "ab"]
    srcs = [(n, r, f, k) for n, r, f, k in srcs]
    rows = dc.combine(srcs)
    a, b, tot = rows
    assert (a["hosts"], a["imprint_found"], a["new"]) == (3, 2, 2)  # z.de last row failed
    assert (b["imprint_found"], b["new"]) == (3, 2)  # y.de and w.de new exactly
    assert b["new_www"] == 1  # y.de equals www.y.de after collapse, only w.de is new
    assert (tot["new"], tot["new_www"]) == (4, 3)
