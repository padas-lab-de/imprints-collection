# E52 runs: predictions and efficiency on the 1,869 gold items (no reference)

E52 steps 1, 3 and 4 (2026-11-13). This file has no accuracy numbers. The gold labels do not exist yet, so every
agreement number below compares candidates with each other, **not with a reference**.

- Items: datasets/E52/gold_inputs.jsonl (1,869 items, gold_sample.jsonl order, sha256 `ca0b3850...`), made by
  `scripts/E52/build_inputs.py` from the same-day `ic fetch` text of datasets/E53/gold (read only). 53 items have no
  imprint text (1 of them has no ic_fetch.jsonl). Address makes no call for them; the topic runs use the landing page.
- Endpoint: innkube only (no paid API, no FAITH, cost $0). `/v1/models` on 2026-11-13 served gemma4-31b-it,
  qwen38-27b, qwen-agentworld-35b-a3b, octen-embedding-8b, qwen3-reranker-4b, soofi-s-isar-preview.
  **qwen3-next-80b-a3b-instruct is not served: not run** (so it has no reasoning level). qwen-agentworld-35b-a3b is
  served and is a candidate.
- "(screen)" = phase-1 screen models (gemma4-31b-it, qwen38-27b).
- Runs (configs of results/E50/final_config.md): address = mode main, json_schema, reasoning none, imprint input,
  6000 chars; POI k30 = retrieve k30 with reasoning gemma short / qwen low / agentworld short; POI flat = the same
  with strategy flat (variant); WZ k30 = retrieve k30, reasoning none, 1500 chars per field.
- Load: 6 workers per run, at most 2 runs at the same time (`scripts/E52/runs.sh`), full window 13:56-17:25 UTC.
  No HTTP 429/503 or other HTTP errors (`scripts/E52/run.py` logs every HTTP error; no log file was made).
- Failure columns: malformed = no JSON object, or a topic answer with no valid id and no KEINE (e.g. an id outside
  the candidate list); truncated = cut at max_tokens with no JSON left; cut = all replies at max_tokens, also those
  that still parsed. Failed items keep their line in the prediction file (temperature 0 and the request cache make a
  re-run give the same answer).
- s/item = wall time of one call with 6 workers in parallel. The POI p95 includes the first items, which wait for
  the one-time node embedding.
- Scorer freeze (step 1): `tests/test_e52_scorer_freeze.py`. scripts/E49/score.py reproduces every cell of
  results/E49/poi3c/summary.md on the E49 references. scripts/E50/compare.py gives the same P@1-3 and acc@1, but
  its acc@L (L2, L3) counts only hosts whose reference reaches L; summary.md acc counts a prediction that equals a
  shorter reference as a hit. The two acc@L2/acc@L3 are therefore different metrics (up to 0.021 apart at L2, about
  0.3 at L3 on the E49 data). The test pins both definitions; choose one before scoring E52.

## Full runs (1,869 items)

Stage full: 1869 items; 53 without imprint text (1 of them without an ic_fetch.jsonl): address makes no call for them (prediction no_imprint), topics run on the landing page.

| candidate | run | items | done | no call | failed (empty/malformed/truncated/timeout/other) | per 1,000 | cut | abstain | tok in mean / p95 | tok out mean / p95 | s/item median / p95 | window UTC | HTTP errors |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen38-27b (screen) | address | 1869 | 1869 | 53 | 0 (0/0/0/0/0) | 0.0 | 0 | - | 896 / 1645 | 67 / 75 | 1.37 / 2.08 | 11-13T13:56-14:04 | 0 |
| qwen38-27b (screen) | POI k30 | 1869 | 1869 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 83 | 2448 / 3721 | 494 / 895 | 9.66 / 19.04 | 11-13T14:04-14:57 | 0 |
| qwen38-27b (screen) | POI flat | 1869 | 1869 | 0 | 6 (0/6/0/0/0) | 3.2 | 0 | 70 | 23978 / 25234 | 531 / 1033 | 18.94 / 41.57 | 11-13T14:57-16:43 | 0 |
| qwen38-27b (screen) | WZ k30 | 1869 | 1869 | 0 | 1 (0/1/0/0/0) | 0.5 | 0 | 103 | 3059 / 3740 | 25 / 25 | 5.05 / 6.19 | 11-13T16:43-17:09 | 0 |
| gemma4-31b-it (screen) | address | 1869 | 1869 | 53 | 0 (0/0/0/0/0) | 0.0 | 0 | - | 946 / 1730 | 52 / 58 | 1.12 / 2.17 | 11-13T13:56-14:03 | 0 |
| gemma4-31b-it (screen) | POI k30 | 1869 | 1869 | 0 | 2 (0/2/0/0/0) | 1.1 | 0 | 45 | 2510 / 3831 | 62 / 82 | 3.18 / 4.80 | 11-13T14:03-14:20 | 0 |
| gemma4-31b-it (screen) | POI flat | 1869 | 1869 | 0 | 1 (0/1/0/0/0) | 0.5 | 0 | 25 | 24184 / 25457 | 70 / 87 | 13.50 / 20.76 | 11-13T14:20-15:35 | 0 |
| gemma4-31b-it (screen) | WZ k30 | 1869 | 1869 | 0 | 1 (0/1/0/0/0) | 0.5 | 0 | 26 | 3143 / 3846 | 29 / 29 | 5.25 / 8.89 | 11-13T15:35-16:04 | 0 |
| qwen-agentworld-35b-a3b | address | 1869 | 1869 | 53 | 0 (0/0/0/0/0) | 0.0 | 0 | - | 896 / 1645 | 49 / 56 | 0.77 / 0.93 | 11-13T16:04-16:08 | 0 |
| qwen-agentworld-35b-a3b | POI k30 | 1869 | 1869 | 0 | 1 (0/1/0/0/0) | 0.5 | 1 | 33 | 2439 / 3712 | 80 / 104 | 2.56 / 3.34 | 11-13T16:29-16:42 | 0 |
| qwen-agentworld-35b-a3b | POI flat | 1869 | 1869 | 0 | 6 (0/4/2/0/0) | 3.2 | 12 | 42 | 23969 / 25225 | 81 / 107 | 3.05 / 4.44 | 11-13T17:09-17:25 | 0 |
| qwen-agentworld-35b-a3b | WZ k30 | 1869 | 1869 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 20 | 3059 / 3740 | 27 / 63 | 4.01 / 5.00 | 11-13T16:08-16:29 | 0 |

Prediction files (sha256):

| candidate | run | file | sha256 | calls | cached calls |
|---|---|---|---|---|---|
| qwen38-27b | address | `datasets/E52/preds/full/address/address__qwen__r-none__f-schema__mode-main.jsonl` | `e9e96e6cc744284d8654a24977c625a9a4c47f3ef5d5589c8c1f01a5a5768305` | 1816 | 20 |
| qwen38-27b | POI k30 | `datasets/E52/preds/full/poi3/retrieve__qwen__r-low.jsonl` | `4351a16f24f77c973247f2778a665d63a3d03104562d4cc4d07e8066cd309080` | 1869 | 16 |
| qwen38-27b | POI flat | `datasets/E52/preds/full/poi3/flat__qwen__r-low.jsonl` | `84b18b9a43bdfab65365c0909a0fdbed6438ee25c297ec2a0af9dcd41cd0696a` | 1869 | 20 |
| qwen38-27b | WZ k30 | `datasets/E52/preds/full/wz/retrieve__qwen__r-none__c1500.jsonl` | `4600c318218c21d5eab965cbc06b2ae6316b8c54e77b4451e1dc150460cf4a55` | 1869 | 18 |
| gemma4-31b-it | address | `datasets/E52/preds/full/address/address__gemma__r-none__f-schema__mode-main.jsonl` | `0c00533cd711c2c35bc3d9386afa6cf50bd3319380aa8bd8ab9bdfb62e654b71` | 1816 | 20 |
| gemma4-31b-it | POI k30 | `datasets/E52/preds/full/poi3/retrieve__gemma__r-short.jsonl` | `b59cc1e28c438bc0cbffd62d64450b6a34f9de59f0610e17bd9a6b9c2f79677b` | 1869 | 18 |
| gemma4-31b-it | POI flat | `datasets/E52/preds/full/poi3/flat__gemma__r-short.jsonl` | `5313d70328f47fb23ff9134689d92cefdec7a0427b492bb739ee98c0b95b9e6b` | 1869 | 20 |
| gemma4-31b-it | WZ k30 | `datasets/E52/preds/full/wz/retrieve__gemma__r-none__c1500.jsonl` | `80ccc6bb31d63357b177cb2efd9bf5025d70256be49b1dd4c7374573fe2c2068` | 1869 | 19 |
| qwen-agentworld-35b-a3b | address | `datasets/E52/preds/full/address/address__agentworld__r-none__f-schema__mode-main.jsonl` | `5137ebedc1fecf344c07d35dd38b6e7301a4bf8aeb4224a4d49cc32d31c8d795` | 1816 | 20 |
| qwen-agentworld-35b-a3b | POI k30 | `datasets/E52/preds/full/poi3/retrieve__agentworld__r-short.jsonl` | `7fcffffb976b39979bd9b5e9a88543b40bb6912b249f164e27d7b6586eb6b0ad` | 1869 | 20 |
| qwen-agentworld-35b-a3b | POI flat | `datasets/E52/preds/full/poi3/flat__agentworld__r-short.jsonl` | `93f8cea6799c9b1a09c25462aa547e887909b76eeb9cdcbd1568245a56b8f746` | 1869 | 20 |
| qwen-agentworld-35b-a3b | WZ k30 | `datasets/E52/preds/full/wz/retrieve__agentworld__r-none__c1500.jsonl` | `7b96818ef45876d0319db7b3df5db4641d6b3a7f78f08a71ed5f1e2a37201a82` | 1869 | 20 |

Commands (exact, as run from the repository root; E52 = datasets/E52):

- qwen38-27b address: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen38-27b_address.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen38-27b --workers 6 --task address --reasoning none --mode main --fmt schema`
- qwen38-27b POI k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen38-27b_poi_k30.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen38-27b --workers 6 --task topic --schema poi3 --strategy retrieve --k 30 --reasoning low`
- qwen38-27b POI flat: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen38-27b_poi_flat.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen38-27b --workers 6 --task topic --schema poi3 --strategy flat --reasoning low`
- qwen38-27b WZ k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen38-27b_wz.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen38-27b --workers 6 --task topic --schema wz --reasoning none --site-chars 1500`
- gemma4-31b-it address: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/gemma4-31b-it_address.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model gemma4-31b-it --workers 6 --task address --reasoning none --mode main --fmt schema`
- gemma4-31b-it POI k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/gemma4-31b-it_poi_k30.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model gemma4-31b-it --workers 6 --task topic --schema poi3 --strategy retrieve --k 30 --reasoning short`
- gemma4-31b-it POI flat: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/gemma4-31b-it_poi_flat.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model gemma4-31b-it --workers 6 --task topic --schema poi3 --strategy flat --reasoning short`
- gemma4-31b-it WZ k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/gemma4-31b-it_wz.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model gemma4-31b-it --workers 6 --task topic --schema wz --reasoning none --site-chars 1500`
- qwen-agentworld-35b-a3b address: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen-agentworld-35b-a3b_address.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task address --reasoning none --mode main --fmt schema`
- qwen-agentworld-35b-a3b POI k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen-agentworld-35b-a3b_poi_k30.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task topic --schema poi3 --strategy retrieve --k 30 --reasoning short`
- qwen-agentworld-35b-a3b POI flat: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen-agentworld-35b-a3b_poi_flat.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task topic --schema poi3 --strategy flat --reasoning short`
- qwen-agentworld-35b-a3b WZ k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/full/qwen-agentworld-35b-a3b_wz.http.log -- --dev $E52/gold_inputs.jsonl  --out-dir $E52/preds/full --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task topic --schema wz --reasoning none --site-chars 1500`

Agreement between candidates, **no reference** (share of items with the same answer; n in brackets = items where both reach the level):

| run | x | y | n | agree L1 | agree L2 | agree L3 |
|---|---|---|---|---|---|---|
| address | qwen | gemma | 1869 | 0.970 (main address) | | |
| address | qwen | agentworld | 1869 | 0.950 (main address) | | |
| address | gemma | agentworld | 1869 | 0.952 (main address) | | |
| POI k30 | qwen | gemma | 1867 | 0.889 (1770) | 0.766 (1729) | 0.921 (416) |
| POI k30 | qwen | agentworld | 1868 | 0.880 (1774) | 0.743 (1728) | 0.894 (426) |
| POI k30 | gemma | agentworld | 1866 | 0.884 (1808) | 0.764 (1753) | 0.897 (427) |
| POI flat | qwen | gemma | 1863 | 0.891 (1791) | 0.769 (1776) | 0.897 (487) |
| POI flat | qwen | agentworld | 1857 | 0.871 (1771) | 0.736 (1707) | 0.854 (439) |
| POI flat | gemma | agentworld | 1862 | 0.863 (1807) | 0.733 (1736) | 0.865 (458) |
| WZ k30 | qwen | gemma | 1867 | 0.889 (1761) | 0.854 (1760) | 0.805 (1749) |
| WZ k30 | qwen | agentworld | 1868 | 0.861 (1763) | 0.822 (1752) | 0.768 (1736) |
| WZ k30 | gemma | agentworld | 1868 | 0.845 (1830) | 0.798 (1815) | 0.733 (1792) |
| POI k30 vs flat | qwen k30 | qwen flat | 1863 | 0.919 (1760) | 0.820 (1729) | 0.935 (462) |
| POI k30 vs flat | gemma k30 | gemma flat | 1866 | 0.914 (1818) | 0.824 (1786) | 0.936 (469) |
| POI k30 vs flat | agentworld k30 | agentworld flat | 1862 | 0.870 (1801) | 0.762 (1713) | 0.881 (453) |

## Pilot (20 items, seed 52; datasets/E52/pilot_hosts.txt)

Stop rule: stop a candidate if more than 2 of 20 fail. No candidate x run reached it.

Stage pilot: 20 items; 0 without imprint text (0 of them without an ic_fetch.jsonl): address makes no call for them (prediction no_imprint), topics run on the landing page.

| candidate | run | items | done | no call | failed (empty/malformed/truncated/timeout/other) | per 1,000 | cut | abstain | tok in mean / p95 | tok out mean / p95 | s/item median / p95 | window UTC | HTTP errors |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen38-27b (screen) | address | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | - | 791 / 1542 | 70 / 75 | 1.19 / 1.25 | 11-13T13:53-13:53 | 0 |
| qwen38-27b (screen) | POI k30 | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 3 | 2372 / 3315 | 464 / 755 | 7.69 / 41.98 | 11-13T13:53-13:54 | 0 |
| qwen38-27b (screen) | POI flat | 20 | 20 | 0 | 1 (0/1/0/0/0) | 50.0 | 0 | 2 | 23922 / 24969 | 548 / 857 | 14.02 / 23.25 | 11-13T13:54-13:55 | 0 |
| qwen38-27b (screen) | WZ k30 | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 1 | 2971 / 3567 | 24 / 25 | 4.46 / 37.83 | 11-13T13:55-13:55 | 0 |
| gemma4-31b-it (screen) | address | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | - | 833 / 1612 | 53 / 58 | 1.01 / 1.08 | 11-13T13:53-13:53 | 0 |
| gemma4-31b-it (screen) | POI k30 | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 1 | 2427 / 3342 | 63 / 78 | 3.12 / 35.43 | 11-13T13:53-13:53 | 0 |
| gemma4-31b-it (screen) | POI flat | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 0 | 24122 / 25196 | 71 / 81 | 11.04 / 16.40 | 11-13T13:53-13:54 | 0 |
| gemma4-31b-it (screen) | WZ k30 | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 1 | 3055 / 3635 | 28 / 29 | 4.47 / 67.55 | 11-13T13:54-13:55 | 0 |
| qwen-agentworld-35b-a3b | address | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | - | 791 / 1542 | 51 / 56 | 0.59 / 0.65 | 11-13T13:55-13:55 | 0 |
| qwen-agentworld-35b-a3b | POI k30 | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 1 | 2364 / 3306 | 79 / 99 | 3.00 / 5.27 | 11-13T13:55-13:56 | 0 |
| qwen-agentworld-35b-a3b | POI flat | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 1 | 23913 / 24960 | 78 / 107 | 3.39 / 5.17 | 11-13T13:56-13:56 | 0 |
| qwen-agentworld-35b-a3b | WZ k30 | 20 | 20 | 0 | 0 (0/0/0/0/0) | 0.0 | 0 | 0 | 2965 / 3567 | 23 / 25 | 5.43 / 9.20 | 11-13T13:55-13:56 | 0 |

Prediction files (sha256):

| candidate | run | file | sha256 | calls | cached calls |
|---|---|---|---|---|---|
| qwen38-27b | address | `datasets/E52/preds/pilot/address/address__qwen__r-none__f-schema__mode-main.jsonl` | `bdcd3c5a85d3be83efc8ac76ca81b62869275d3c7f09ad6c8ec94d459043bd79` | 20 | 0 |
| qwen38-27b | POI k30 | `datasets/E52/preds/pilot/poi3/retrieve__qwen__r-low.jsonl` | `ea40c7c6164c6d44d75f598ffeeaa0311f48f352fde800d5d282af6d6f4620ff` | 20 | 0 |
| qwen38-27b | POI flat | `datasets/E52/preds/pilot/poi3/flat__qwen__r-low.jsonl` | `1117bc01e2c09aae8ed06ccbc503999ffe7281b6ee1db4f39d0e2eedfacb3976` | 20 | 0 |
| qwen38-27b | WZ k30 | `datasets/E52/preds/pilot/wz/retrieve__qwen__r-none__c1500.jsonl` | `2ca59904528a8cfb8a95f412b5103abd2546932910b0668c46e4bc1c42ba4f31` | 20 | 0 |
| gemma4-31b-it | address | `datasets/E52/preds/pilot/address/address__gemma__r-none__f-schema__mode-main.jsonl` | `bb44331711ad80187e9775de9e433b641db6c508ea07f0307fb5ab03cfe5dc8d` | 20 | 0 |
| gemma4-31b-it | POI k30 | `datasets/E52/preds/pilot/poi3/retrieve__gemma__r-short.jsonl` | `b80ff7d9f1a641aed4d9730f6a837289414b4118b1a209d32915688bcf903bc0` | 20 | 0 |
| gemma4-31b-it | POI flat | `datasets/E52/preds/pilot/poi3/flat__gemma__r-short.jsonl` | `398ab080c537142a894ae709fe75f349fe55ee634fefc74ffaf033a61f055aff` | 20 | 0 |
| gemma4-31b-it | WZ k30 | `datasets/E52/preds/pilot/wz/retrieve__gemma__r-none__c1500.jsonl` | `f2b317052e3122396d2d24df656d6985f418ab5a41dacdde4c11fe03db0a9b80` | 20 | 0 |
| qwen-agentworld-35b-a3b | address | `datasets/E52/preds/pilot/address/address__agentworld__r-none__f-schema__mode-main.jsonl` | `e91c04aae8b217aa6b83a06578c10e76aa05eaa75f9a6e13d69126de46f5b9a2` | 20 | 0 |
| qwen-agentworld-35b-a3b | POI k30 | `datasets/E52/preds/pilot/poi3/retrieve__agentworld__r-short.jsonl` | `0738e19f2d771f85092756cafa754c24528efd3e76b3c1cdfa7175bb02b6bc4b` | 20 | 0 |
| qwen-agentworld-35b-a3b | POI flat | `datasets/E52/preds/pilot/poi3/flat__agentworld__r-short.jsonl` | `cd9698abd3b0bc960389b844bb47f0a6d59e72a2573cf2b5f562dd8fa5f6489e` | 20 | 0 |
| qwen-agentworld-35b-a3b | WZ k30 | `datasets/E52/preds/pilot/wz/retrieve__agentworld__r-none__c1500.jsonl` | `a13f573d659e3e14312ea71891d2663a627f6876d6f94cde86c06ec0ad8ebafe` | 20 | 0 |

Commands (exact, as run from the repository root; E52 = datasets/E52):

- qwen38-27b address: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen38-27b_address.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen38-27b --workers 6 --task address --reasoning none --mode main --fmt schema`
- qwen38-27b POI k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen38-27b_poi_k30.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen38-27b --workers 6 --task topic --schema poi3 --strategy retrieve --k 30 --reasoning low`
- qwen38-27b POI flat: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen38-27b_poi_flat.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen38-27b --workers 6 --task topic --schema poi3 --strategy flat --reasoning low`
- qwen38-27b WZ k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen38-27b_wz.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen38-27b --workers 6 --task topic --schema wz --reasoning none --site-chars 1500`
- gemma4-31b-it address: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/gemma4-31b-it_address.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model gemma4-31b-it --workers 6 --task address --reasoning none --mode main --fmt schema`
- gemma4-31b-it POI k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/gemma4-31b-it_poi_k30.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model gemma4-31b-it --workers 6 --task topic --schema poi3 --strategy retrieve --k 30 --reasoning short`
- gemma4-31b-it POI flat: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/gemma4-31b-it_poi_flat.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model gemma4-31b-it --workers 6 --task topic --schema poi3 --strategy flat --reasoning short`
- gemma4-31b-it WZ k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/gemma4-31b-it_wz.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model gemma4-31b-it --workers 6 --task topic --schema wz --reasoning none --site-chars 1500`
- qwen-agentworld-35b-a3b address: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen-agentworld-35b-a3b_address.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task address --reasoning none --mode main --fmt schema`
- qwen-agentworld-35b-a3b POI k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen-agentworld-35b-a3b_poi_k30.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task topic --schema poi3 --strategy retrieve --k 30 --reasoning short`
- qwen-agentworld-35b-a3b POI flat: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen-agentworld-35b-a3b_poi_flat.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task topic --schema poi3 --strategy flat --reasoning short`
- qwen-agentworld-35b-a3b WZ k30: `python3 -I scripts/E52/run.py --http-log $E52/logs/pilot/qwen-agentworld-35b-a3b_wz.http.log -- --dev $E52/gold_inputs.jsonl --hosts $E52/pilot_hosts.txt --out-dir $E52/preds/pilot --cache $E52/cache --model qwen-agentworld-35b-a3b --workers 6 --task topic --schema wz --reasoning none --site-chars 1500`

Agreement between candidates, **no reference** (share of items with the same answer; n in brackets = items where both reach the level):

| run | x | y | n | agree L1 | agree L2 | agree L3 |
|---|---|---|---|---|---|---|
| address | qwen | gemma | 20 | 1.000 (main address) | | |
| address | qwen | agentworld | 20 | 0.900 (main address) | | |
| address | gemma | agentworld | 20 | 0.900 (main address) | | |
| POI k30 | qwen | gemma | 20 | 0.941 (17) | 0.824 (17) | 0.667 (6) |
| POI k30 | qwen | agentworld | 20 | 0.941 (17) | 0.824 (17) | 1.000 (5) |
| POI k30 | gemma | agentworld | 20 | 0.895 (19) | 0.737 (19) | 0.833 (6) |
| POI flat | qwen | gemma | 19 | 0.941 (17) | 0.765 (17) | 0.600 (5) |
| POI flat | qwen | agentworld | 19 | 0.941 (17) | 0.812 (16) | 0.667 (3) |
| POI flat | gemma | agentworld | 20 | 0.895 (19) | 0.778 (18) | 1.000 (4) |
| WZ k30 | qwen | gemma | 20 | 0.833 (18) | 0.833 (18) | 0.833 (18) |
| WZ k30 | qwen | agentworld | 20 | 0.789 (19) | 0.778 (18) | 0.778 (18) |
| WZ k30 | gemma | agentworld | 20 | 0.895 (19) | 0.889 (18) | 0.889 (18) |
| POI k30 vs flat | qwen k30 | qwen flat | 19 | 1.000 (16) | 0.938 (16) | 0.800 (5) |
| POI k30 vs flat | gemma k30 | gemma flat | 20 | 1.000 (19) | 1.000 (19) | 0.750 (8) |
| POI k30 vs flat | agentworld k30 | agentworld flat | 20 | 0.789 (19) | 0.667 (18) | 0.667 (3) |
