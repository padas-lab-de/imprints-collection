import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation"))
from tree import load_schema, load_tree  # noqa
from vote import level_majority, plurality  # noqa


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


def test_poi3_real_schema():
    if not Path("topics/poi_v3.jsonl").is_file():
        pytest.skip("run from the repository root")
    t = load_schema("poi3")
    assert len(t.roots) == 8 and t.max_level <= 3


def test_loader_rejects_unknown_parent(tmp_path):
    p = write(tmp_path, "bad.jsonl", [{"name": "A", "parent": "A"}, {"name": "B", "parent": "X"}])
    with pytest.raises(ValueError):
        load_tree(p)


def test_votes(poi):
    assert level_majority(poi, ["Bäckerei", "Metzgerei", "Bäckerei"]) == "Bäckerei"
    assert level_majority(poi, ["Bäckerei", "Metzgerei", "Lebensmittel"]) == "Lebensmittel"
    assert level_majority(poi, ["Bäckerei", "Restaurant", None]) is None
    assert level_majority(poi, ["Bäckerei", "Metzgerei", "Restaurant"]) == "Lebensmittel"
    assert level_majority(poi, ["Bäckerei", "Bar (Einzelhandel)", "Restaurant"]) == "Einzelhandel"
    assert plurality(poi, ["Restaurant", "Bäckerei", "Bäckerei"]) == "Bäckerei"
    assert plurality(poi, [None, None]) is None


def test_rules_block(wz, tmp_path):
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
    from strategies import DEFAULTS, retrieve, rules_code_ids

    ids = rules_code_ids(wz, "1. Restaurant 56.11.1 und 69, nicht 99.99.9 [56.11]\n2. 56.11.1 wieder 2025")
    assert ids == ["56.11.1", "69", "56.11"]
    assert len(ids) == len(set(ids)) and "99.99.9" not in ids and "1" not in ids
    base = dict(DEFAULTS)

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


def test_poi3_prompts_use_v3_names():
    from strategies import DEFAULTS, cand_line, schema_line, system_prompt

    if not Path("topics/poi_v3.jsonl").is_file():
        pytest.skip("topics/poi_v3.jsonl missing")
    t3 = load_schema("poi3")
    for lang in ("de", "en"):
        cfg = dict(DEFAULTS, lang=lang)
        s3 = system_prompt(t3, cfg)
        assert "Italian Restaurant" in s3 and "Italienisches Restaurant" not in s3
        assert "english" in schema_line(cfg, t3).lower() or "englisch" in schema_line(cfg, t3).lower()
    assert cand_line(t3, "italian-restaurant", dict(DEFAULTS, node_text="path")).startswith("[italian-restaurant] Dining")


def test_poi3_bilingual_node_text_opt_in():
    from strategies import DEFAULTS, cand_line, system_prompt

    if not Path("topics/poi_v3.jsonl").is_file():
        pytest.skip("topics/poi_v3.jsonl missing")
    t3 = load_schema("poi3")
    off, both = dict(DEFAULTS, node_text="path"), dict(DEFAULTS, node_text="path", node_lang="both")
    # default: English names only
    assert cand_line(t3, "italian-restaurant", off) == "[italian-restaurant] Dining and Drinking > Restaurant > Italian Restaurant"
    line = cand_line(t3, "italian-restaurant", both)
    assert line.startswith("[italian-restaurant] Dining and Drinking (") and "Italian Restaurant (Italienisches Restaurant)" in line
    # a node whose German name is a list (merged v2 nodes) shows the first two names
    assert "(" in t3.title_of("manufacturer-or-factory", "both") and t3.title_of("manufacturer-or-factory") == "Manufacturer or Factory"
    # manufacturer line: off by default
    assert system_prompt(t3, dict(DEFAULTS)) == system_prompt(t3, dict(DEFAULTS, mfr_line=False))
    assert "Manufacturer or Factory" in system_prompt(t3, dict(DEFAULTS, mfr_line=True))
