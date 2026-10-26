"""Label schema validation, save/load roundtrip, and the HTTP tool (localhost only)."""

import copy
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from ic.gold.annotate import schema
from ic.gold.annotate.server import make_handler
from ic.gold.annotate.store import Store


def addr(**kw):
    a = {
        "role": "operator",
        "street": "Hauptstr.",
        "number": "12a",
        "postcode": "94032",
        "town": "Passau",
        "country": "Deutschland",
        "po_box": False,
        "modality": "text",
        "evidence": "Hauptstr. 12a 94032 Passau",
    }
    a.update(kw)
    return a


def good(**kw):
    lab = {
        "host": "example.de",
        "site_status": "live",
        "imprint_present": True,
        "imprint_url": "https://example.de/impressum",
        "imprint_location": "separate_page",
        "addresses": [addr()],
        "main_address_index": 0,
        "no_address_reason": None,
        "operator_type": "corporate",
        "topic": "Retail",
        "topic_ambiguous": False,
        "flags": [],
        "comment": "",
    }
    lab.update(kw)
    return lab


def test_valid_label_passes():
    assert schema.validate_label(good()) == []


def test_enum_values_match_design():
    assert len(schema.TOPICS) == 11
    assert "none" in schema.IMPRINT_LOCATION and "pdf" in schema.IMPRINT_LOCATION
    assert set(schema.NO_ADDRESS_REASON) == {"no_imprint", "imprint_without_address", "site_dead"}


@pytest.mark.parametrize(
    "change",
    [
        {"site_status": "gone"},
        {"imprint_present": None},
        {"imprint_location": "nowhere"},
        {"imprint_present": True, "imprint_location": "none"},
        {"topic": "Cats"},
        {"operator_type": ""},
        {"flags": ["bogus"]},
        {"main_address_index": 3},
        {"main_address_index": None},
        {"no_address_reason": "no_imprint"},
        {"annotator": "bob"},
    ],
)
def test_invalid_labels_rejected(change):
    assert schema.validate_label(good(**change)), change


def test_address_rules():
    assert schema.validate_label(good(addresses=[addr(role="boss")]))
    assert schema.validate_label(good(addresses=[addr(modality="smell")]))
    assert schema.validate_label(good(addresses=[addr(street="", postcode="", town="")]))
    assert schema.validate_label(good(addresses=[addr(evidence="")]))  # text needs evidence
    # image modality may have empty evidence
    assert schema.validate_label(good(addresses=[addr(modality="image", evidence="")])) == []
    # main address must not be the agency
    assert schema.validate_label(good(addresses=[addr(role="agency")]))
    two = good(addresses=[addr(role="agency"), addr()], main_address_index=1, flags=["multi_address"])
    assert schema.validate_label(two) == []


def test_negatives():
    dead = good(
        site_status="unreachable", imprint_present=False, imprint_location="none",
        addresses=[], main_address_index=None, no_address_reason="site_dead",
        operator_type=None, topic=None,
    )
    assert schema.validate_label(dead) == []
    assert schema.validate_label({**dead, "no_address_reason": "no_imprint"})
    no_imp = good(imprint_present=False, imprint_location="none", addresses=[],
                  main_address_index=None, no_address_reason="no_imprint")
    assert schema.validate_label(no_imp) == []
    assert schema.validate_label({**no_imp, "no_address_reason": "imprint_without_address"})
    no_addr = good(addresses=[], main_address_index=None, no_address_reason="imprint_without_address")
    assert schema.validate_label(no_addr) == []
    # only a host address listed: imprint present, no operator address
    only_host = good(addresses=[addr(role="host")], main_address_index=None,
                     no_address_reason="imprint_without_address")
    assert schema.validate_label(only_host) == []
    assert schema.validate_label({**only_host, "main_address_index": 0})


def test_text_warnings():
    lab = good()
    assert schema.text_warnings(lab, ["Impressum Hauptstr. 12a\n94032 Passau"]) == []
    assert schema.text_warnings(lab, ["Impressum nothing here"])
    assert schema.text_warnings(lab, [""]) == []  # no text: nothing to check


# ---- store ------------------------------------------------------------------
def make_store(tmp_path, label="L1"):
    d = tmp_path / "gold"
    (d / "example.de").mkdir(parents=True)
    (d / "example.de" / "imprint.txt").write_text("Impressum\nHauptstr. 12a\n94032 Passau\n", encoding="utf-8")
    (d / "example.de" / "landing.txt").write_text("Welcome", encoding="utf-8")
    (d / "example.de" / "landing.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (d / "example.de" / "meta.json").write_text(json.dumps({"captured_at": "2026-11-05T10:12:03Z"}))
    rows = [
        {"item": 1, "host": "example.de", "labeller": "L1", "role": "primary", "order": 2},
        {"item": 2, "host": "missing.de", "labeller": "L1", "role": "calibration", "order": 1},
        {"item": 3, "host": "other.de", "labeller": "L2", "role": "primary", "order": 1},
    ]
    (d / "assignment.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return Store(d, label)


def test_store_items_sorted_and_scoped(tmp_path):
    st = make_store(tmp_path)
    assert [i["host"] for i in st.items] == ["missing.de", "example.de"]  # by order, only L1
    assert not st.has_host("other.de")
    assert [x["phase"] for x in st.listing()] == ["calibration", "main"]


def test_missing_capture_is_graceful(tmp_path):
    st = make_store(tmp_path)
    cap = st.capture("missing.de")
    assert cap["exists"] is False and cap["capture_id"] is None and cap["texts"] == {}
    assert cap["images"] == {"landing": None, "imprint": None}


def test_save_load_roundtrip_last_wins(tmp_path):
    st = make_store(tmp_path)
    rec, errs, warns = st.save_label(good(), elapsed=100)
    assert errs == [] and warns == []
    assert rec["capture_id"] == "2026-11-05T10:12:03Z"
    assert rec["annotator"] == "L1" and rec["seconds_spent"] == 100 and rec["item"] == 1
    lab2 = good(topic="Event", comment="  changed ")
    rec2, errs, _ = st.save_label(lab2, elapsed=30)
    assert errs == [] and rec2["seconds_spent"] == 130  # accumulates over edits
    lines = st.labels_path.read_text().strip().splitlines()
    assert len(lines) == 2  # append-only
    loaded = Store(st.data_dir, "L1").load_labels()
    assert loaded["example.de"]["topic"] == "Event"
    assert loaded["example.de"]["comment"] == "changed"
    assert Store(st.data_dir, "L1").listing()[1]["done"] is True


def test_client_cannot_set_capture_id_or_other_labeller(tmp_path):
    st = make_store(tmp_path)
    rec, errs, _ = st.save_label(good(capture_id="fake", annotator="L1", seconds_spent=1), 5)
    assert rec["capture_id"] == "2026-11-05T10:12:03Z" and rec["seconds_spent"] == 5
    rec, errs, _ = st.save_label(good(host="other.de"), 5)  # belongs to L2
    assert rec is None and errs
    assert not (st.data_dir / "labels" / "L2.jsonl").exists()


def test_invalid_label_not_written(tmp_path):
    st = make_store(tmp_path)
    rec, errs, _ = st.save_label(good(topic="Cats"), 1)
    assert rec is None and errs and not st.labels_path.exists()


def test_torn_last_line_ignored(tmp_path):
    st = make_store(tmp_path)
    st.save_label(good(), 1)
    with open(st.labels_path, "a") as f:
        f.write('{"host": "example')
    assert "example.de" in st.load_labels()



def write_prefill(st, *hosts):
    with open(st.data_dir / "prefill.jsonl", "w") as f:
        for h in hosts:
            rec = {"host": h, "source": {"model": "m", "prompt": "p1"}, "label": {"site_status": "live", "addresses": [addr()]}}
            f.write(json.dumps(rec) + "\n")


def test_prefill_only_for_allowed_roles(tmp_path):
    st = make_store(tmp_path)
    write_prefill(st, "example.de", "missing.de")
    st = Store(st.data_dir, "L1")  # default: primary items only (D24)
    assert st.prefill("example.de")["source"] == "m/p1"
    assert st.prefill("missing.de") is None  # calibration item: from scratch
    assert st.prefill("other.de") is None  # not this labeller's item
    assert [x["prefill"] for x in st.listing()] == [False, True]
    assert Store(st.data_dir, "L1", prefill_roles=()).prefill("example.de") is None
    assert Store(st.data_dir, "L1", prefill_roles=("primary", "calibration")).prefill("missing.de")


def test_prefilled_from_recorded_by_server(tmp_path):
    st = make_store(tmp_path)
    rec, errs, _ = st.save_label(good(prefilled_from=True), 1)
    assert errs == [] and rec["prefilled_from"] is None  # no suggestion exists: the client cannot claim one
    write_prefill(st, "example.de")
    st = Store(st.data_dir, "L1")
    assert st.save_label(good(prefilled_from=True), 1)[0]["prefilled_from"] == "m/p1"
    assert st.save_label(good(), 1)[0]["prefilled_from"] is None


# ---- http -------------------------------------------------------------------
@pytest.fixture
def running(tmp_path):
    st = make_store(tmp_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(st))
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield st, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def http(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_http_flow(running):
    st, base = running
    code, body = http(base + "/")
    assert code == 200 and b"Imprint labelling" in body
    state = json.loads(http(base + "/api/state")[1])
    assert [i["host"] for i in state["items"]] == ["missing.de", "example.de"]
    assert "stratum" not in json.dumps(state)
    item = json.loads(http(base + "/api/item?host=example.de")[1])
    assert item["capture"]["texts"]["imprint"].startswith("Impressum")
    assert "meta" not in item["capture"] and item["label"] is None and item["prefill"] is None
    assert http(base + "/api/item?host=other.de")[0] == 404  # not assigned to L1
    assert http(base + "/img/example.de/landing.png")[0] == 200
    assert http(base + "/img/example.de/imprint.png")[0] == 404
    assert http(base + "/img/example.de/..%2Fmeta.json")[0] == 404
    code, body = http(base + "/api/label", {"label": good(topic="Cats"), "elapsed": 3})
    assert code == 400 and json.loads(body)["ok"] is False
    code, body = http(base + "/api/label", {"label": good(), "elapsed": 3})
    assert code == 200 and json.loads(body)["ok"] is True
    assert copy.deepcopy(st.load_labels())["example.de"]["seconds_spent"] == 3


def test_redirect_site_is_labelled_in_full():
    assert schema.validate_label(good(site_status="redirect_other_domain")) == []


def test_image_evidence_defaults_to_image():
    lab = schema.normalise_label(good(addresses=[addr(modality="image", evidence="")]))
    assert lab["addresses"][0]["evidence"] == "image"
