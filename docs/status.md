# Status — German Imprints Collection, journal extension

Updated 2026-10-23. Decisions and in-flight work: [decisions.md](decisions.md).

## Goal
Target: Scientific Data, Data Descriptor (D10-journal-venue).
Journal extension of the WebSci Companion '26 demo paper (arXiv 2609.03971), which reported no evaluation numbers: (1) evaluation of address extraction, topic classification and geocoding with a model comparison and error analysis; (2) a fresh, larger snapshot via better fetch yield and link expansion.

## Results so far

### E2-gold-baseline-innkube (1,000 gold items, prompt german/simple, temperature 0)
| Model | Address all fields, exact | Address all fields, normalized | Topic acc. | Topic macro-F1 | Failed calls |
|---|---|---|---|---|---|
| Qwen3.8-27B (reasoning off) | 0.904 | 0.953 | 0.736 | 0.595 | 0 |
| Gemma4-31B | 0.885 | 0.945 | 0.752 | 0.605 | 0 |

Source: results/<model>/german/simple/eval/metrics.json.
- Address errors (Qwen, 47 items): mostly town granularity (gold keeps district suffixes like "Grimma /OT Kaditzsch", model writes "Grimma"), single-letter spelling deviations, and a few wrong-address choices on multi-address imprints (ids 279, 678).
- Topic: largest confusions all go into Business and Professional Services (Community 32, Arts 30, Retail 23). Health and Medicine recall ~0.5 at precision ~1.0.
- Caveat: topic is evaluated on the imprint text (gold has no homepage text), while production classifies the homepage.

### E10-link-expansion-pilot (merged; report docs/experiments/E10-link-expansion-pilot.md)
- 11,969 new hosts (not in seeds) linked from the 20k seeds: imprint found 1,231/9,182 reachable = 13.4%; 83% of them with DACH address.
- .de/.at/.ch new hosts: 413 DACH imprints per 1,000 fetched (seeds 432); other TLDs 34 per 1,000. Full round adds roughly +2-4% (wide range). Card D16-link-expansion-scope.

### E9-fetch-precision (merged; report docs/experiments/E9-fetch-precision.md) — current fetcher
- Same 20k hosts: 10,246/16,129 = 63.5% of reachable (E4 59.2%, E6 64.2%); .de 83.6% (E4 79.7%).
- Precision of gains vs E4: 49/50 (CI ~89-100%; E6 was 40/50 on a different sample). Recovers 37 of 43 E5 rule misses.
- Not yet judged: ~140 hosts lost vs E6 (likely mostly rejected false positives; 30-host sample would settle it).

### E7-eval-homepage-location (old 1,000-item gold set; report docs/experiments/E7-eval-homepage-location.md)
- Homepages re-fetched for 890/1,000 gold hosts (84 unreachable, 23 empty, 3 filtered; 90 redirect to another host).
- Topic, same 890 items: homepage input is ~2.5 points below imprint input (Qwen acc 0.710 vs 0.734, macro-F1 0.566 vs 0.594; Gemma 0.722 vs 0.748, 0.576 vs 0.601). Likely partly because old gold topics were labelled from imprint text and sites changed since; the new gold set (D14 A) fixes the label source.
- Address by geocoded location (D12): street level <=250 m Qwen 0.982, Gemma 0.972; town level 0.992 / 0.986 (vs exact 0.904 / 0.885). 22/31 Qwen town errors resolve. Caveat: Photon is fuzzy, so street level is lenient (wrong house number can still match); 7 gold addresses do not geocode.

### E4-fetch-yield-baseline
- Small alphabetical sample (1,000): 437 imprints / 819 reachable = 53.4%; not representative.
- Random 20k sample (seed 20261023, 29 min): reachable 16,217; imprint found 9,606 = 59.2% of reachable (paper 58.2%); host_not_found 17.9%.
  - Imprint/reachable by TLD: .de 79.7% (7,106/8,917), .at 86.2%, .ch 78.0%, .eu 65.4%, .net 36.8%, .com 30.4%, .org 20.1%, other 13.6%.
  - Biggest yield target: 1,811 reachable .de hosts without imprint.
- Link expansion signal: the 20k fetch discovered 19,980 unique external hosts, 5,360 (27%) not in the 6.56M seed list; of these 602 .de, 1,985 .com.

### E5-imprint-not-found-causes (200 of the 1,811 .de hosts; report docs/experiments/E5-imprint-not-found-causes.md)
- Parked/placeholder 20.5%, JS-only/empty 17.5%, missed by fetch rules 17.0%, genuinely no imprint 11.5%, redirect/spam 7.0%, link target failed 6.0%, imprint on landing page 5.0%, /impressum exists but unlinked 4.5%, other 11%.
- Static-rule fixes would recover 42/200 = 21% (CI 15.9-27.2%), about 380 of the 1,811: .de found rate 79.7% -> ~84.0%. Top fixes: key links by full URL (5.5%), keep pages with empty main-content extraction (5%), probe /impressum (4.5%).

### E6-fetch-rule-fixes (merged 8e35e07; report docs/experiments/E6-fetch-rule-fixes.md)
- Same 20k hosts: imprint found 10,327/16,093 = 64.2% of reachable (E4 59.2%); .de 7,469/8,888 = 84.0% (E4 79.7%).
- 873 gained, 152 lost (56 removed old false positives: landing-page shells, PDFs decoded as "None"; 96 crawl noise). Recovers 39 of the 42 E5 rule misses.
- Precision of gains 40/50 = 80% (CI 67-89%); 5 of 10 errors from the English keyword "imprint" (product pages). Changed URLs 17/20. Superseded by E9.
- stats.py/merge.py now count an address only if a field is non-empty.

### Findings on the original pipeline
- stats.py counts all-empty LLM addresses as extracted: the paper's 3,225,347 "extracted address" is a count of responses.
- Qwen3-Next (paper model) is no longer served on innkube.

## Next steps
See "Next" of the latest brief and decisions.md "In flight".
