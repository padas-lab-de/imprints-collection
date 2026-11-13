"""Unit tests for ic.eval.metrics on small hand-made cases (topics, addresses, efficiency)."""

import numpy as np
import pytest

from ic.eval._legacy import get_tree
from ic.eval.io import PredSet, hkey, unit_sample
from ic.eval.metrics import (
    ADDRESS_METRIC_DEFS,
    address_vectors,
    efficiency,
    evidence_ok,
    item_cost,
    location_match,
    pred_state,
    topic_metric_defs,
    topic_vectors,
    usage_vectors,
)
from ic.eval.reference import address_of

BATH = "bathroom-contractor"  # BPS > home-improvement-service > bathroom-contractor
PAINT = "painter"  # BPS > home-improvement-service > painter
HIS = "home-improvement-service"
HW = "hardware-store-and-building-supplies"  # retail > hardware...


def topic_set(rows, name="m/v"):
    return PredSet(
        name, "topic", "poi", "m", "v", {hkey(r["host"]): r for r in rows}, "", {}
    )


def refs_poi(d):
    return {
        hkey(h): {
            "poi": (
                None if m is False else {"main": m, "extra": ex, "online_only": False}
            )
        }
        for h, (m, ex) in d.items()
    }


def R(v, y, z):
    return v[y].sum() / v[z].sum()


def test_pred_state():
    assert pred_state(None) == "missing"
    assert pred_state({"error": "no_input"}) == "no_input"
    assert pred_state({"error": "timeout"}) == "failed"
    assert pred_state({"main": None, "error": None}) == "ok"


def test_topic_vectors_hand_case():
    tree = get_tree("poi3")
    hosts = ["a.de", "b.de", "c.de", "d.de", "e.de", "f.de"]
    refs = refs_poi(
        {
            "a.de": (BATH, []),
            "b.de": (BATH, []),
            "c.de": (BATH, [HW]),
            "d.de": (HIS, []),
            "e.de": (None, []),
            "f.de": (BATH, []),
        }
    )
    ps = topic_set(
        [
            {"host": "a.de", "main": BATH},  # exact
            {"host": "b.de", "main": HIS},  # correct but stops at level 2
            {"host": "c.de", "main": HW},  # wrong at level 1, but an accepted extra
            {
                "host": "d.de",
                "main": PAINT,
            },  # deeper than the reference, correct up to level 2
            {"host": "e.de", "main": BATH},  # reference "none" -> not scored
            {"host": "f.de", "main": None, "error": "boom"},  # failed
        ]
    )
    v = topic_vectors(unit_sample(hosts), refs, ps, tree)
    assert v["scored"].tolist() == [1, 1, 1, 1, 0, 1]
    assert v["ref_none"].tolist() == [0, 0, 0, 0, 1, 0]
    assert v["fail"].tolist() == [0, 0, 0, 0, 0, 1]
    # level 1: covered a,b,c,d; correct a,b,d
    assert R(v, "hit@1", "cov@1") == pytest.approx(3 / 4)
    assert R(v, "hit@1", "nref@1") == pytest.approx(3 / 5)
    # level 3: reference reaches L3 for a,b,c,f; only a's prediction reaches L3 there (HW is level 2)
    assert v["nref@3"].tolist() == [1, 1, 1, 0, 0, 1]
    assert v["cov@3"].tolist() == [1, 0, 0, 0, 0, 0]
    assert R(v, "hit@3", "cov@3") == 1.0
    assert R(v, "hit@2", "cov@2") == pytest.approx(3 / 4)  # a, b, d right; c wrong
    # truncated accuracy (E49 summary "acc"): d is correct at L3 truncation (both paths cut to length)
    assert v["acct@3"].tolist() == [1, 0, 0, 0, 0, 0]
    assert v["acct@2"].tolist() == [1, 1, 0, 1, 0, 0]
    # lenient: c is accepted through the extra
    assert v["len@1"].tolist() == [1, 1, 1, 1, 0, 0]
    assert v["nolabel"].tolist() == [0, 0, 0, 0, 0, 1]
    names = [n for n, _, _ in topic_metric_defs(3)]
    assert {
        "P@2",
        "acc@2",
        "cov@2",
        "acc_trunc@3",
        "lenient@1",
        "no_label",
        "failed",
    } <= set(names)


def test_no_input_miss_vs_skip():
    tree = get_tree("poi3")
    refs = refs_poi({"a.de": (BATH, []), "b.de": (BATH, [])})
    ps = topic_set(
        [
            {"host": "a.de", "main": BATH},
            {"host": "b.de", "main": None, "error": "no_input"},
        ]
    )
    smp = unit_sample(["a.de", "b.de"])
    miss = topic_vectors(smp, refs, ps, tree, no_input="miss")
    skip = topic_vectors(smp, refs, ps, tree, no_input="skip")
    assert (
        R(miss, "hit@1", "nref@1") == 0.5
        and miss["nolabel"][1] == 1
        and miss["fail"][1] == 0
    )
    assert R(skip, "hit@1", "nref@1") == 1.0 and skip["scored"][1] == 0


def test_location_match():
    a = {
        "street": "Brehmstraße",
        "number": "24",
        "postcode": "30173",
        "town": "Hannover",
    }
    b = {"street": "Brehmstr.", "number": "26", "postcode": "30173", "town": "Hannover"}
    assert location_match(a, b, {}, 100.0) == (True, "postcode+street")
    c = {
        "street": "Andere Str.",
        "number": "1",
        "postcode": "30173",
        "town": "Hannover",
    }
    assert location_match(a, c, {}, 100.0) == (False, "no_geocode")
    from ic.eval.io import addr_key

    geo = {
        addr_key(a): (52.3700, 9.7600),
        addr_key(c): (52.3705, 9.7600),
    }  # about 56 m apart
    assert location_match(a, c, geo, 100.0) == (True, "distance")
    geo[addr_key(c)] = (52.3800, 9.7600)  # about 1.1 km
    assert location_match(a, c, geo, 100.0)[0] is False


def test_evidence_check():
    pm = {"street": "Brehmstraße", "postcode": "30173"}
    assert evidence_ok(pm, "Ronny Schneider, Brehmstr. 24, 30173 Hannover")
    assert not evidence_ok(pm, "Ronny Schneider, Hauptstr. 1, 80331 München")


def _addr_label(street=None, postcode="30173", town="Hannover", reason=None):
    if street is None:
        return address_of(
            {"addresses": [], "main_address_index": None, "no_address_reason": reason}
        )
    return address_of(
        {
            "addresses": [
                {
                    "role": "operator",
                    "street": street,
                    "number": "1",
                    "postcode": postcode,
                    "town": town,
                    "country": "",
                }
            ],
            "main_address_index": 0,
        }
    )


def test_address_vectors_hand_case():
    hosts = ["a.de", "b.de", "c.de", "d.de", "e.de"]
    refs = {
        "a.de": {"address": _addr_label("Brehmstraße")},  # pred matches
        "b.de": {"address": _addr_label("Brehmstraße")},  # pred wrong street
        "c.de": {
            "address": _addr_label(None, reason="no_imprint")
        },  # pred none, same reason
        "d.de": {
            "address": _addr_label(None, reason="imprint_without_address")
        },  # pred invents an address
        "e.de": {"address": _addr_label("Hauptstraße")},  # pred finds nothing
    }

    def row(h, street=None, reason=None):
        if street is None:
            return {
                "host": h,
                "addresses": [],
                "main_index": None,
                "no_address_reason": reason,
                "error": None,
            }
        return {
            "host": h,
            "addresses": [
                {
                    "role": "operator",
                    "street": street,
                    "number": "1",
                    "postcode": "30173",
                    "town": "Hannover",
                    "country": "",
                }
            ],
            "main_index": 0,
            "error": None,
        }

    rows = [
        row("a.de", "Brehmstr."),
        row("b.de", "Andere Str."),
        row("c.de", None, "no_imprint"),
        row("d.de", "Brehmstraße"),
        row("e.de", None, "no_imprint"),
    ]
    ps = PredSet(
        "m/v", "address", "address", "m", "v", {r["host"]: r for r in rows}, "", {}
    )
    texts = {
        "a.de": "Brehmstr. 1, 30173 Hannover",
        "b.de": "nothing here",
        "d.de": "Brehmstraße 1 30173",
    }
    v = address_vectors(unit_sample(hosts), refs, ps, {}, texts)
    assert v["loc100_all"].tolist() == [1, 0, 1, 0, 0]
    assert R(v, "loc100", "ref_main") == pytest.approx(1 / 3)
    assert R(v, "loc100", "pred_main") == pytest.approx(1 / 3)  # addr_P
    assert v["false_addr"].tolist() == [0, 0, 0, 1, 0]
    assert v["missed"].tolist() == [0, 0, 0, 0, 1]
    assert R(v, "na_tp", "na_pred") == pytest.approx(1 / 2)  # noaddr_P
    assert v["reason_ok"][2] == 1
    assert v["halluc"].tolist() == [0, 1, 0, 0, 0] and v["ev_n"].sum() == 3
    assert v["geo_missing"].sum() == 3  # no geocodes given
    names = {n for n, _, _ in ADDRESS_METRIC_DEFS}
    assert {"loc100_all", "addr_P", "field_F1", "noaddr_R", "hallucination"} <= names


def test_efficiency_and_cost():
    u = {"prompt_tokens": 1000, "cached_prompt_tokens": 400, "completion_tokens": 50}
    c = item_cost(
        u, {"usd_per_mtok_in": 1.0, "usd_per_mtok_cached": 0.1, "usd_per_mtok_out": 4.0}
    )
    assert c["C"] == 600 + 500
    assert c["usd"] == pytest.approx((600 * 1.0 + 400 * 0.1 + 50 * 4.0) / 1e6)
    rows = [
        {"host": "a.de", "main": BATH, "usage": dict(u, calls=1), "latency_s": 2.0},
        {
            "host": "b.de",
            "main": None,
            "error": "timeout",
            "usage": dict(u, calls=2),
            "latency_s": 4.0,
        },
        {"host": "c.de", "main": None, "error": "no_input", "usage": {}},
    ]
    ps = PredSet(
        "m/v",
        "topic",
        "poi",
        "m",
        "v",
        {r["host"]: r for r in rows},
        "",
        {"usd_per_mtok_in": 1.0, "gpu_hours_per_mhost": 3.0},
    )
    smp = unit_sample(["a.de", "b.de", "c.de", "d.de"])
    uv = usage_vectors(smp, ps)
    assert uv["attempted"].tolist() == [
        1,
        1,
        0,
        1,
    ]  # no_input not attempted; missing counts as failed
    e = efficiency(smp.design(), uv, ps.meta)
    assert e["failed_rate_items"] == pytest.approx(2 / 3)
    assert e["failed_rate"] == pytest.approx(
        2 / 4
    )  # per call: (0 + 1 + 1) / (1 + 2 + 1)
    assert e["C_per_1M"] == pytest.approx(1100 * 2 / 3 * 1e6)
    assert e["gpu_hours_per_1M"] == 3.0
    assert e["s_median"] in (2.0, 4.0)
    assert np.isnan(uv["s"][3])
