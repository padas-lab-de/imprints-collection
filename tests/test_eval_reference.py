"""Reference builder (protocol 2.2) and agreement statistics."""

import pytest

from ic.eval.agreement import agreement, cohen_kappa, krippendorff_alpha_nominal
from ic.eval.reference import build_reference

BATH, PAINT, HIS, BPS = (
    "bathroom-contractor",
    "painter",
    "home-improvement-service",
    "business-and-professional-services",
)
HW = "hardware-store-and-building-supplies"


def lab(
    host, poi=None, wz=None, status="live", street="Brehmstraße", pc="30173", extra=()
):
    adds = (
        []
        if street is None
        else [
            {
                "role": "operator",
                "street": street,
                "number": "1",
                "postcode": pc,
                "town": "Hannover",
                "country": "",
            }
        ]
    )
    return {
        "host": host,
        "site_status": status,
        "imprint_present": street is not None,
        "addresses": adds,
        "main_address_index": 0 if adds else None,
        "no_address_reason": None if adds else "no_imprint",
        "topic_labels": {
            "poi": {"main": poi, "extra": list(extra)} if poi is not None else None,
            "wz": {"main": wz, "extra": []} if wz is not None else None,
        },
        "flags": [],
    }


def two(h, a, b):
    labels = {"L1": {h: a}, "L2": {h: b}}
    asg = {h: {"L1": "primary", "L2": "second"}}
    return labels, asg


def test_single_and_agree():
    labels, asg = two(
        "a.de", lab("a.de", BATH, "47.5"), lab("a.de", BATH, "47.5", street="Brehmstr.")
    )
    labels["L1"]["b.de"] = lab("b.de", HW)
    refs, stats = build_reference(["a.de", "b.de"], labels, asg)
    assert refs["a.de"]["how"] == {
        "status": "agree",
        "address": "agree",
        "poi": "agree",
        "wz": "agree",
    }
    assert refs["a.de"]["double"] and refs["a.de"]["poi"]["main"] == BATH
    assert refs["b.de"]["how"]["poi"] == "single" and not refs["b.de"]["double"]
    assert stats["poi"] == {"agree": 1, "single": 1}


def test_depth_rule_lcp_vs_deeper():
    labels, asg = two("a.de", lab("a.de", BATH), lab("a.de", HIS))
    r_lcp, _ = build_reference(["a.de"], labels, asg)
    assert (
        r_lcp["a.de"]["poi"]["main"] == HIS
        and r_lcp["a.de"]["how"]["poi"] == "depth_lcp"
    )
    r_deep, _ = build_reference(["a.de"], labels, asg, depth_rule="deeper")
    assert r_deep["a.de"]["poi"]["main"] == BATH


def test_unresolved_topic_rules():
    labels, asg = two("a.de", lab("a.de", BATH), lab("a.de", PAINT))
    r, _ = build_reference(["a.de"], labels, asg)
    assert (
        r["a.de"]["poi"]["main"] == HIS and r["a.de"]["how"]["poi"] == "unresolved_lcp"
    )
    r, _ = build_reference(["a.de"], labels, asg, unresolved_topic="primary")
    assert r["a.de"]["poi"]["main"] == BATH
    r, _ = build_reference(["a.de"], labels, asg, unresolved_topic="drop")
    assert r["a.de"]["poi"] is None
    # no common prefix -> lcp is empty (no reference topic main)
    labels, asg = two("b.de", lab("b.de", BATH), lab("b.de", HW))
    r, _ = build_reference(["b.de"], labels, asg)
    assert r["b.de"]["poi"]["main"] is None


def test_adjudication_scope():
    labels, asg = two("a.de", lab("a.de", BATH), lab("a.de", PAINT))
    adj = {"a.de": dict(lab("a.de", PAINT), parts=["poi"])}
    r, _ = build_reference(["a.de"], labels, asg, adj)
    assert (
        r["a.de"]["poi"]["main"] == PAINT and r["a.de"]["how"]["poi"] == "adjudicated"
    )
    assert r["a.de"]["how"]["address"] == "agree"  # parts limits the record to poi
    # an adjudication on an agreeing item is ignored by default, used with scope "double"
    labels, asg = two("b.de", lab("b.de", BATH), lab("b.de", BATH))
    adj = {"b.de": dict(lab("b.de", PAINT), parts=["poi"])}
    assert build_reference(["b.de"], labels, asg, adj)[0]["b.de"]["poi"]["main"] == BATH
    assert (
        build_reference(["b.de"], labels, asg, adj, adjudication_scope="double")[0][
            "b.de"
        ]["poi"]["main"]
        == PAINT
    )
    # single-labelled items only with scope "all"
    labels = {"L1": {"c.de": lab("c.de", BATH)}}
    adj = {"c.de": dict(lab("c.de", PAINT), parts=["poi"])}
    assert build_reference(["c.de"], labels, {}, adj)[0]["c.de"]["poi"]["main"] == BATH
    assert (
        build_reference(["c.de"], labels, {}, adj, adjudication_scope="all")[0]["c.de"][
            "poi"
        ]["main"]
        == PAINT
    )


def test_address_disagreement_primary_or_drop():
    labels, asg = two(
        "a.de",
        lab("a.de", BATH, street="Brehmstraße"),
        lab("a.de", BATH, street="Hauptstraße"),
    )
    r, _ = build_reference(["a.de"], labels, asg)
    assert r["a.de"]["how"]["address"] == "unresolved_primary"
    assert r["a.de"]["address"]["addresses"][0]["street"].startswith("Brehm")
    r, _ = build_reference(["a.de"], labels, asg, unresolved_other="drop")
    assert r["a.de"]["address"] is None


def test_not_live_drops_topics():
    labels, asg = two(
        "a.de", lab("a.de", BATH, status="dead"), lab("a.de", BATH, status="dead")
    )
    r, _ = build_reference(["a.de"], labels, asg)
    assert (
        r["a.de"]["live"] is False
        and r["a.de"]["poi"] is None
        and r["a.de"]["how"]["poi"] == "not_live"
    )


def test_calibration_majority_and_consensus():
    h = "a.de"
    labels = {
        "L1": {h: lab(h, BATH)},
        "L2": {h: lab(h, BATH)},
        "L3": {h: lab(h, PAINT)},
    }
    asg = {h: {"L1": "calibration", "L2": "calibration", "L3": "calibration"}}
    r, _ = build_reference([h], labels, asg)
    assert (
        r[h]["calibration"]
        and r[h]["poi"]["main"] == BATH
        and r[h]["how"]["poi"] == "majority"
    )
    labels["L2"][h] = lab(h, HW)
    r, _ = build_reference([h], labels, asg)
    assert (
        r[h]["how"]["poi"] == "level_majority" and r[h]["poi"]["main"] == HIS
    )  # 2 of 3 to L2
    r, _ = build_reference([h], labels, asg, {h: dict(lab(h, HW), parts=["poi"])})
    assert r[h]["poi"]["main"] == HW and r[h]["how"]["poi"] == "consensus"


def test_use_first_second():
    labels, asg = two("a.de", lab("a.de", BATH), lab("a.de", PAINT))
    assert (
        build_reference(["a.de"], labels, asg, use="first")[0]["a.de"]["poi"]["main"]
        == BATH
    )
    assert (
        build_reference(["a.de"], labels, asg, use="second")[0]["a.de"]["poi"]["main"]
        == PAINT
    )


def test_kappa_alpha():
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "a", "b", "b"]) == 1.0
    assert cohen_kappa(["a", "b", "a", "b"], ["a", "a", "b", "b"]) == pytest.approx(0.0)
    assert krippendorff_alpha_nominal([["a", "a"], ["b", "b"], ["a", "a"]]) == 1.0
    assert krippendorff_alpha_nominal([["a", "b"], ["b", "a"]]) < 0


def test_agreement_report():
    labels = {
        "L1": {"a.de": lab("a.de", BATH), "b.de": lab("b.de", HW)},
        "L2": {"a.de": lab("a.de", HIS), "b.de": lab("b.de", HW, street="Hauptstraße")},
    }
    asg = {
        "a.de": {"L1": "primary", "L2": "second"},
        "b.de": {"L1": "primary", "L2": "second"},
    }
    a = agreement(["a.de", "b.de"], labels, asg)
    assert a["items"] == 2 and a["pairs"] == 2
    assert a["site_status"]["agree"] == 1.0
    assert a["address"]["location_match"] == 0.5
    assert a["topics"]["poi"]["prefix"][1]["agree"] == 1.0
    assert a["topics"]["poi"]["prefix"][2]["agree"] == 1.0
    assert a["topics"]["poi"]["prefix"][3] == {"agree": 0.0, "n": 1}
    assert a["topics"]["poi"]["full_path"] == 0.5
