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

### E4-fetch-yield-baseline
- Small alphabetical sample (1,000): 437 imprints / 819 reachable = 53.4%; not representative.
- Random 20k sample (seed 20261023, 29 min): reachable 16,217; imprint found 9,606 = 59.2% of reachable (paper 58.2%); host_not_found 17.9%.
  - Imprint/reachable by TLD: .de 79.7% (7,106/8,917), .at 86.2%, .ch 78.0%, .eu 65.4%, .net 36.8%, .com 30.4%, .org 20.1%, other 13.6%.
  - Biggest yield target: 1,811 reachable .de hosts without imprint.
- Link expansion signal: the 20k fetch discovered 19,980 unique external hosts, 5,360 (27%) not in the 6.56M seed list; of these 602 .de, 1,985 .com.

### E5-imprint-not-found-causes (200 of the 1,811 .de hosts; report docs/experiments/E5-imprint-not-found-causes.md)
- Parked/placeholder 20.5%, JS-only/empty 17.5%, missed by fetch rules 17.0%, genuinely no imprint 11.5%, redirect/spam 7.0%, link target failed 6.0%, imprint on landing page 5.0%, /impressum exists but unlinked 4.5%, other 11%.
- Static-rule fixes would recover 42/200 = 21% (CI 15.9-27.2%), about 380 of the 1,811: .de found rate 79.7% -> ~84.0%. Top fixes: key links by full URL (5.5%), keep pages with empty main-content extraction (5%), probe /impressum (4.5%).
- E6-fetch-rule-fixes implements F1-F6 + F9 and re-runs the 20k (running).

### Findings on the original pipeline
- stats.py counts all-empty LLM addresses as extracted: the paper's 3,225,347 "extracted address" is a count of responses.
- Qwen3-Next (paper model) is no longer served on innkube.

## Next steps
See "Next" of the latest brief and decisions.md "In flight".
