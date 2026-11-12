"""E53 frame helpers: host normalisation, exclusion, prefix property of the seeded permutation."""

import importlib.util
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("e53_common", ROOT / "scripts" / "E53" / "common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)


def test_norm_host_variants():
    for h in ["Example.DE", "www.example.de", "WWW.example.de.", "https://www.example.de/impressum",
              "http://user@www.example.de:8080/x?y", "example.de/", " example.de \n"]:
        assert C.norm_host(h) == "example.de", h
    assert C.norm_host("") == ""
    assert C.norm_host("shop.example.de") == "shop.example.de"
    assert C.norm_host("wwwexample.de") == "wwwexample.de"
    assert C.norm_host("www2.example.de") == "www2.example.de"


def test_exclude_both_www_variants():
    frame = ["a.de", "www.b.de", "c.de", "www.d.de", "e.de"]
    ex = C.keys(["www.a.de", "b.de", "https://d.de/impressum", ""])
    assert ex == {"a.de", "b.de", "d.de"}
    assert C.exclude(frame, ex) == ["c.de", "e.de"]


def test_rank_key_independent_of_www_and_seeded():
    assert C.rank_key("www.x.de", 1) == C.rank_key("x.de", 1)
    assert C.rank_key("x.de", 1) != C.rank_key("x.de", 2)


def _frame(n=2000):
    rng = random.Random(0)
    return [f"site{rng.randrange(10**9)}-{i}.de" for i in range(n)]


def test_permutation_is_permutation_and_order_free():
    f = _frame()
    p = C.permute(f, 7)
    assert sorted(p) == sorted(f)
    g = list(f)
    random.Random(3).shuffle(g)
    assert C.permute(g, 7) == p  # input order does not matter


def test_prefix_extends():
    p = C.permute(_frame(), 7)
    s1, s2 = p[:300], p[:800]
    assert s2[:300] == s1  # a larger S1 extends the smaller one


def test_removal_does_not_reorder_others():
    f = _frame()
    p = C.permute(f, 7)
    drop = set(random.Random(5).sample(f, 400))
    q = C.permute([h for h in f if h not in drop], 7)
    assert q == [h for h in p if h not in drop]


def test_prefix_inclusion_is_uniform():
    """Every site has the same chance n/N to be in the prefix (over seeds)."""
    f = _frame(50)
    hits = {h: 0 for h in f}
    for seed in range(4000):
        for h in C.permute(f, seed)[:10]:
            hits[h] += 1
    for h, k in hits.items():
        assert 600 < k < 1000, (h, k)  # expected 800
