"""Unit tests for src/ic/gold/sampling.py (E12 gold-sample design)."""

import random

import pytest

from ic.gold.sampling import (
    IMAGE_ONLY,
    NEG_DEAD,
    NEG_NO_IMPRINT,
    NO_COVERAGE,
    draw_sample,
    marginal_counts,
    memberships,
    newcombe_diff,
    priority_stratum,
    rarity_order,
    wilson,
)


def rec(host, **kw):
    base = {
        "host": host, "site_status": "live", "imprint_location": "separate_page", "age_bin": "<2010",
        "tech": "wordpress", "tech_family": "cms_wordpress", "spa_framework": None, "server_lang": None,
        "rendering_need": "static_ok", "model_operator_type": "corporate", "tld": "de", "n_addresses": 1,
        "model_n_addresses": 1, "po_box": False, "multi_address": False, "obfuscation": [], "model_topic": "Retail",
    }
    base.update(kw)
    return base


def test_wilson_known_values():
    lo, hi = wilson(694, 1000)
    assert round(lo * 100, 1) == 66.5 and round(hi * 100, 1) == 72.2  # E8 'live'
    assert wilson(0, 0) == (0.0, 1.0)
    lo, hi = wilson(0, 50)
    assert lo == 0.0 and 0.06 < hi < 0.08


def test_newcombe_contains_zero_for_equal_and_excludes_for_far():
    d, lo, hi = newcombe_diff(50, 100, 50, 100)
    assert d == 0 and lo < 0 < hi
    d, lo, hi = newcombe_diff(90, 100, 10, 100)
    assert lo > 0.6 and hi < 0.9


def test_memberships_negatives_and_coverage():
    assert memberships(rec("a", site_status="unreachable")) == [NEG_DEAD]
    assert memberships(rec("a", imprint_location="none")) == [NEG_NO_IMPRINT]
    ms = memberships(rec("x.at", tld="at", model_operator_type="public_body", po_box=True, model_topic="Event",
                         rendering_need="js_required", imprint_location="other_domain", age_bin=">=2023"))
    for s in ("tld:at", "op:public_body", "hard:po_box", "topic:Event", "render:js_required",
              "loc:other_domain", "age:>=2023", "tech:wordpress"):
        assert s in ms
    ms = memberships(rec("b", n_addresses=0, model_n_addresses=0))
    assert "hard:imprint_without_address" in ms
    ms = memberships(rec("b", n_addresses=0, model_n_addresses=0), image_only_confirmed={"b"})
    assert IMAGE_ONLY in ms and "hard:imprint_without_address" not in ms
    assert "tech:blogger" in memberships(rec("c", tech="blogger", tech_family="blog_platform"))
    assert "hard:multi_address" in memberships(rec("d", model_n_addresses=2))


def test_priority_is_rarest_with_image_only_first():
    lists = [["a", "b"], ["a"], ["a", "c"], ["a", "b"], [IMAGE_ONLY, "a"], [IMAGE_ONLY, "a"], [IMAGE_ONLY], [NEG_DEAD]]
    order = rarity_order(lists)
    assert order[0] == IMAGE_ONLY and order[1] == "c" and order[-1] == "a" and NEG_DEAD not in order
    assert priority_stratum(["a", "b"], order) == "b"
    assert priority_stratum([IMAGE_ONLY, "c"], order) == IMAGE_ONLY
    assert priority_stratum([NEG_DEAD], order) == NEG_DEAD
    assert priority_stratum([], order) == NO_COVERAGE


def synthetic(n=3000, seed=1):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        u = rng.random()
        if u < 0.3:
            out.append(rec(f"h{i}", site_status="unreachable"))
            continue
        if u < 0.45:
            out.append(rec(f"h{i}", imprint_location="none"))
            continue
        out.append(rec(
            f"h{i}.{'at' if rng.random() < 0.03 else 'de'}",
            tld="at" if rng.random() < 0.03 else "de",
            po_box=rng.random() < 0.015,
            rendering_need="js_required" if rng.random() < 0.012 else "static_ok",
            model_operator_type=rng.choice(["corporate"] * 8 + ["private_person"]),
            model_topic="Nightlife Spot" if rng.random() < 0.002 else "Retail",
        ))
    return out


def test_draw_sample_sizes_targets_and_weights():
    recs = synthetic()
    items, info = draw_sample(recs, core_range=(180, 220), n_total=330, frame_size=6_000_000, seed=7,
                              target_range=(10, 20), caps={IMAGE_ONLY: 5})
    assert len(items) == 330
    assert sum(it["core"] for it in items) == info["n_core"]
    assert 180 <= info["n_core"] <= 220
    assert len({it["host"] for it in items}) == len(items)
    marg = marginal_counts(items)
    for s in info["order"]:
        exhausted = info["m"].get(s, 0) == info["M"].get(s, 0)
        assert marg.get(s, 0) >= info["target"] or exhausted, s
    # oversample adds no negatives
    for it in items:
        if it["priority_stratum"].startswith("neg:") or it["priority_stratum"] == NO_COVERAGE:
            assert it["core"]
    # phase-2 weights add up to the screening sample size
    tot = sum(1 / it["pi_phase2"] for it in items)
    covered = sum(v for k, v in info["M"].items() if info["m"].get(k))
    assert tot == pytest.approx(covered)
    # overall weights add up to the frame share of covered strata
    assert sum(it["design_weight"] for it in items) == pytest.approx(covered * 6_000_000 / len(recs))
    for it in items:
        assert it["inclusion_probability"] == pytest.approx(len(recs) / 6_000_000 * it["stratum_selected"] / it["stratum_screened"])


def test_draw_sample_deterministic():
    recs = synthetic(1500, seed=3)
    a, _ = draw_sample(recs, (90, 110), 160, 10**6, seed=11, target_range=(5, 10))
    b, _ = draw_sample(recs, (90, 110), 160, 10**6, seed=11, target_range=(5, 10))
    assert [x["host"] for x in a] == [x["host"] for x in b]


def test_core_is_uniform_prefix():
    recs = synthetic(1000, seed=5)
    items, _ = draw_sample(recs, (100, 100), 100, 10**6, seed=2, target_range=(0, 0))
    assert len(items) == 100 and all(it["core"] for it in items)
