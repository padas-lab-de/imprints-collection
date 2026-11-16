import pytest

from ic.evaluation.geocoding import address_query, haversine_m, locate
from ic.evaluation.scoring import format_table, load_categories, score


class StubGeocoder:
    """Geocoder without network: maps query strings to coordinates."""

    def __init__(self, table):
        self.table = table

    def geocode(self, address):
        if not address:
            return None
        return self.table.get(address_query(address))


def addr(town="", plz="", street="", nr="", country="Deutschland"):
    return {
        "country": country,
        "town": town,
        "postalcode": plz,
        "streetname": street,
        "housenumber": nr,
    }


def gold_item(i, **kw):
    a = addr(**kw)
    return {
        "id": i,
        "url": "x",
        "output_theme": "Retail",
        "output_loc": {
            "Country": a["country"],
            "Town": a["town"],
            "PLZ": a["postalcode"],
            "Street": a["streetname"],
            "Streetnumber": a["housenumber"],
        },
    }


def pred(i, address):
    return {
        "id": i,
        "address": address,
        "topic": "Einzelhandel",
        "address_failed": address is None,
        "topic_failed": False,
    }


def test_address_query_like_pipeline():
    assert address_query(addr("Grimma", "04668", "Markt", "1")) == (
        "Deutschland Grimma 04668 Markt 1"
    )
    assert address_query(addr("Grimma")) == "Deutschland Grimma"


def test_haversine():
    assert haversine_m(12.0, 51.0, 12.0, 51.0) == 0.0
    # one degree latitude is about 111.2 km
    assert haversine_m(12.0, 51.0, 12.0, 52.0) == pytest.approx(111_195, rel=1e-3)


def test_locate_street_and_town_thresholds():
    gold = addr("Grimma", "04668", "Markt", "1")
    table = {
        address_query(gold): {"lon": 12.7289, "lat": 51.2366, "postcode": "04668"},
        # 100 m north
        "near": {"lon": 12.7289, "lat": 51.2375, "postcode": "04668"},
        # about 3 km north, different postcode
        "mid": {"lon": 12.7289, "lat": 51.2636, "postcode": "04669"},
        # about 20 km north
        "far": {"lon": 12.7289, "lat": 51.4166, "postcode": "04670"},
    }
    table[address_query(addr(town="near"))] = table["near"]
    table[address_query(addr(town="mid"))] = table["mid"]
    table[address_query(addr(town="far"))] = table["far"]
    geo = StubGeocoder(table)

    near = locate(gold, addr(town="near"), geo)
    assert near["street"] and near["town"]
    mid = locate(gold, addr(town="mid"), geo)
    assert not mid["street"] and mid["town"]
    far = locate(gold, addr(town="far"), geo)
    assert not far["street"] and not far["town"]
    # thresholds are parameters
    assert locate(gold, addr(town="mid"), geo, town_km=1.0)["town"] is False
    assert locate(gold, addr(town="near"), geo, street_m=50)["street"] is False


def test_same_postcode_counts_as_town_match_despite_distance():
    gold = addr("Berlin", "10115", "A", "1")
    other = addr("Berlin", "10115", "B", "2")
    geo = StubGeocoder(
        {
            address_query(gold): {"lon": 13.0, "lat": 52.0, "postcode": None},
            address_query(other): {"lon": 13.2, "lat": 52.2, "postcode": None},
        }
    )
    result = locate(gold, other, geo)
    assert result["town"] and not result["street"]


def test_failure_statuses():
    gold = addr("Grimma", "04668", "Markt", "1")
    geo = StubGeocoder({address_query(gold): {"lon": 1, "lat": 1, "postcode": None}})
    assert locate(addr("Nowhere"), gold, geo)["status"] == "gold_geocode_failed"
    assert locate(gold, None, geo)["status"] == "pred_missing"
    assert locate(gold, addr("Unknown"), geo)["status"] == "pred_geocode_failed"


def test_score_location_metric_counts_and_headline():
    categories = load_categories()
    g_ok = addr("Grimma /OT Kaditzsch", "04668", "Dorfstr.", "3")
    p_ok = addr("Grimma", "04668", "Dorfstr.", "3")  # same place, town string differs
    g_bad = addr("Leipzig", "04109", "Markt", "1")
    p_bad = addr("Dresden", "01067", "Markt", "1")  # wrong city
    g_none = addr("Nirgendwo", "99999", "X", "1")  # gold not geocodable
    geo = StubGeocoder(
        {
            address_query(g_ok): {"lon": 12.9, "lat": 51.2, "postcode": "04668"},
            address_query(p_ok): {"lon": 12.9, "lat": 51.2, "postcode": "04668"},
            address_query(g_bad): {"lon": 12.37, "lat": 51.34, "postcode": "04109"},
            address_query(p_bad): {"lon": 13.74, "lat": 51.05, "postcode": "01067"},
        }
    )
    gold = [
        gold_item(0, **dict(town=g_ok["town"], plz="04668", street="Dorfstr.", nr="3")),
        gold_item(1, **dict(town="Leipzig", plz="04109", street="Markt", nr="1")),
        gold_item(2, **dict(town="Nirgendwo", plz="99999", street="X", nr="1")),
    ]
    predictions = [pred(0, p_ok), pred(1, p_bad), pred(2, g_none)]
    metrics, errors = score(gold, predictions, categories, geocoder=geo)

    loc = metrics["address"]["location"]
    assert loc["gold_geocode_failed"] == 1
    assert loc["n_scored"] == 2
    assert loc["street_level"] == pytest.approx(0.5)
    assert loc["town_level"] == pytest.approx(0.5)
    assert metrics["address"]["correct"] == loc["street_level"]
    # the string metric still calls item 0 wrong, the location metric does not
    assert metrics["address"]["all_correct_exact"] == pytest.approx(1 / 3)  # item 2
    by_id = {e["id"]: e for e in errors}
    assert by_id[0]["address"]["town"]["gold"] == "Grimma /OT Kaditzsch"
    assert by_id[0]["location"]["street"] is True
    assert by_id[1]["location"]["street"] is False
    assert 2 not in by_id
    assert "ADDRESS CORRECT" in format_table(metrics)


def test_score_without_geocoder_has_no_location_block():
    categories = load_categories()
    gold = [gold_item(0, town="A", plz="1", street="S", nr="1")]
    metrics, _ = score(gold, [pred(0, addr("A", "1", "S", "1"))], categories)
    assert "location" not in metrics["address"]
    assert "correct" not in metrics["address"]
