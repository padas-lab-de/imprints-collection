"""E53 step 15: r5 top-up draw, folds, records and the assignment extension (no network)."""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from ic.gold.assignment import CAPACITY, LABELLERS, extend_assignment, labeller_loads

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "E53"
sys.path.insert(0, str(SCRIPTS))
_spec = importlib.util.spec_from_file_location("e53_topup", SCRIPTS / "topup.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)


def test_added_frame_keys_and_exclusions():
    r5 = ["a.de", "www.B.de", "c.de", "new.de", "www.new.de", "excl.de", "x.de"]
    src = ["a.de", "b.de", "c.de", "gone.de"]
    F = T.added_frame(r5, src, {"excl.de"})
    assert F == [
        "new.de",
        "x.de",
    ]  # www./case folded, one host per key, excluded key left out


def test_topup_size_rounds_and_caps():
    assert T.topup_size(1869, 37311, 3901721) == 18
    assert T.topup_size(1000, 37311, 3901721) == 10
    assert T.topup_size(1869, 3, 10) == 3  # never more than N_A
    assert T.topup_size(1869, 0, 3901721) == 0


def test_draw_srs_deterministic_prefix():
    F = [f"h{i}.de" for i in range(500)]
    s1, s2 = T.draw_srs(F, 18, 20261114), T.draw_srs(list(reversed(F)), 18, 20261114)
    assert s1 == s2 and len(set(s1)) == 18  # order of the input does not matter
    assert T.draw_srs(F, 20, 20261114)[:18] == s1  # nested
    assert T.draw_srs(F, 18, 1) != s1


def test_dropped_items():
    gold = [{"host": "a.de"}, {"host": "www.b.de"}, {"host": "c.de"}]
    assert T.dropped_items(gold, {"a.de", "b.de"}) == [{"host": "c.de"}]


def test_topup_folds_balance():
    folds = T.topup_folds(
        [f"h{i}.de" for i in range(18)],
        Counter({0: 374, 1: 374, 2: 374, 3: 374, 4: 373}),
    )
    after = Counter({0: 374, 1: 374, 2: 374, 3: 374, 4: 373}) + Counter(folds.values())
    assert (
        max(after.values()) - min(after.values()) <= 1
        and sum(after.values()) == 1869 + 18
    )
    assert folds == T.topup_folds(
        [f"h{i}.de" for i in reversed(range(18))],
        Counter({0: 374, 1: 374, 2: 374, 3: 374, 4: 373}),
    )


def test_topup_records_fields_match_gold_sample():
    recs = T.topup_records(["b.de", "a.de"], 1000, {"a.de": 0, "b.de": 4})
    assert [r["host"] for r in recs] == ["a.de", "b.de"]
    keys = {
        "M_h",
        "classes",
        "core",
        "fold",
        "fold_group",
        "host",
        "m_h",
        "pi",
        "selected_for",
        "stratum",
        "weight",
    }
    assert set(recs[0]) == keys
    assert (
        recs[0]["pi"] == 2 / 1000
        and recs[0]["weight"] == 500
        and recs[0]["stratum"] == "topup"
    )
    assert recs[1]["fold"] == 4 and not recs[1]["core"]


def _rows(loads):
    rows, item = [], 0
    for lab, n in loads.items():
        for k in range(n):
            rows.append(
                {
                    "item": item,
                    "host": f"o{item}.de",
                    "labeller": lab,
                    "role": "primary",
                    "order": k + 1,
                }
            )
            item += 1
    return rows


def test_extend_assignment_keeps_2_1_1_and_appends():
    rows = _rows({"L1": 1172, "L2": 586, "L3": 586})
    new_items = [{"item": 5000 + i, "host": f"n{i}.de"} for i in range(18)]
    new = extend_assignment(rows, new_items, 7)
    assert len(new) == 18 and {r["role"] for r in new} == {"primary"}
    assert sorted(r["item"] for r in new) == list(range(5000, 5018))
    load = labeller_loads(rows + new)
    assert load == {
        "L1": 1180,
        "L2": 591,
        "L3": 591,
    }  # 2,362 rows; 2:1:1 would be 1,181 / 590.5 / 590.5
    for lab in LABELLERS:  # orders continue after the last existing row, no gaps
        o = sorted(r["order"] for r in new if r["labeller"] == lab)
        start = max(r["order"] for r in rows if r["labeller"] == lab)
        assert o == list(range(start + 1, start + 1 + len(o)))
    assert new == extend_assignment(rows, list(reversed(new_items)), 7)  # deterministic


def test_extend_assignment_skips_dropped_and_rejects_clashes():
    rows = _rows({"L1": 10, "L2": 5, "L3": 5})
    drop = [r["host"] for r in rows if r["labeller"] == "L2"][:3]  # L2 loses 3 items
    new = extend_assignment(
        rows,
        [{"item": 100 + i, "host": f"n{i}.de"} for i in range(3)],
        1,
        skip_hosts=drop,
    )
    assert Counter(r["labeller"] for r in new) == {"L2": 3}
    assert labeller_loads(rows, drop)["L2"] == 2 and CAPACITY["L1"] == 2
    with pytest.raises(ValueError):
        extend_assignment(rows, [{"item": 0, "host": "z.de"}], 1)
    with pytest.raises(ValueError):
        extend_assignment(rows, [{"item": 999, "host": rows[0]["host"]}], 1)
    with pytest.raises(ValueError):
        extend_assignment(
            rows, [{"item": 999, "host": "y.de"}, {"item": 999, "host": "z.de"}], 1
        )


def test_cmd_assign_writes_new_file_and_keeps_old(tmp_path):
    gold = tmp_path / "gold"
    gold.mkdir()
    rows = _rows({"L1": 4, "L2": 2, "L3": 2})
    (gold / "assignment.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    old = (gold / "assignment.jsonl").read_text()
    sample = tmp_path / "topup.jsonl"
    sample.write_text("".join(json.dumps({"host": h}) + "\n" for h in ("p.de", "q.de")))
    dropped = tmp_path / "dropped.jsonl"
    dropped.write_text("")
    a = type(
        "A",
        (),
        {
            "gold": str(gold),
            "sample": str(sample),
            "dropped": str(dropped),
            "seed": 3,
            "summary": None,
        },
    )
    T.cmd_assign(a)
    assert (gold / "assignment_pre_topup.jsonl").read_text() == old
    new = [json.loads(l) for l in (gold / "assignment.jsonl").read_text().splitlines()]
    assert len(new) == 10 and {r["item"] for r in new} >= {8, 9}
    assert [r for r in new if r["item"] < 8] == sorted(
        rows, key=lambda r: (r["labeller"], r["order"])
    )
    with pytest.raises(SystemExit):
        T.cmd_assign(a)  # runs once only
