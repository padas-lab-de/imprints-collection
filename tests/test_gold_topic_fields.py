"""Topic labels (POI v3 + WZ 2025) in the gold labelling tool (D51 B, E49 rules R4, R5)."""

import copy
import json
import threading
import urllib.parse
from http.server import ThreadingHTTPServer

import pytest
from test_gold_labels import good, http, make_store

from ic.gold.annotate import schema, topics
from ic.gold.annotate.server import make_handler
from ic.gold.annotate.store import Store


def tl(**kw):
    d = {
        "poi": {"main": "italian-restaurant", "extra": ["thai-restaurant"], "confidence": "high",
                "note": "", "online_only": False},
        "wz": {"main": "56.11.1", "extra": [], "confidence": "medium", "note": ""},
    }
    for k, v in kw.items():
        sch, f = k.split("__")
        d[sch][f] = v
    return d


def v2(**kw):
    return good(schema_version=2, topic_labels=kw.pop("topic_labels", tl()), **kw)


def test_ids_exist_in_trees():
    assert "italian-restaurant" in topics.get_tree("poi").nodes
    assert len(topics.get_tree("poi")) == 753
    assert "56.11.1" in topics.get_tree("wz").nodes


def test_valid_v2_label_passes_and_old_label_still_valid():
    assert schema.validate_label(v2()) == []
    assert schema.validate_label(good()) == []  # no topic labels, no schema_version: version 1


def pick_valid_poi():
    t = topics.get_tree("poi")
    leaf = next(n for n in t.nodes.values() if not n.children and n.level >= 3)
    return leaf, t[leaf.path[1]]


def test_validation_rules():
    leaf, mid = pick_valid_poi()
    ok = tl(poi__main=leaf.id, poi__extra=[])
    assert schema.validate_label(v2(topic_labels=ok)) == []
    # unknown ids
    assert any("unknown main" in e for e in schema.validate_label(v2(topic_labels=tl(wz__main="99.99.9"))))
    assert any("unknown extra" in e for e in schema.validate_label(v2(topic_labels=tl(
        poi__main=leaf.id, poi__extra=["no-such-node"]))))
    # R5: extra is the main, or an ancestor of the main
    assert any("R5" in e for e in schema.validate_label(v2(topic_labels=tl(
        poi__main=leaf.id, poi__extra=[leaf.id]))))
    assert any("R5" in e for e in schema.validate_label(v2(topic_labels=tl(
        poi__main=leaf.id, poi__extra=[mid.id]))))
    assert any("R5" in e for e in schema.validate_label(v2(topic_labels=tl(
        wz__main="56.11.1", wz__extra=["56.11"]))))
    # a descendant or a sibling is fine as extra
    assert schema.validate_label(v2(topic_labels=tl(wz__main="56.11", wz__extra=["56.11.1", "56.12"]))) == []
    # more than two extras, duplicates, bad confidence, online_only type
    assert schema.validate_label(v2(topic_labels=tl(wz__extra=["56.12", "56.12.1", "56.11.2"])))
    assert schema.validate_label(v2(topic_labels=tl(wz__extra=["56.12", "56.12"])))
    assert schema.validate_label(v2(topic_labels=tl(wz__confidence="sure")))
    assert schema.validate_label(v2(topic_labels=tl(poi__online_only="yes")))
    # no main: needs a note and no extras
    assert schema.validate_label(v2(topic_labels=tl(wz__main=None, wz__extra=[])))
    assert schema.validate_label(v2(topic_labels=tl(wz__main=None, wz__extra=[], wz__note="parked"))) == []
    assert schema.validate_label(v2(topic_labels=tl(wz__main=None, wz__extra=["56.12"], wz__note="parked")))
    # version 2 on a live site needs both schemas
    only_poi = tl()
    del only_poi["wz"]
    assert schema.validate_label(v2(topic_labels=only_poi))
    assert schema.validate_label(good(schema_version=2))


def test_store_roundtrip_with_and_without_topic_fields(tmp_path):
    st = make_store(tmp_path)
    rec, errs, _ = st.save_label(good(), 1)  # old style
    assert errs == [] and "topic_labels" not in rec
    # restaurant is the parent of italian-restaurant: R5 (the duplicate is dropped by normalise)
    rec, errs, _ = st.save_label(v2(topic_labels=tl(poi__extra=[" restaurant ", "restaurant"])), 2)
    assert rec is None and any("R5" in e for e in errs)
    t = tl(poi__extra=["thai-restaurant"], wz__extra=["56.12"])
    rec, errs, _ = st.save_label(v2(topic_labels=t), 2)
    assert errs == []
    back = Store(st.data_dir, "L1").load_labels()["example.de"]
    assert back["schema_version"] == 2
    assert back["topic_labels"]["wz"] == {"main": "56.11.1", "extra": ["56.12"], "confidence": "medium", "note": ""}
    assert back["topic_labels"]["poi"]["online_only"] is False
    # an old line in the file (no topic fields) still loads
    p = st.labels_path
    old = {k: v for k, v in back.items() if k not in ("topic_labels", "schema_version")}
    p.write_text(json.dumps(old) + "\n", encoding="utf-8")
    assert "topic_labels" not in Store(st.data_dir, "L1").load_labels()["example.de"]


def test_prefill_never_carries_topic_labels(tmp_path):
    st = make_store(tmp_path)
    rec = {"host": "example.de", "source": {"model": "m", "prompt": "p"},
           "label": {"site_status": "live", "topic_labels": tl()}}
    (st.data_dir / "prefill.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")
    st = Store(st.data_dir, "L1")
    assert "topic_labels" not in st.prefill("example.de")["label"]


def test_search_ranks_and_returns_paths():
    r = topics.search("poi", "restaurant")
    assert r[0]["id"] == "restaurant" and r[0]["path"][0]["id"] == "dining-and-drinking"
    assert all(h["path"][-1]["id"] == h["id"] for h in r)
    de = topics.search("poi", "Italienisches Restaurant")
    assert de[0]["id"] == "italian-restaurant" and de[0]["de"] == "Italienisches Restaurant"
    assert topics.search("poi", "baeckerei") == topics.search("poi", "bäckerei")  # umlaut folding
    wz = topics.search("wz", "56.11.1")
    assert wz[0]["id"] == "56.11.1" and [p["id"] for p in wz[0]["path"]][-3:] == ["56.1", "56.11", "56.11.1"]
    assert any(h["id"] == "56.11.4" for h in topics.search("wz", "Cafés"))
    assert any(not h["leaf"] for h in topics.search("wz", "56.11"))  # inner nodes are offered
    assert topics.search("poi", "   ") == []


@pytest.fixture
def running(tmp_path):
    st = make_store(tmp_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(st))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield st, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_http_topic_search_and_save(running):
    st, base = running
    code, body = http(base + "/api/topic_search?schema=wz&q=" + urllib.parse.quote("Zahnärzte"))
    res = json.loads(body)["results"]
    assert code == 200 and res and res[0]["path"][-1]["id"] == res[0]["id"]
    code, body = http(base + "/api/topic_search?schema=poi&id=italian-restaurant")
    assert code == 200 and json.loads(body)["results"][0]["path"][-1]["title"] == "Italian Restaurant"
    assert http(base + "/api/topic_search?schema=poi&id=nope")[0] == 404
    assert http(base + "/api/topic_search?schema=xx&q=a")[0] == 400
    state = json.loads(http(base + "/api/state")[1])
    assert state["enums"]["confidence"] == ["high", "medium", "low"] and state["enums"]["schema_version"] == 2
    bad = v2(topic_labels=tl(poi__extra=["restaurant"]))
    code, body = http(base + "/api/label", {"label": bad, "elapsed": 1})
    assert code == 400 and any("R5" in e for e in json.loads(body)["errors"])
    code, body = http(base + "/api/label", {"label": v2(topic_labels=tl(poi__extra=[])), "elapsed": 1})
    assert code == 200
    item = json.loads(http(base + "/api/item?host=example.de")[1])
    assert item["label"]["topic_labels"]["poi"]["main"] == "italian-restaurant"
    assert copy.deepcopy(item["prefill"]) is None
