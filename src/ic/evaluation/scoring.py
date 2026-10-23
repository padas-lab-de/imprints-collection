import json
import re
import unicodedata
from collections import Counter

from ic.evaluation.geocoding import STREET_THRESHOLD_M, TOWN_THRESHOLD_KM, locate

ADDRESS_FIELDS = ["country", "town", "postalcode", "streetname", "housenumber"]
GOLD_ADDRESS_KEYS = {
    "country": "Country",
    "town": "Town",
    "postalcode": "PLZ",
    "streetname": "Street",
    "housenumber": "Streetnumber",
}

# German top-level category -> English gold class (decision D5-topic-eval-granularity)
TOP_LEVEL_DE_TO_EN = {
    "Kunst und Unterhaltung": "Arts and Entertainment",
    "Geschäfts- und professionelle Dienstleistungen": "Business and Professional Services",
    "Gemeinschaft und Regierung": "Community and Government",
    "Essen und Trinken": "Dining and Drinking",
    "Ereignis": "Event",
    "Gesundheit und Medizin": "Health and Medicine",
    "Sehenswürdigkeiten und im Freien": "Landmarks and Outdoors",
    "Nachtleben-Spot": "Nightlife Spot",
    "Einzelhandel": "Retail",
    "Sport und Freizeit": "Sports and Recreation",
    "Reisen und Transport": "Travel and Transportation",
}
TOP_LEVEL_EN_TO_DE = {en: de for de, en in TOP_LEVEL_DE_TO_EN.items()}
NONE_LABEL = "<none>"

COUNTRY_ALIASES = {
    "deutschland": "de",
    "germany": "de",
    "de": "de",
    "deu": "de",
    "bundesrepublikdeutschland": "de",
    "federalrepublicofgermany": "de",
}


# ---------------------------------------------------------------- normalization


def normalize(value, field: str | None = None) -> str:
    """
    Normalizes an address value for lenient comparison: Unicode NFKC, casefold,
    "strasse"/"straße"/"str." unified to "str", whitespace and punctuation removed.
    For the country field, "Deutschland"/"Germany"/"DE" are unified.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()  # casefold: ß -> ss
    text = text.replace("strasse", "str")
    text = re.sub(r"[\W_]+", "", text)  # drops whitespace and punctuation
    if field == "country":
        text = COUNTRY_ALIASES.get(text, text)
    return text


# ---------------------------------------------------------------- topic hierarchy


def load_categories(path: str = "topics/categories.jsonl") -> list[dict]:
    """
    Loads the category records ({"name", "parent"}) from a JSONL file.
    """
    with open(path, "r", encoding="UTF-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_top_level_index(categories: list[dict]) -> dict[str, list[str]]:
    """
    Maps every category name to the German top-level ancestor(s) reached by walking
    the parent chain. A few names occur twice with different parents (Karaoke-Bar,
    Rettungsdienst) and may therefore reach several top-levels.
    """
    parents: dict[str, list] = {}
    for category in categories:
        parents.setdefault(category["name"], []).append(category["parent"])

    top_levels = [c["name"] for c in categories if c["parent"] is None]
    assert set(top_levels) == set(TOP_LEVEL_DE_TO_EN), (
        "TOP_LEVEL_DE_TO_EN must cover exactly the top-level categories, "
        f"difference: {set(top_levels) ^ set(TOP_LEVEL_DE_TO_EN)}"
    )

    def walk(name: str, seen: frozenset) -> set[str]:
        result = set()
        for parent in parents[name]:
            if parent is None:
                result.add(name)
            elif parent not in seen:
                result |= walk(parent, seen | {name})
        return result

    index = {}
    for name in parents:
        tops = walk(name, frozenset())
        assert tops, f"Category without top-level ancestor: {name}"
        index[name] = [t for t in top_levels if t in tops]
    return index


def english_classes(category: str | None, index: dict[str, list[str]]) -> list[str]:
    """
    English gold class(es) of a predicted German category; empty if unknown.
    """
    if category not in index:
        return []
    return [TOP_LEVEL_DE_TO_EN[t] for t in index[category]]


# ---------------------------------------------------------------- metrics


def prf1(tp: int, fp: int, fn: int) -> dict:
    """
    Precision, recall, F1 and support from raw counts.
    """
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}


def classification_report(y_true: list[str], y_pred: list[str]) -> dict:
    """
    Accuracy, macro-F1 (over labels that occur in y_true or y_pred, excluding
    NONE_LABEL), per-class P/R/F1 and a confusion matrix (rows: gold, columns: pred).
    """
    labels = sorted((set(y_true) | set(y_pred)) - {NONE_LABEL})
    confusion = {t: Counter() for t in sorted(set(y_true))}
    for t, p in zip(y_true, y_pred):
        confusion[t][p] += 1

    per_class = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        per_class[label] = prf1(tp, fp, fn)

    n = len(y_true)
    return {
        "n": n,
        "accuracy": sum(t == p for t, p in zip(y_true, y_pred)) / n if n else 0.0,
        "macro_f1": (
            sum(v["f1"] for v in per_class.values()) / len(per_class)
            if per_class
            else 0.0
        ),
        "per_class": per_class,
        "confusion_matrix": {t: dict(c) for t, c in confusion.items()},
    }


# ---------------------------------------------------------------- scoring


def score(
    gold: list[dict],
    predictions: list[dict],
    categories: list[dict],
    geocoder=None,
    street_m: float = STREET_THRESHOLD_M,
    town_km: float = TOWN_THRESHOLD_KM,
) -> tuple[dict, list[dict]]:
    """
    Scores predictions against the gold standard.

    Args:
        gold: Gold items (id, output_loc, output_theme, ...).
        predictions: Prediction records (id, address dict with lower-case keys or None,
            topic str or None, address_failed, topic_failed). If an id occurs more
            than once, the last record wins. Gold items without prediction count as
            failed.
        categories: Records of categories.jsonl ({"name", "parent"}).
        geocoder: Optional object with geocode(address dict) -> dict | None (see
            ic.evaluation.geocoding). If given, the geocoding-based location match
            is computed (street level: distance <= street_m; town level: same
            postcode or distance <= town_km) and is the headline address metric.

    Returns:
        (metrics, errors): Metrics dict and a list of per-item error records.
    """
    index = build_top_level_index(categories)
    pred_by_id = {p["id"]: p for p in predictions}
    n = len(gold)

    exact = Counter()
    normalized = Counter()
    all_exact = all_normalized = 0
    address_failed = topic_failed = 0
    y_true, y_pred = [], []
    errors = []
    loc_counts = Counter()

    for item in gold:
        pred = pred_by_id.get(item["id"])
        error = {"id": item["id"], "url": item.get("url")}

        # Address
        address = pred.get("address") if pred else None
        if not pred or pred.get("address_failed") or not isinstance(address, dict):
            address = None
            address_failed += 1
        item_exact = item_norm = True
        wrong = {}
        for field in ADDRESS_FIELDS:
            gold_value = item["output_loc"][GOLD_ADDRESS_KEYS[field]]
            pred_value = address.get(field) if address else None
            ok_exact = pred_value is not None and str(pred_value) == str(gold_value)
            ok_norm = pred_value is not None and normalize(
                pred_value, field
            ) == normalize(gold_value, field)
            exact[field] += ok_exact
            normalized[field] += ok_norm
            item_exact &= ok_exact
            item_norm &= ok_norm
            if not ok_exact:
                wrong[field] = {
                    "gold": gold_value,
                    "pred": pred_value,
                    "normalized_match": ok_norm,
                }
        all_exact += item_exact
        all_normalized += item_norm

        location = None
        if geocoder is not None:
            gold_address = {
                f: item["output_loc"][GOLD_ADDRESS_KEYS[f]] for f in ADDRESS_FIELDS
            }
            location = locate(gold_address, address, geocoder, street_m, town_km)
            loc_counts[location["status"]] += 1
            if location["status"] != "gold_geocode_failed":
                loc_counts["street"] += location["street"]
                loc_counts["town"] += location["town"]
                if location["status"] == "ok":
                    fine = {"house", "street"}
                    resolved = (
                        location.get("gold_type") in fine
                        and location.get("pred_type") in fine
                    )
                    loc_counts["both_street_resolved"] += resolved
                    loc_counts["street_match_coarse"] += (
                        location["street"] and not resolved
                    )
        location_miss = (
            location is not None
            and location["status"] != "gold_geocode_failed"
            and not location["street"]
        )
        if wrong or location_miss:
            error["address"] = wrong
            error["address_failed"] = address is None
            if location is not None:
                error["location"] = location

        # Topic
        category = pred.get("topic") if pred else None
        if not pred or pred.get("topic_failed") or category is None:
            topic_failed += 1
        candidates = english_classes(category, index)
        gold_class = item["output_theme"]
        if gold_class in candidates:
            pred_class = gold_class  # ambiguous duplicate names: credit if any matches
        elif candidates:
            pred_class = candidates[0]
        else:
            pred_class = NONE_LABEL
        y_true.append(gold_class)
        y_pred.append(pred_class)
        if pred_class != gold_class:
            error["topic"] = {
                "gold": gold_class,
                "pred_category": category,
                "pred_class": pred_class,
            }
        if len(error) > 2:
            errors.append(error)

    def rate(count):
        return count / n if n else 0.0

    metrics = {
        "n": n,
        "failed_calls": {"address": address_failed, "topic": topic_failed},
        "address": {
            "exact": {f: rate(exact[f]) for f in ADDRESS_FIELDS},
            "normalized": {f: rate(normalized[f]) for f in ADDRESS_FIELDS},
            "all_correct_exact": rate(all_exact),
            "all_correct_normalized": rate(all_normalized),
        },
        "topic": classification_report(y_true, y_pred),
    }
    if geocoder is not None:
        scored = n - loc_counts["gold_geocode_failed"]
        metrics["address"]["location"] = {
            "street_threshold_m": street_m,
            "town_threshold_km": town_km,
            "n_scored": scored,
            "gold_geocode_failed": loc_counts["gold_geocode_failed"],
            "pred_missing": loc_counts["pred_missing"],
            "pred_geocode_failed": loc_counts["pred_geocode_failed"],
            "street_level": loc_counts["street"] / scored if scored else 0.0,
            "town_level": loc_counts["town"] / scored if scored else 0.0,
            # street matches where Photon resolved gold or prediction only to a
            # coarser object (town, district, ...): both then sit near a centroid
            "street_match_with_coarse_geocode": loc_counts["street_match_coarse"],
            "street_level_count": loc_counts["street"],
            "town_level_count": loc_counts["town"],
        }
        # headline "address correct"
        metrics["address"]["correct"] = metrics["address"]["location"]["street_level"]
    return metrics, errors


def format_table(metrics: dict) -> str:
    """
    Renders metrics as a compact text table.
    """
    a = metrics["address"]
    failed = metrics["failed_calls"]
    lines = [
        f"Items: {metrics['n']}   failed calls: address={failed['address']}"
        f" topic={failed['topic']}",
        "",
    ]
    loc = a.get("location")
    if loc:
        lines += [
            f"ADDRESS CORRECT (street level, <= {loc['street_threshold_m']:g} m): "
            f"{loc['street_level']:.3f}  ({loc['street_level_count']}/{loc['n_scored']})",
            f"Town level (same postcode or <= {loc['town_threshold_km']:g} km): "
            f"{loc['town_level']:.3f}  ({loc['town_level_count']}/{loc['n_scored']})",
            f"Excluded, gold not geocodable: {loc['gold_geocode_failed']}   "
            f"prediction missing: {loc['pred_missing']}   "
            f"prediction not geocodable: {loc['pred_geocode_failed']}",
            f"Street matches with a coarse (non house/street) geocode: "
            f"{loc['street_match_with_coarse_geocode']}",
            "",
            "Secondary, field-level string comparison:",
        ]
    lines.append(f"{'Address field':<14}{'exact':>8}{'normalized':>12}")
    for f in ADDRESS_FIELDS:
        lines.append(f"{f:<14}{a['exact'][f]:>8.3f}{a['normalized'][f]:>12.3f}")
    lines.append(
        f"{'all fields':<14}{a['all_correct_exact']:>8.3f}"
        f"{a['all_correct_normalized']:>12.3f}"
    )
    t = metrics["topic"]
    lines += [
        "",
        f"Topic accuracy: {t['accuracy']:.3f}   macro-F1: {t['macro_f1']:.3f}",
        f"{'Class':<38}{'P':>7}{'R':>7}{'F1':>7}{'n':>6}",
    ]
    for label, v in t["per_class"].items():
        lines.append(
            f"{label:<38}{v['precision']:>7.3f}{v['recall']:>7.3f}"
            f"{v['f1']:>7.3f}{v['support']:>6}"
        )
    return "\n".join(lines)
