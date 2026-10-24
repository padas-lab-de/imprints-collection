# Status — German Imprints Collection, journal extension

Updated 2026-10-24. Decisions and in-flight work: [decisions.md](decisions.md).

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

### E12-gold-screening (merged; design docs/gold_set_design.md v0.2, tables results/E12/screening_prevalence.md, results/E12/gold_sample_quotas.md)
- 10,000 random seed hosts screened (frame 6,557,719): live 71.4%, HTTP error 12.6%, unreachable 7.5%, cross-domain redirect 6.9%; imprint found 57.7% of live; address only in an image 15 hand-confirmed (0.36% of imprints).
- Gold sample datasets/E12/gold_sample.jsonl: 1,000 items = 700 random core + 300 oversample, target 30 per stratum (seed 20261025); 799 live, 219 no-imprint and 201 not-live negatives (core only); Horvitz-Thompson weights 656-16,582. Short strata (all screened hosts used): Nightlife 3, Blogger 8, Landmarks 13, image-only 15.
- Doubts: Strato /24 answered 503 for 578 hosts (gold capture must run from another IP); no-imprint share on live .de/.at/.ch 16.3% vs 12.1% in E8 (unexplained).

### E14-link-expansion-depth (merged; report docs/experiments/E14-link-expansion-depth.md)
- DACH-address imprints per 1,000 fetched: seeds 432, round 1 85, round 2 20, round 3 8; on .de/.at/.ch hosts 603, 413, 181, 121. Frontier grows per round (0.59, 1.27, 2.07, 3.11 new hosts per fetched host). ~40% of round 2-3 imprints duplicate earlier operators.
- Full run from 6.56M seeds: depth 1 all TLDs 3.5-3.9M fetches / 302-332k DACH imprints; + depth 2-3 on .de/.at/.ch only 3.9-4.6M / 363-439k; depth 3 all TLDs 11.4-19.1M / 407-512k. Card D19-link-expansion-depth.

### E13-snapshot-dry-run (merged; report docs/experiments/E13-snapshot-dry-run.md)
- Per-provider limit in fetch.py (group = resolved /24 or /48; 4 concurrent, 0.25 s gap, 10 s pause after 429/503, one retry), crash resume per batch; 115 tests.
- 100k random seeds in 283 min (353 hosts/min; steady ~490/min), shared VM. Found/reachable 62.5%, .de 85.0% (E9 63.5%, 83.6%). Strato: 24 of 6,433 hosts blocked (E8: nearly all). 429/503 failures mostly Cloudflare bot challenges.
- 6.56M seeds at the measured rate: ~310 h, ~33 GB (66 GB free). Memory grows ~0.5 GB/h, so run in ranges of ~10 batches. Card D18-snapshot-provider-cap.

### E8-gold-strata-pilot (merged; design docs/gold_set_design.md, tables results/E8/pilot_prevalence.md)
- 1,000 random seed hosts: live 69.4%, HTTP error 13.2% (inflated: Strato hosts answered 503 to the crawl VM), unreachable 8.2%, cross-domain redirect 7.7%.
- Of live: WordPress 31.6%, site builder 10.7%, custom PHP 7.8%, static 7.8%, SPA 3.3%, Blogger 0.3%; JS required 1.2%; domain age <2010 40%, >=2023 11.5%; no imprint 39% (.de/.at/.ch 12%, other TLDs 75%).
- Of imprints: multiple addresses 30%, obfuscation 33%, address only in an image 0.5% (2/422), PDF 0.
- Design: ~1,300 items = 600 random core + ~700 oversampled rare strata, marginal quotas, Horvitz-Thompson weights (card D17-gold-set-size). Detectors spot-checked by hand (tech 20/20, multi-address 18/20, LLM operator type 12/13).

### E11-external-host-discovery (merged; report docs/experiments/E11-external-host-discovery.md)
- The original fetcher stored landing-page links keyed by URL path, so external links (path "/") overwrote each other; fixed in 5d5afa2. Current count (34,771 unique external hosts on 20k seeds vs 19,980) is correct; on 77 re-fetched hosts the fix alone explains the whole difference. E10 estimate stands.

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
