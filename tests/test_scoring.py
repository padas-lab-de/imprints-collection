import json

import pytest

from ic.evaluation.scoring import (
    ADDRESS_FIELDS,
    GOLD_ADDRESS_KEYS,
    TOP_LEVEL_DE_TO_EN,
    TOP_LEVEL_EN_TO_DE,
    build_top_level_index,
    classification_report,
    load_categories,
    normalize,
    score,
)

GOLD_PATH = "evaluation/gold_standard_data.jsonl"


@pytest.fixture(scope="module")
def categories():
    return load_categories()


@pytest.fixture(scope="module")
def gold():
    with open(GOLD_PATH, encoding="UTF-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_normalize_street_variants():
    variants = ["Hauptstraße", "Hauptstrasse", "Hauptstr.", "HAUPTSTR", "Haupt-Str."]
    assert len({normalize(v, "streetname") for v in variants}) == 1


def test_normalize_whitespace_punctuation_unicode():
    assert normalize(" 12 a ", "housenumber") == normalize("12a", "housenumber")
    assert normalize("Ｂｅｒｌｉｎ", "town") == normalize("berlin", "town")  # NFKC
    assert normalize("Frankfurt (Oder)", "town") == normalize("frankfurtoder", "town")


def test_normalize_country():
    for value in ["Deutschland", "Germany", "DE", "de", " Deutschland "]:
        assert normalize(value, "country") == normalize("Germany", "country")
    assert normalize("Österreich", "country") != normalize("Germany", "country")
    assert normalize(None) == ""


def test_top_level_mapping_is_complete(categories):
    tops = [c["name"] for c in categories if c["parent"] is None]
    assert len(tops) == 11 and set(tops) == set(TOP_LEVEL_DE_TO_EN)


def test_every_category_maps_to_english_class(categories, gold):
    index = build_top_level_index(categories)
    assert len(index) == len({c["name"] for c in categories})
    gold_classes = {item["output_theme"] for item in gold}
    assert gold_classes <= set(TOP_LEVEL_EN_TO_DE)
    for name, tops in index.items():
        assert tops
        assert all(TOP_LEVEL_DE_TO_EN[t] in TOP_LEVEL_EN_TO_DE for t in tops)
    assert index["Rathaus"] == ["Gemeinschaft und Regierung"]
    assert index["Attraktion"] == ["Kunst und Unterhaltung"]


def test_macro_f1_hand_made():
    y_true = ["a", "a", "b", "b", "c"]
    y_pred = ["a", "b", "b", "b", "a"]
    report = classification_report(y_true, y_pred)
    # a: tp1 fp1 fn1 -> F1=0.5; b: tp2 fp1 fn0 -> P=2/3 R=1 F1=0.8; c: F1=0
    assert report["accuracy"] == pytest.approx(3 / 5)
    assert report["per_class"]["a"]["f1"] == pytest.approx(0.5)
    assert report["per_class"]["b"]["f1"] == pytest.approx(0.8)
    assert report["per_class"]["c"]["f1"] == 0.0
    assert report["macro_f1"] == pytest.approx((0.5 + 0.8 + 0.0) / 3)
    assert report["confusion_matrix"]["a"] == {"a": 1, "b": 1}


def oracle_predictions(gold):
    return [
        {
            "id": item["id"],
            "address": {
                f: item["output_loc"][GOLD_ADDRESS_KEYS[f]] for f in ADDRESS_FIELDS
            },
            "topic": TOP_LEVEL_EN_TO_DE[item["output_theme"]],
            "address_failed": False,
            "topic_failed": False,
        }
        for item in gold
    ]


def test_oracle_scores_100_percent(gold, categories):
    metrics, errors = score(gold, oracle_predictions(gold), categories)
    assert metrics["n"] == 1000
    assert metrics["failed_calls"] == {"address": 0, "topic": 0}
    for field in ADDRESS_FIELDS:
        assert metrics["address"]["exact"][field] == 1.0
        assert metrics["address"]["normalized"][field] == 1.0
    assert metrics["address"]["all_correct_exact"] == 1.0
    assert metrics["address"]["all_correct_normalized"] == 1.0
    assert metrics["topic"]["accuracy"] == 1.0
    assert metrics["topic"]["macro_f1"] == 1.0
    assert errors == []


def test_missing_and_failed_predictions_count_as_wrong(gold, categories):
    gold = gold[:4]
    predictions = oracle_predictions(gold)[:3]  # item 3 has no prediction
    predictions[0] = {
        "id": gold[0]["id"],
        "address": None,
        "topic": None,
        "address_failed": True,
        "topic_failed": True,
    }
    metrics, errors = score(gold, predictions, categories)
    assert metrics["failed_calls"] == {"address": 2, "topic": 2}
    assert metrics["address"]["all_correct_exact"] == 0.5
    assert metrics["topic"]["accuracy"] == 0.5
    assert {e["id"] for e in errors} == {gold[0]["id"], gold[3]["id"]}


def test_normalized_beats_exact(gold, categories):
    item = dict(gold[0])
    item["output_loc"] = dict(
        item["output_loc"], Street="Hauptstraße", Country="Deutschland"
    )
    pred = oracle_predictions([item])[0]
    pred["address"].update(streetname="Hauptstr.", country="Germany")
    metrics, errors = score([item], [pred], categories)
    assert metrics["address"]["exact"]["streetname"] == 0.0
    assert metrics["address"]["normalized"]["streetname"] == 1.0
    assert metrics["address"]["normalized"]["country"] == 1.0
    assert metrics["address"]["all_correct_normalized"] == 1.0
    assert errors[0]["address"]["streetname"]["normalized_match"] is True
