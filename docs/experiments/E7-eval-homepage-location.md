# E7-eval-homepage-location (2026-10-23)

Implements D11 A (topic on homepage) and D12 A (geocoding-based location match). No paid APIs, no new LLM calls for the location part. Model: prompt german/simple, innkube, temperature 0, reasoning off for Qwen (as E2).

## 1. Homepages of the 1,000 gold hosts
Script `scripts/gold_homepages.py` (imports `try_fetch` and `parse_html` from `ic.cli.fetch`, so UA, timeouts, redirect handling and resiliparse main-content extraction are identical to production; no link discovery; https then http; 16 workers; ~65 s). Run on the crawling-subnet VM at 2026-10-23 17:08 UTC.

```
scripts/gold_homepages.py evaluation/gold_standard_data.jsonl /home/dinzinger/GitHub/imprints-collection/datasets/E7/gold_homepages.jsonl 16
```
Output (outside git): `/home/dinzinger/GitHub/imprints-collection/datasets/E7/gold_homepages.jsonl` (id, host, url, status, title, description, main_content, fetched_at).

| Status | n |
|---|---|
| ok (non-empty main content) | 890 |
| host_not_found (DNS, connect/read timeout, or no HTTP 200 after redirects on both schemes; `try_fetch` does not distinguish) | 84 |
| empty_content (fetched, HTML parsed, main content empty: JS-only/parked) | 23 |
| filtered (host or final URL on the production filter list) | 3 |

Of the 890: median main content 2,351 characters, 57 shorter than 200 characters, 13 without title, 348 without description (meta description is missing on 39%), 90 of all 1,000 responses redirected to a different host (domain changes). Gold labels are older than these homepages, so some sites changed owner or content, which affects the topic comparison below (homepage today vs imprint text at label time).

## 2. Topic: homepage vs imprint input (same 890 items)
`ic evaluate MODEL german simple --topic-input homepage --homepages <path>`. Prompt built with `build_topic_message(url, title, description, main_content)` from the homepage fields like `process_llm.py` (final homepage URL, `prepare_content` truncation at 30,000 tokens). The 110 gold items without homepage are excluded from both columns. Imprint column: the E2 predictions rescored on the same 890 items (the imprint prompt has no description, as in E2). 0 failed calls. Sources: `results/<MODEL>/german/simple/eval/metrics_homepage.json`, `predictions_topic_homepage.jsonl`.

| Model | Input | Accuracy | Macro-F1 |
|---|---|---|---|
| Qwen3.8-27B | homepage | 0.710 | 0.566 |
| Qwen3.8-27B | imprint | 0.734 | 0.594 |
| Gemma4-31B | homepage | 0.722 | 0.576 |
| Gemma4-31B | imprint | 0.748 | 0.601 |

Per-class F1 (homepage / imprint):

| Class | n | Qwen3.8-27B | Gemma4-31B |
|---|---|---|---|
| Arts and Entertainment | 74 | 0.526 / 0.507 | 0.483 / 0.507 |
| Business and Professional Services | 288 | 0.784 / 0.798 | 0.787 / 0.809 |
| Community and Government | 181 | 0.712 / 0.736 | 0.740 / 0.755 |
| Dining and Drinking | 23 | 0.585 / 0.634 | 0.579 / 0.600 |
| Event | 10 | 0.457 / 0.640 | 0.593 / 0.696 |
| Health and Medicine | 64 | 0.705 / 0.680 | 0.700 / 0.653 |
| Landmarks and Outdoors | 13 | 0.240 / 0.231 | 0.182 / 0.200 |
| Nightlife Spot | 3 | 0.000 / 0.000 | 0.000 / 0.000 |
| Retail | 117 | 0.712 / 0.765 | 0.744 / 0.795 |
| Sports and Recreation | 58 | 0.723 / 0.758 | 0.737 / 0.792 |
| Travel and Transportation | 59 | 0.781 / 0.785 | 0.789 / 0.804 |

Homepage input scores about 2.4 to 2.6 points lower accuracy and 2.5 to 2.8 points lower macro-F1 than imprint input on the same items. Health and Medicine improves on the homepage (Qwen +0.025, Gemma +0.047). Classes with n <= 23 (Event, Dining, Landmarks, Nightlife) are noisy. No confidence intervals computed.

## 3. Address: geocoding-based location match
Photon at `GEOCODING_API_ENDPOINT`; query string built exactly like `cli/geocode.py` ("country town postalcode streetname housenumber"), first feature used. Results cached in `results/<MODEL>/german/simple/eval/geocode_cache.jsonl` (query -> lon, lat, postcode, name, type). Thresholds are parameters: `--street-threshold-m` (default 250), `--town-threshold-km` (default 5). Street level: distance <= 250 m. Town level: same postcode (address field, else Photon postcode) or distance <= 5 km. Gold addresses that do not geocode are excluded and counted; a missing or non-geocodable prediction would count as no match (0 occurred). `metrics.json` has `address.correct` (= street-level, headline) and `address.location`; `format_table` leads with it and lists exact/normalized as secondary. Existing E2 predictions rescored with `--score-only`.

| Model | Street level (<=250 m) | Town level | Exact, all fields | Normalized, all fields | Scored / gold-geocode failures |
|---|---|---|---|---|---|
| Qwen3.8-27B | 0.982 (975/993) | 0.992 (985/993) | 0.904 | 0.953 | 993 / 7 |
| Gemma4-31B | 0.972 (965/993) | 0.986 (979/993) | 0.885 | 0.945 | 993 / 7 |

Items remain on exact/normalized only for comparison with E2; the exact/normalized numbers are unchanged.

### The 31 Qwen town errors of E2
The 31 = items whose town differs after normalization (town normalized accuracy 0.969). With the location metric:
- 22 become street-level and town-level matches (Qwen); Gemma has the same 31-item set (identical town errors count) with 17 resolved.
- 9 stay errors for Qwen: 2 gold addresses do not geocode (ids 78 "Liepe" vs "Rankwitz, OT-Liepe", 917 "Ainring-Feldkirchen"), and 7 are genuinely a different place (ids 77, 279, 389, 678, 828, 836, 854: multi-address imprints or wrong-address choice; 12 to 512 km apart).

### Street-level misses (Qwen, 18)
Different place or wrong address of a multi-address imprint: 41, 77, 279, 389, 678, 828, 836, 854 (>8 km). Same town, different street or house, 250 m to 4.1 km: 107 (262 m, house number only), 411, 429, 483, 525, 697, 797, 867, 906, 914 (mostly street-name spelling deviations such as "Wildscheuerweg" vs "Wilscheuerweg", where Photon maps to different objects).

### Gold geocoding failures (7; feed D9)
Queries with no Photon result: `Ketsch 68775 Hockenheimerstr. 34a`, `Liepe 17406 Grüssowerstraße 16`, `Traunstein 83278 Jamsgasse 77a`, `Mörlenbach 69509 Bonsweihererstraße 46`, `Freistaat Sachsen 09033 Gotthardstrasse 10` (town field contains the state), `Ainring-Feldkirchen 83404 Saalfeld 11`, `St. Blasien 79837 Todtmooserstr. 48`. Mostly spelling variants of street names and non-standard town fields.

## Caveats
- Photon is fuzzy: a wrong house number or a typo in the street name is still within 250 m, so street-level is more lenient than "all fields exact" (0.982 vs 0.904 for Qwen). 8 street-level matches per model involve a coarse geocode (gold or prediction resolved only to a town/district, not a house or street), i.e. both sit near a centroid. The street-level threshold is therefore not equal to "street and house number correct"; keep exact/normalized as the strict secondary.
- Gold and predictions are geocoded with the same Photon instance and the same query construction, so a systematic Photon bias cancels but is not measured against a ground truth (D9).
- Homepages were fetched today; gold labels (imprint text, theme) are older. Differences between homepage and imprint input mix the input effect with site drift; the 110 unreachable hosts are excluded from both columns.
- `try_fetch` returns only HTTP 200 responses, so 4xx/5xx, timeouts and DNS failures are one category (host_not_found).

## Files
- `src/ic/evaluation/geocoding.py` (new: `PhotonGeocoder`, `locate`, `haversine_m`), `src/ic/evaluation/scoring.py` (`score(..., geocoder, street_m, town_km)`, `format_table`), `src/ic/cli/evaluate.py` (`--topic-input`, `--homepages`, `--geocode/--no-geocode`, `--street-threshold-m`, `--town-threshold-km`), `scripts/gold_homepages.py`, `tests/test_location.py` (stubbed geocoder, no network).
- Tests: 35 passed.
