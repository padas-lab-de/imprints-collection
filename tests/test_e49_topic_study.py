import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "E49"))
from score import score  # noqa: E402
from tree import load_schema, load_tree  # noqa: E402
from vote import level_majority, plurality  # noqa: E402


def write(tmp_path, name, rows):
    p = tmp_path / name
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return p


@pytest.fixture
def poi(tmp_path):
    rows = [
        {"name": "Essen", "parent": "Essen"},
        {"name": "Restaurant", "parent": "Essen"},
        {"name": "Italienisches Restaurant", "parent": "Essen"},
        {"name": "Einzelhandel", "parent": "Einzelhandel"},
        {"name": "Lebensmittel", "parent": "Einzelhandel"},
        {"name": "Bäckerei", "parent": "Lebensmittel"},
        {"name": "Metzgerei", "parent": "Lebensmittel"},
        {"name": "Bar", "parent": "Essen"},
        {"name": "Bar", "parent": "Einzelhandel"},  # same name, two parents
        {"name": "Restaurant", "parent": "Essen"},  # exact duplicate row
    ]
    return load_tree(write(tmp_path, "poi.jsonl", rows), "poi")


@pytest.fixture
def wz(tmp_path):
    rows = [
        {"code": "I", "level": "abschnitt", "title": "Gastgewerbe", "parent": None, "keywords": []},
        {"code": "56", "level": "abteilung", "title": "Gastronomie", "parent": "I", "keywords": []},
        {"code": "56.1", "level": "gruppe", "title": "Restaurants", "parent": "56", "keywords": []},
        {"code": "56.11", "level": "klasse", "title": "Restaurants", "parent": "56.1", "keywords": []},
        {"code": "56.11.1", "level": "unterklasse", "title": "Restaurants mit Bedienung", "parent": "56.11",
         "keywords": ["Gaststätten", "Wirtshaus"]},
        {"code": "56.11.2", "level": "unterklasse", "title": "Selbstbedienung", "parent": "56.11", "keywords": []},
        {"code": "M", "level": "abschnitt", "title": "Freiberufliche Dienstleistungen", "parent": None, "keywords": []},
        {"code": "69", "level": "abteilung", "title": "Rechtsberatung", "parent": "M", "keywords": []},
    ]
    return load_tree(write(tmp_path, "wz.jsonl", rows), "wz")


def test_poi_loader(poi):
    assert len(poi) == 9  # duplicate Restaurant merged
    assert poi.roots == ["Essen", "Einzelhandel"]
    assert "Bar (Essen)" in poi and "Bar (Einzelhandel)" in poi and "Bar" not in poi
    assert poi.path("Bäckerei") == ["Einzelhandel", "Lebensmittel", "Bäckerei"]
    assert poi["Bäckerei"].level == 3 and poi.max_level == 3
    assert not poi.coded and poi.label("Bäckerei") == "Bäckerei"
    assert poi.resolve("bäckerei") == ("Bäckerei", "ci")
    assert poi.resolve("Einzelhandel > Lebensmittel > Metzgerei") == ("Metzgerei", "title")
    assert poi.resolve("Raumfahrt")[0] is None
    assert poi.resolve("[Lebensmittel] Einzelhandel > Lebensmittel") == ("Lebensmittel", "exact")
    assert "umfasst u. a.: Bäckerei, Metzgerei" in poi.text("Lebensmittel", "kw")


def test_wz_loader(wz):
    assert wz.coded and wz.roots == ["I", "M"]
    assert wz.path("56.11.1") == ["I", "56", "56.1", "56.11", "56.11.1"]
    assert wz["56.11.1"].level == 5 and wz["56.11.1"].level_name == "unterklasse"
    # single-child chains: 56.1 -> 56.11 (56 -> 56.1 too)
    assert wz.extend("56") == "56.11" and wz.extend("56.11") == "56.11"
    assert wz.canonical_path("56.1") == ["I", "56", "56.1", "56.11"]
    assert wz.candidates_up_to(4) == ["56.11", "69"]  # single-child nodes are stood for by their child
    assert wz.resolve("56.11.1 Restaurants mit Bedienung") == ("56.11.1", "title")
    assert "Stichwörter: Gaststätten, Wirtshaus" in wz.text("56.11.1", "kw")
    assert wz.text("56.11.1", "name") == "Restaurants mit Bedienung"


def test_real_schemas_load():
    for s in ("poi", "poi3", "wz"):
        if Path({"poi": "topics/poi_v2.jsonl", "poi3": "topics/poi_v3.jsonl", "wz": "topics/wz2025.jsonl"}[s]).is_file():
            t = load_schema(s)
            assert len(t) > 100 and t.roots
            assert all(t.path(i)[0] in t.roots for i in t.nodes)


def test_poi3_loader(tmp_path):
    rows = [
        {"id": "dining", "name": "Dining and Drinking", "parent": "dining", "fsq_ids": ["a"], "de": "Essen"},
        {"id": "restaurant", "name": "Restaurant", "parent": "dining", "fsq_ids": ["b"], "de": "Restaurant"},
        {"id": "italian-restaurant", "name": "Italian Restaurant", "parent": "restaurant", "fsq_ids": ["c"],
         "de": "Italienisches Restaurant"},
        {"id": "butcher", "name": "Butcher or Meat Store", "parent": "dining", "fsq_ids": ["d", "e"],
         "de": ["Metzger", "Wurstladen"]},
    ]
    t = load_tree(write(tmp_path, "poi_v3.jsonl", rows), "poi3")
    assert t.roots == ["dining"] and len(t) == 4 and not t.coded
    assert t.path("italian-restaurant") == ["dining", "restaurant", "italian-restaurant"]
    assert t["italian-restaurant"].title == "Italian Restaurant"
    assert t["butcher"].keywords == ["Metzger", "Wurstladen"]
    assert t.resolve("Italian Restaurant") == ("italian-restaurant", "ci")
    assert t.resolve("italian-restaurant") == ("italian-restaurant", "exact")


def test_poi3_real_schema_and_migration_map():
    if not Path("topics/poi_v3.jsonl").is_file():
        pytest.skip("run from the repository root")
    t = load_schema("poi3")
    assert len(t.roots) == 8 and t.max_level <= 3
    v2 = [json.loads(l)["name"] for l in Path("topics/poi_v2.jsonl").read_text(encoding="utf-8").splitlines() if l]
    m = json.loads(Path("results/E49/poi_v2_to_v3.json").read_text(encoding="utf-8"))
    assert set(m) == set(v2)  # every v2 node is mapped
    assert all(m[n] in t for n in v2)  # to an existing v3 node
    # every v3 node except added ones carries its v2 name(s), and they map back to it
    for i, n in t.nodes.items():
        assert all(m[de] == i for de in n.keywords)
    refs = Path("results/E49/refs/poi_v3.jsonl")
    for l in refs.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        assert r["main"] is None or t.path(r["main"]) == r["path"]
        assert all(e in t for e in r["extra"])


def test_loader_rejects_unknown_parent(tmp_path):
    p = write(tmp_path, "bad.jsonl", [{"name": "A", "parent": "A"}, {"name": "B", "parent": "X"}])
    with pytest.raises(ValueError):
        load_tree(p)


def pred(host, main, ranked=None, error=None):
    return {"host": host, "main": main, "ranked": ranked or ([main] if main else []), "error": error,
            "usage": {"calls": 1, "prompt_tokens": 10, "completion_tokens": 2}, "latency_s": 1.0}


def test_score_levels(poi):
    refs = {
        "a": {"host": "a", "main": "Bäckerei", "extra": []},
        "b": {"host": "b", "main": "Italienisches Restaurant", "extra": ["Restaurant"]},
        "c": {"host": "c", "main": "Lebensmittel", "extra": []},  # labeller stopped at level 2
        "d": {"host": "d", "main": "Metzgerei", "extra": []},
        "e": {"host": "e", "main": None, "extra": []},
    }
    preds = [
        pred("a", "Bäckerei"),  # right at all levels
        pred("b", "Restaurant", ranked=["Restaurant", "Italienisches Restaurant"]),  # near / lenient / top3
        pred("c", "Bäckerei"),  # deeper than the reference
        pred("d", "Lebensmittel"),  # stopped at level 2 (not covered at 3)
        pred("e", None),
        pred("x", "Essen", error="no_input"),  # not scored
    ]
    m = score(poi, refs, preds)
    assert m["n_scored"] == 4 and m["n_ref_none"] == 1 and m["ref_none_pred_abstained"] == 1
    L1, L2, L3 = m["levels"]
    assert L1["n_ref"] == 4 and L1["coverage"] == 1.0 and L1["precision"] == 1.0
    assert L2["n_ref"] == 4 and L2["precision"] == 0.75  # b wrong at level 2
    assert L3["n_ref"] == 2 and L3["coverage"] == 0.5 and L3["precision"] == 1.0 and L3["acc"] == 0.5
    # truncate both: a ok, b wrong, c: ref ends at Lebensmittel, pred[:3] longer -> wrong, d: pred[:3]=[E,L] != ref -> wrong
    assert L3["acc_trunc"] == 0.25
    assert L2["lenient"] == 1.0 and L2["near"] == 1.0 and L2["top3"] == 1.0
    assert m["cost_per_host"]["calls"] == 1.0


def test_score_single_child_chain(wz):
    refs = {"h": {"host": "h", "main": "56.11", "extra": []}}
    m = score(wz, refs, [pred("h", "56.1")])  # 56.1 has one child: same decision
    assert [lv["acc_trunc"] for lv in m["levels"]] == [1.0, 1.0, 1.0, 1.0, 1.0]


def test_votes(poi):
    assert level_majority(poi, ["Bäckerei", "Metzgerei", "Bäckerei"]) == "Bäckerei"
    assert level_majority(poi, ["Bäckerei", "Metzgerei", "Lebensmittel"]) == "Lebensmittel"
    assert level_majority(poi, ["Bäckerei", "Restaurant", None]) is None
    assert level_majority(poi, ["Bäckerei", "Metzgerei", "Restaurant"]) == "Lebensmittel"
    assert level_majority(poi, ["Bäckerei", "Bar (Einzelhandel)", "Restaurant"]) == "Einzelhandel"
    assert plurality(poi, ["Restaurant", "Bäckerei", "Bäckerei"]) == "Bäckerei"
    assert plurality(poi, [None, None]) is None


def test_rules_block(wz, tmp_path):
    from run import make_tag
    from strategies import DEFAULTS, load_rules, system_prompt

    f = tmp_path / "wz_rules.md"
    f.write_text("# comment, not sent\nRegeln:\n1. Weingut: 11.02.0\n", encoding="utf-8")
    rules = load_rules(f)
    assert rules == "Regeln:\n1. Weingut: 11.02.0"
    base = dict(DEFAULTS)
    legacy = {k: v for k, v in base.items() if k != "rules"}  # configs from before --rules existed
    off = system_prompt(wz, base)
    assert off == system_prompt(wz, legacy) and "Regeln" not in off  # default off: prompt (cache key) unchanged
    on = system_prompt(wz, dict(base, rules=rules))
    assert on.startswith(off) and on.endswith("1. Weingut: 11.02.0") and "comment" not in on
    assert make_tag(base, "gemma4-31b-it", 1) == "flat__gemma__home__dmax__nt-path"
    assert make_tag(dict(base, rules=rules), "gemma4-31b-it", 1, "wz_rules").endswith("__rules-wz_rules")


def test_keep_outside(wz):
    from client import Usage
    from strategies import DEFAULTS, choose

    class Fake:
        def chat(self, *a, **k):
            return {"id": "69", "konfidenz": 0.9}, None  # valid node, not offered

    drop = choose(Fake(), "m", wz, dict(DEFAULTS), Usage(), "site", ["56.11.1"])
    assert drop["ids"] == [] and "outside_candidates" in drop["how"]
    keep = choose(Fake(), "m", wz, dict(DEFAULTS, keep_outside=True), Usage(), "site", ["56.11.1"])
    assert keep["ids"] == ["69"] and "outside_kept" in keep["how"]


def test_rules_candidates(wz, tmp_path):
    from run import make_tag
    from strategies import DEFAULTS, retrieve, rules_code_ids

    ids = rules_code_ids(wz, "1. Restaurant 56.11.1 und 69, nicht 99.99.9 [56.11]\n2. 56.11.1 wieder 2025")
    assert ids == ["56.11.1", "69", "56.11"]
    assert len(ids) == len(set(ids)) and "99.99.9" not in ids and "1" not in ids
    base = dict(DEFAULTS)
    assert make_tag(base, "m", 1) == make_tag(dict(base, rules_cands=None), "m", 1)  # off: tag unchanged
    assert make_tag(dict(base, rules_cands=ids), "m", 1).endswith("rulescand")

    class Fake:
        def embed(self, texts, usage):
            return [[1.0] + [0.0] * 3 for _ in texts]

        def chat(self, *a, **k):
            return {"id": "69"}, None

    rec = {"host": "h", "home": "Weingut"}
    import strategies

    seen = {}
    orig = strategies.choose
    strategies.choose = lambda c, m, t, cfg, u, h, cands, *a, **k: seen.setdefault("c", cands) and orig(c, m, t, cfg, u, h, cands, *a, **k)
    try:
        strategies.retrieve(Fake(), "m", wz, rec, dict(base, strategy="retrieve", k=1, rules_cands=["69"]), strategies.Usage())
    except Exception:
        pass
    finally:
        strategies.choose = orig
    assert "69" in seen.get("c", [])
