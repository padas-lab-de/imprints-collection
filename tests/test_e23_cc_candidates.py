import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("duckdb")

spec = importlib.util.spec_from_file_location(
    "cc_candidates", Path(__file__).resolve().parent.parent / "scripts/E23/cc_candidates.py"
)
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)


def test_collapse():
    assert cc.collapse("WWW.Example.de ") == "example.de"
    assert cc.collapse("wwwx.de") == "wwwx.de"


def test_not_known_with_www_variants():
    known = {cc.collapse(h) for h in ["www.a.de", "b.de"]}
    keys = {cc.collapse(h) for h in ["a.de", "www.b.de", "c.de"]}
    assert cc.not_known(keys, known) == {"c.de"}


def test_pick_form_and_rule():
    assert cc.pick_form({"www.a.de": 3, "a.de": 5}) == "a.de"
    assert cc.pick_form({"www.a.de": 5, "a.de": 5}) == "a.de"
    assert cc.german_rule(0, 2) is False and cc.german_rule(0, 2, loose=True) is True
    assert cc.tld_of("x.co.uk") == "uk"
