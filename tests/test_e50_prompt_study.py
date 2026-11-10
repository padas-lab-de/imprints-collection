import hashlib
import json
import re
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "E49"))
sys.path.insert(0, str(ROOT / "scripts" / "E50"))
import addr_score as AS  # noqa: E402
import address as AD  # noqa: E402
import compare as CP  # noqa: E402
import joint as JT  # noqa: E402
import strategies as S  # noqa: E402
import topic as TP  # noqa: E402
from client import Client  # noqa: E402
from llm import LLM, Usage2, build_body  # noqa: E402
from tree import load_schema  # noqa: E402

REC = {"host": "baeckerei-test.de", "homepage_text": "Bäckerei Test\nBrot und Brötchen\n" + "x" * 7000,
       "imprint_text": "Impressum\nBäckerei Test GmbH\nHauptstr. 5\nD-94032 Passau", "meta": {"title": "Bäckerei"}}


def _vec(text: str) -> list[float]:
    h = hashlib.sha256(text.encode()).digest()
    return [b / 255 for b in h[:8]]


class Fake:
    """Replaces the HTTP transport: records request bodies, returns a canned chat answer and fake embeddings."""

    def setup(self, answer='{"id": "KEINE", "konfidenz": 0.5}', finish="stop"):
        self.base, self._key, self.cache, self.sem = "", "", Path("/nonexistent"), threading.Semaphore(4)
        self.bodies, self.answer, self.finish = [], answer, finish
        return self

    def _post(self, path, body, kind, timeout=300):
        if path == "/embeddings":
            return {"data": [{"index": i, "embedding": _vec(t)} for i, t in enumerate(body["input"])],
                    "usage": {"prompt_tokens": 1}}, 0.0, False
        self.bodies.append(body)
        return {"choices": [{"message": {"content": self.answer}, "finish_reason": self.finish}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 10, "prompt_tokens_details": {"cached_tokens": 60},
                          "completion_tokens_details": {"reasoning_tokens": 4}}}, 1.0, False


class FakeE49(Fake, Client):
    pass


class FakeLLM(Fake, LLM):
    pass


@pytest.fixture(scope="module")
def poi3():
    return load_schema("poi3")


@pytest.fixture(scope="module")
def wz():
    return load_schema("wz")


def e49_cfg(**kw):
    return dict(S.DEFAULTS, input="both", **kw)


@pytest.mark.parametrize("e49kw,reasoning", [({"reason": "short"}, "short"), ({"think": "on"}, "default"),
                                             ({}, "none")])
def test_poi_base_body_equals_e49(poi3, e49kw, reasoning):
    old = FakeE49().setup()
    S.flat(old, "m", poi3, REC, e49_cfg(node_lang="both", **e49kw), Usage2())
    new = FakeLLM().setup()
    TP.flat(new, "m", poi3, REC, TP.full_cfg(strategy="flat", input="both", node_lang="both", reasoning=reasoning),
            Usage2())
    assert old.bodies == new.bodies


def test_wz_base_body_equals_e49(wz):
    old = FakeE49().setup()
    S.retrieve(old, "m", wz, REC, e49_cfg(strategy="retrieve"), Usage2())
    new = FakeLLM().setup()
    TP.retrieve(new, "m", wz, REC, TP.full_cfg(strategy="retrieve", input="both"), Usage2())
    assert old.bodies == new.bodies and len(new.bodies) == 1


def test_build_body_levels():
    msgs = [{"role": "user", "content": "x"}]
    assert build_body("m", msgs, max_tokens=400)["reasoning_effort"] == "none"
    b = build_body("m", msgs, max_tokens=400, reasoning="default")
    assert "reasoning_effort" not in b and b["max_tokens"] == 6000
    b = build_body("m", msgs, max_tokens=400, reasoning="low", response_format={"type": "json_object"})
    assert b["reasoning_effort"] == "low" and b["max_tokens"] == 8000 and b["response_format"]["type"] == "json_object"
    with pytest.raises(ValueError):
        build_body("m", msgs, max_tokens=400, reasoning="high-ish")


def test_usage2_and_cut_reply(poi3):
    llm = FakeLLM().setup(answer='{"id": "bakery"', finish="length")
    u = Usage2()
    with pytest.raises(ValueError, match="cut at max_tokens"):
        llm.chat2("m", [{"role": "user", "content": "x"}], u, max_tokens=10)
    assert u.cached_prompt_tokens == 60 and u.reasoning_tokens == 4 and u.truncated == 1 and u.calls == 1
    p = TP.predict(llm, "m", poi3, REC, TP.full_cfg(strategy="flat", input="both"))
    assert p["main"] is None and p["error"].startswith("ValueError: cut")


def test_variants(poi3, wz):
    base = TP.full_cfg(strategy="flat", input="both", node_lang="both")
    cands = poi3.candidates_up_to(99)
    m0 = TP.messages(poi3, base, TP.site_text(REC, base), cands)
    m1 = TP.messages(poi3, dict(base, layout="list_first"), TP.site_text(REC, base), cands)
    assert m1[1]["content"] == TP.site_text(REC, base) and "[KEINE]" in m1[0]["content"]
    assert m0[0]["content"] != m1[0]["content"] and m0[1]["content"].startswith(TP.site_text(REC, base))
    # budget: 1500 characters per field
    s = TP.site_text(REC, dict(base, site_chars=1500))
    assert s.count("x") == 1500 - len("Bäckerei Test\nBrot und Brötchen\n") and "Hauptstr. 5" in s
    # wording and language
    g = TP.system_text(poi3, dict(base, wording="guide"))
    assert g.startswith("Du ordnest") and "7. Passt keine" in g and "Schema:" in g
    assert TP.system_text(wz, dict(base, wording="guide", lang="en")).count("The category names are German.") == 1
    assert TP.system_text(poi3, dict(base, wording="minimal")).count("\n") == 1
    assert "Answer format" in TP.messages(poi3, dict(base, lang="en"), "site", cands)[1]["content"]
    # shots
    assert "Beispiele" in TP.system_text(poi3, dict(base, shots=4))
    # tags
    assert TP.tag(base, "gemma") == "flat__gemma__r-none"
    assert TP.tag(dict(base, reasoning="short", fmt="schema", site_chars=3000), "qwen") == \
        "flat__qwen__r-short__f-schema__c3000"


@pytest.mark.parametrize("reasoning", ["none", "short"])
def test_schema_mirrors_answer_format(poi3, reasoning):
    cfg = TP.full_cfg(strategy="flat", fmt="schema", reasoning=reasoning)
    rf = TP.response_format(cfg, ["bakery", "cafe"])
    sch = rf["json_schema"]["schema"]
    keys = re.findall(r'"(\w+)":', S.answer_spec(cfg))
    assert list(sch["properties"]) == keys and sch["required"] == keys and sch["additionalProperties"] is False
    assert sch["properties"]["id"]["enum"] == ["bakery", "cafe", "KEINE"]
    assert TP.response_format(dict(cfg, fmt="json_object"), []) == {"type": "json_object"}
    assert TP.response_format(dict(cfg, fmt="free"), []) is None


def test_address_prompt_parse_and_schema():
    cfg = AD.full_cfg(fmt="schema")
    msgs = AD.messages(REC, cfg)
    assert "Hauptstr. 5" in msgs[1]["content"] and "Brötchen" not in msgs[1]["content"]
    keys = re.findall(r'"(\w+)":', AD.answer_spec(cfg))
    sch = AD.response_format(cfg)["json_schema"]["schema"]
    assert list(sch["properties"]) == ["addresses", "no_address_reason"]
    assert set(keys) == set(sch["properties"]) | set(sch["properties"]["addresses"]["items"]["properties"])
    assert AD.messages(dict(REC, imprint_text=""), cfg) is None
    ans = {"addresses": [{"street": "Bank", "number": "1", "postcode": "1", "town": "x", "country": "", "role": "agency",
                          "main": False},
                         {"street": "Hauptstr.", "number": "5", "postcode": "94032", "town": "Passau", "country": "",
                          "role": "operator", "main": True}], "no_address_reason": None}
    p = AD.parse(ans)
    assert p["main_index"] == 1 and p["no_address_reason"] is None
    assert AD.parse({"addresses": [], "no_address_reason": "no_imprint"})["no_address_reason"] == "no_imprint"
    assert AD.parse({"addresses": []})["no_address_reason"] == "imprint_without_address"
    m = AD.parse({"address": {"street": "A", "number": "1", "postcode": "1", "town": "T", "country": ""},
                  "no_address_reason": None}, "main")
    assert m["main_index"] == 0
    mm = AD.full_cfg(mode="main", fmt="schema")
    assert "address" in AD.response_format(mm)["json_schema"]["schema"]["properties"]
    llm = FakeLLM().setup()
    out = AD.predict(llm, "m", dict(REC, imprint_text=""), cfg)
    assert out["no_address_reason"] == "no_imprint" and out["usage"]["calls"] == 0


def test_joint_prompt(poi3, wz):
    trees = {"poi3": poi3, "wz": wz}
    cfg = AD.full_cfg(node_lang="both", reasoning="short", fmt="schema")
    ans = json.dumps({"begruendung": "x", "poi": "bakery", "wz": "KEINE",
                      "addresses": [{"street": "Hauptstr.", "number": "5", "postcode": "94032", "town": "Passau",
                                     "country": "", "role": "operator", "main": True}], "no_address_reason": None})
    llm = FakeLLM().setup(answer=ans)
    out = JT.predict(llm, "m", trees, REC, cfg)
    assert out["error"] is None and out["poi"]["main"] == "bakery" and out["wz"]["main"] is None
    assert out["address"]["main_index"] == 0
    body = llm.bodies[0]
    sys_, user = body["messages"][0]["content"], body["messages"][1]["content"]
    assert "[bakery]" in sys_ and "Teil C" in sys_ and "Hauptstr. 5" in user and "Teil B" in user
    props = body["response_format"]["json_schema"]["schema"]["properties"]
    assert list(props) == ["begruendung", "poi", "wz", "addresses", "no_address_reason"]
    keys = re.findall(r'"(\w+)":', JT.answer_spec(cfg, ("poi", "wz", "address")))
    assert keys[:3] == ["begruendung", "poi", "wz"] and "no_address_reason" in keys
    two = JT.messages(trees, cfg, "site", ["bakery"], ["10"], ("poi", "wz"))
    assert "Teil C" not in two[0]["content"] and "addresses" not in two[1]["content"]


def test_addr_score():
    ref = {"a.de": AS.to_record({"addresses": [{"street": "Hauptstraße", "number": "5", "postcode": "94032",
                                                "town": "Passau", "country": "Deutschland"}], "main_address_index": 0}),
           "b.de": AS.to_record({"addresses": [], "no_address_reason": "imprint_without_address"}),
           "c.de": AS.to_record({"address": {"streetname": "Ring", "housenumber": "1", "postalcode": "1010",
                                             "town": "Wien", "country": ""}})}
    pred = {"a.de": AS.to_record({"addresses": [{"street": "Hauptstr.", "number": "5", "postcode": "D-94032",
                                                 "town": "Passau", "country": "DE", "main": True}]}),
            "b.de": AS.to_record({"addresses": [{"street": "X", "number": "1", "postcode": "1", "town": "Y",
                                                 "country": "", "role": "agency", "main": False}],
                                  "no_address_reason": "imprint_without_address"}),
            "c.de": AS.to_record({"addresses": [], "no_address_reason": "imprint_without_address"})}
    m = AS.score(ref, pred, texts={"a.de": "Hauptstr. 5, D-94032 Passau"})
    assert m["n"] == 3 and m["main_exact"] == 1.0
    assert m["noaddr_P"] == 0.5 and m["noaddr_R"] == 1.0 and m["false_address_rate"] == 0.0
    assert m["missed_address_rate"] == 0.5 and m["evidence"] == 1.0
    assert m["main_P"] == 1.0 and m["main_R"] == round(5 / 9, 3)
    assert AS.field_eq("town", "Frankfurt", "Frankfurt am Main") and not AS.field_eq("town", "Bonn", "Berlin")


def test_compare_paired_and_verdict(poi3):
    refs = {f"h{i}": {"host": f"h{i}", "main": "bakery"} for i in range(40)}
    base = [{"host": f"h{i}", "main": "bakery" if i < 30 else None, "usage": {"prompt_tokens": 1000}} for i in range(40)]
    var = [{"host": f"h{i}", "main": "bakery" if i < 38 else None, "usage": {"prompt_tokens": 500}} for i in range(40)]
    vb, vv = CP.host_vectors(poi3, refs, base), CP.host_vectors(poi3, refs, var)
    hs = sorted(vb)
    pr = CP.paired([(vv, vb)], hs, 2)
    assert pr["d"] == pytest.approx(0.2) and pr["wins"] == 8 and pr["losses"] == 0 and pr["p"] < 0.01
    assert pr["lo"] > 0 and pr["cost_ratio"] == pytest.approx(0.5)
    assert CP.verdict(pr, [0.2], [0.0]) == "better"
    worse = CP.paired([(vb, vv)], hs, 2)
    assert CP.verdict(worse, [-0.2], [0.0]) == "worse/inadmissible"
    same = CP.paired([(vb, vb)], hs, 2)
    assert CP.verdict(same, [0.0], [0.0]) == "no difference"
    assert CP.parse_tag("flat__gemma__r-short__f-schema__c3000") == ("gemma", "r-short", "f-schema__c3000")


def test_layout_list_first_q_and_tags(poi3):
    base = TP.full_cfg(strategy="flat", node_lang="both")
    cands = poi3.candidates_up_to(2)[:5]
    m = TP.messages(poi3, dict(base, layout="list_first_q"), "SITE", cands)
    m0 = TP.messages(poi3, dict(base, layout="list_first_q"), "OTHER", cands)
    assert m[0] == m0[0]  # static system prefix
    assert m[1]["content"].startswith("SITE") and TP.QUESTION["de"] in m[1]["content"]
    assert m[1]["content"].index(TP.QUESTION["de"]) > m[1]["content"].index("SITE")
    assert "Antwortformat" in m[1]["content"] and "Antwortformat" not in m[0]["content"]
    assert TP.tag(dict(base, layout="list_first_q"), "gemma") == "flat__gemma__r-none__list_first_q"
    ret = dict(base, strategy="retrieve")
    assert TP.tag(ret, "qwen") == "retrieve__qwen__r-none"
    assert TP.tag(dict(ret, k=50), "qwen") == "retrieve__qwen__r-none__k50"
    acfg = AD.full_cfg(reasoning="short")
    assert TP.tag(acfg, "gemma", task="address") == "address__gemma__r-short"
    assert TP.tag(dict(acfg, mode="main", fmt="schema"), "gemma", task="address") == \
        "address__gemma__r-short__f-schema__mode-main"
    # strategy-aware run keys
    assert CP.parse_tag("retrieve__qwen__r-default", "poi3") == ("qwen", "r-default", "retrieve")
    assert CP.parse_tag("retrieve__qwen__r-none__c1500", "wz") == ("qwen", "r-none", "c1500")
    assert CP.parse_tag("joint-poi-wz__gemma__r-short", "wz") == ("gemma", "r-short", "joint-poi-wz")
    assert CP.parse_tag("address__gemma__r-none__mode-main", "address") == ("gemma", "r-none", "mode-main")


SPEC_REF = {"host": "u.de", "addresses": [
    {"role": "operator", "street": "Schillingallee", "number": "35", "postcode": "18057", "town": "Rostock",
     "country": "", "po_box": False, "modality": "text", "evidence": "x"},
    {"role": "operator", "street": "Postfach", "number": "10 08 88", "postcode": "18055", "town": "Rostock",
     "country": "", "po_box": True, "modality": "text", "evidence": "y"},
    {"role": "agency", "street": "Weg", "number": "1", "postcode": "10115", "town": "Berlin", "country": "",
     "po_box": False, "modality": "text", "evidence": "z"}],
    "main_address_index": 0, "no_address_reason": None, "flags": ["po_box"], "confidence": "high", "note": "",
    "agree_ab": True}


def test_addr_spec_adapter():
    r = AS.to_record(SPEC_REF)
    assert r["main_index"] == 0 and r["no_address_reason"] is None and len(r["addresses"]) == 3
    assert [a["po_box"] for a in r["addresses"]] == [False, True, False]
    assert [a["role"] for a in r["addresses"]] == ["operator", "operator", "agency"]
    only_box = dict(SPEC_REF, addresses=[SPEC_REF["addresses"][1]], main_address_index=0)
    assert AS.to_record(only_box)["addresses"][0]["po_box"]
    none = {"host": "n.de", "addresses": [SPEC_REF["addresses"][2]], "main_address_index": None,
            "no_address_reason": "imprint_without_address"}
    rn = AS.to_record(none)
    assert rn["main_index"] is None and rn["no_address_reason"] == "imprint_without_address"
    # a predicted P.O. box is recognised from the street word
    pred = AD.parse({"addresses": [{"street": "Postfach", "number": "1137", "postcode": "91502", "town": "Ansbach",
                                    "country": "", "role": "operator", "main": True}], "no_address_reason": None})
    assert AS.to_record(pred)["addresses"][0]["po_box"]
    # scoring: main ok, reason accuracy, P.O. box counts
    refs = {"u.de": r, "n.de": rn, "e.de": AS.to_record({"addresses": [], "main_address_index": None,
                                                         "no_address_reason": "no_imprint"})}
    preds = {"u.de": AS.to_record({"addresses": [dict(SPEC_REF["addresses"][0], main=True)]}),
             "n.de": AS.to_record({"addresses": [], "main_index": None, "no_address_reason": "no_imprint"}),
             "e.de": AS.to_record({"addresses": [], "main_index": None, "no_address_reason": "no_imprint"})}
    m = AS.score(refs, preds)
    assert m["main_ok"] == 1.0 and m["main_exact"] == 1.0 and m["reason_acc"] == 0.5
    assert m["per_host"]["u.de"]["both_main"] and not m["per_host"]["n.de"]["both_main"]
    assert m["main_po_box_n"] == 0


def test_compare_address_vectors():
    refs = {"u.de": SPEC_REF, "n.de": {"host": "n.de", "addresses": [], "main_address_index": None,
                                        "no_address_reason": "imprint_without_address"}}
    good = [{"host": "u.de", "addresses": [dict(SPEC_REF["addresses"][0], main=True)], "main_index": 0,
             "no_address_reason": None, "usage": {"prompt_tokens": 100, "completion_tokens": 10}},
            {"host": "n.de", "addresses": [], "main_index": None, "no_address_reason": "imprint_without_address",
             "usage": {}}]
    bad = [dict(good[0], addresses=[dict(SPEC_REF["addresses"][1], main=True)]),
           dict(good[1], addresses=[dict(SPEC_REF["addresses"][2], role="operator", main=True)], main_index=0,
                no_address_reason=None)]
    vg, vb = CP.addr_vectors(refs, good), CP.addr_vectors(refs, bad)
    assert vg["u.de"]["hit"] == [1, 1] and vg["u.de"]["cov"] == [1, 1] and vg["u.de"]["C"] == 200
    assert vg["n.de"]["hit"] == [1, 0] and vg["n.de"]["cov"] == [1, 0]
    assert vb["u.de"]["hit"] == [0, 0] and vb["u.de"]["cov"] == [1, 1]
    assert vb["n.de"]["hit"] == [0, 0]


def test_final_table_row_and_jsonl_line_separators(tmp_path):
    import final_table as FT

    v = {f"h{i}": {"hit": [int(i < 3)], "cov": [1], "fail": 0, "C": 10} for i in range(4)}
    r = FT.row(v, sorted(v), 1)
    assert r["n"] == 4 and r["acc"] == 0.75 and r["P"] == 0.75 and r["C"] == 10
    assert 0 <= r["lo"] <= r["acc"] <= r["hi"] <= 1
    assert FT.row(v, [], 1) == {"n": 0}
    p = tmp_path / "x.jsonl"
    p.write_text(json.dumps({"host": "a.de", "t": "x y"}, ensure_ascii=False) + "\n", encoding="utf-8")
    assert CP.load_jsonl(p)[0]["t"] == "x y"
    assert list(AS.load(p)) == ["a.de"]
