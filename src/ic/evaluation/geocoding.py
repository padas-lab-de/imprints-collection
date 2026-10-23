import json
import logging
import math
import os
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests

STREET_THRESHOLD_M = 250.0
TOWN_THRESHOLD_KM = 5.0
ADDRESS_ORDER = ["country", "town", "postalcode", "streetname", "housenumber"]


def address_query(address: dict) -> str:
    """
    Builds the Photon query string exactly like the pipeline (cli/geocode.py):
    "country town postalcode streetname housenumber", stripped, double blanks collapsed.
    """
    parts = [address.get(k) for k in ADDRESS_ORDER]
    return " ".join(str(v) for v in parts if v is not None).strip().replace("  ", " ")


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Great-circle distance in metres.
    """
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(a))


class PhotonGeocoder:
    """
    Geocodes address dicts (lower-case keys) with Photon and caches the results in a
    JSONL file (query -> first feature or null). Errors (network, non-200) are not
    cached. geocode() returns {"lon", "lat", "postcode", "name"} or None.
    """

    def __init__(self, endpoint: str, cache_path: str | None = None, retries: int = 3):
        self.endpoint = endpoint
        self.cache_path = cache_path
        self.retries = retries
        self.cache: dict[str, dict | None] = {}
        self.errors = 0
        self._lock = threading.Lock()
        if cache_path and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="UTF-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        self.cache[record["query"]] = record["result"]

    def _request(self, query: str) -> tuple[bool, dict | None]:
        url = f"{self.endpoint}?q={urllib.parse.quote(query)}"
        for _ in range(self.retries):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    features = response.json()["features"]
                    if not features:
                        return True, None
                    feature = features[0]
                    lon, lat = feature["geometry"]["coordinates"]
                    props = feature.get("properties", {})
                    return True, {
                        "lon": lon,
                        "lat": lat,
                        "postcode": props.get("postcode"),
                        "name": props.get("name"),
                        "type": props.get("type"),
                    }
            except Exception as e:  # network error, bad JSON
                logging.debug(f"Geocoding error for {query}: {e}")
            time.sleep(1)
        return False, None

    def geocode(self, address: dict | None) -> dict | None:
        query = address_query(address) if address else ""
        if not query:
            return None
        with self._lock:
            if query in self.cache:
                return self.cache[query]
        ok, result = self._request(query)
        if not ok:
            self.errors += 1
            return None
        with self._lock:
            self.cache[query] = result
            if self.cache_path:
                os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)
                with open(self.cache_path, "a", encoding="UTF-8") as f:
                    f.write(
                        json.dumps({"query": query, "result": result}, ensure_ascii=False)
                        + "\n"
                    )
        return result

    def prefetch(self, addresses: list[dict | None], workers: int = 8) -> None:
        """
        Fills the cache for all addresses in parallel.
        """
        with ThreadPoolExecutor(max_workers=workers) as executor:
            list(executor.map(self.geocode, addresses))


def locate(
    gold_address: dict,
    pred_address: dict | None,
    geocoder,
    street_m: float = STREET_THRESHOLD_M,
    town_km: float = TOWN_THRESHOLD_KM,
) -> dict:
    """
    Compares the geocoded gold and predicted address.

    status "gold_geocode_failed": gold address not geocodable, item is excluded.
    status "pred_missing" / "pred_geocode_failed": counted as no match.
    Otherwise status "ok" with distance_m and the matches:
      street: distance <= street_m
      town:   same postcode (address field, else Photon postcode) OR distance <= town_km
    """
    gold_geo = geocoder.geocode(gold_address)
    if gold_geo is None:
        return {"status": "gold_geocode_failed", "street": False, "town": False}
    if not pred_address:
        return {"status": "pred_missing", "street": False, "town": False}
    pred_geo = geocoder.geocode(pred_address)
    if pred_geo is None:
        return {"status": "pred_geocode_failed", "street": False, "town": False}

    distance = haversine_m(gold_geo["lon"], gold_geo["lat"], pred_geo["lon"], pred_geo["lat"])
    gold_plz = str(gold_address.get("postalcode") or gold_geo.get("postcode") or "").strip()
    pred_plz = str(pred_address.get("postalcode") or pred_geo.get("postcode") or "").strip()
    same_plz = gold_plz != "" and gold_plz == pred_plz
    return {
        "status": "ok",
        "distance_m": distance,
        "street": distance <= street_m,
        "town": same_plz or distance <= town_km * 1000,
        "gold_type": gold_geo.get("type"),
        "pred_type": pred_geo.get("type"),
    }
