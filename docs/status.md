# Status — German Imprints Collection, journal extension

Updated 2026-10-23. Decisions and in-flight work: [decisions.md](decisions.md).

## Goal
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
- Small alphabetical sample (1,000): 437 imprints / 819 reachable = 53.4% (paper 58.2%). Random 20k sample running.

### Findings on the original pipeline
- stats.py counts all-empty LLM addresses as extracted: the paper's 3,225,347 "extracted address" is a count of responses.
- Qwen3-Next (paper model) is no longer served on innkube.

## Next steps
See "Next" of the latest brief and decisions.md "In flight".
