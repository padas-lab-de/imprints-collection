# E53 step 15: r5 top-up (2026-11-14)

Design: `docs/gold_set_design.md` §2.3. Script: `scripts/E53/topup.py` (`draw`, `merge`, `assign`), tests `tests/test_e53_topup.py`.
One paid call batch (prefill, $0.0038). All steps ran on 2026-11-14 UTC.

## Draw (source: `datasets/E53/topup/draw.json`)

| | value |
|---|---|
| r5 final (`canonical_sites_after_filter.txt` of the r5 build) | 3,945,356 sites, sha256 `93bd4d30dcc4d290a63953d5df98b2e64d8e0bef413a68653ed1b58d3cf0c461` |
| frame source (r4 + E40 r2) | 3,908,045 sites, sha256 `748f70f4…` (same file as `frame.json`) |
| r5 keys not in the frame source | 37,338 |
| of these in the exclusion lists (`exclusions/union.txt`) | 27 |
| **N_A** | **37,311** |
| N0 (`frame/frame.json`) | 3,901,721 |
| n_A = round(1,869 x N_A / N0) = round(17.87) | **18** |
| pi = n_A / N_A | 0.000482431 (weight N_A / n_A = 2,072.83) |
| seed | **20261114** (first 18 of F_A sorted by sha256(f"{seed}:{key}"), key = lower-case host without `www.`) |
| frame-source keys not in r5 | 27 |
| gold items not in r5 (dropped) | **0** (`datasets/E53/dropped_r5.jsonl` is empty) |

Key = lower-case host without a leading `www.` (as in the frame).
- Basis 1,869 (lead, 2026-11-14): the top-up has the mean sampling fraction of the drawn set. The design text had 1,000, written before D60 D.
- Fields of `topup_sample.jsonl` are those of `gold_sample.jsonl`: stratum and fold_group "topup", selected_for ["topup"], core false, classes [], M_h = N_A, m_h = n_A.
- Folds: the 18 items go in seeded order to the fold with the fewest items. Folds before: 374 / 374 / 374 / 374 / 373. Folds after: 378 / 378 / 377 / 377 / 377 (1,887 items).
- The 27 r5 additions that are in the exclusion lists are earlier-used hosts. They stay out, as in F0.

Files (sha256):

| file | sha256 |
|---|---|
| `datasets/E53/topup_sample.jsonl` (18 lines) | `58c350e40e47a0d593768b9032e7f924f38ce098fb45989c6179c6a7f8b66c5e` |
| `datasets/E53/dropped_r5.jsonl` (0 lines) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `datasets/E53/topup/hosts.txt` | `b61772b6f2f919fdfa25c7eecf656398c4cca443048537a990f47198fb8032c4` |
| `datasets/E53/phase2/gold_sample.jsonl` (unchanged) | `fc6d45a89355f48629cf1cbb7b590475443e0c6e124f695c14c07df9e453322e` |

## Same-day ic fetch and capture

| | ic fetch | capture |
|---|---|---|
| VM | aralie, checkout tree **collection-release 88b162a** (unchanged since step 5) | akazie, `.venv-render` as in step 5 |
| driver | `scripts/E53/fetch_run.sh datasets/E53/topup/hosts.txt datasets/E53/topup/fetch` | `run_capture_topup.sh` -> `scripts/E53/capture.py --sample datasets/E53/topup/topup_sample.jsonl --out datasets/E53/topup/capture --ip-group akazie --workers 2 --stop-on-block` |
| UTC | 04:15:41Z – 04:24:27Z | 04:19:28Z – 04:24:34Z |
| logs (in `datasets/E53/topup/`) | `fetch_driver.log`, `fetch/fetch_main.log`, `fetch/fetch_shopify.log` | `capture.log`, `capture.err` (empty) |

- All 18 items are Shopify sites (provider group v4:23.227.38, the E48 additions). Pass 1 skipped them; pass 2 fetched them with the D59 settings: 4 workers, provider concurrency 1, delay 5 s.
- ic fetch: 18 imprint_found. throttled 0, no 429/503 in the logs.
- Capture: 17 landing+imprint, 1 landing_only (liaison.life), 0 failed.
  - liaison.life: live, HTTP 200. The capture found no imprint link or probe on the landing page. ic fetch found an imprint.
- **503/429: none.** New `--stop-on-block`: after each item, `capture.py` scans every `*status` field of the record for 503 or 429, then writes `STOP_BLOCKED.json` and captures no later item. It did not fire. Each record was also checked from outside during the run.
- Nothing is left to capture.
- input_day_mismatch: 0. Cookie banners: landing 10 none and 8 rejected; imprint 17 none.
- Merge: `python3 -I scripts/E53/topup.py merge --capture-dir datasets/E53/topup/capture --fetch-dir datasets/E53/topup/fetch/main --fetch-dir datasets/E53/topup/fetch/shopify --fetch-vm aralie --fetch-tree 88b162a`.
  - It uses `merge_fetch.merge_item`, as in step 5.
  - It adds 18 new item dirs and does not touch existing dirs.
  - Summary: `datasets/E53/topup/merge_summary.json`.
- Manifest `datasets/E53/gold/manifest.sha256` (recursive):
  - 18,433 files, sha256 **`b217d5cd84dcb59fa93a4d8cbc04ca71f648ac4af3a12974a48aaf6c328d7937`**.
  - The old one is kept as `manifest_pre_topup.sha256` (18,259 files, `2196f390…`).
  - All 18,259 old lines are in the new manifest unchanged. The 174 new lines all belong to the 18 new dirs.
- On akazie, the step 5 `capture.py` is kept as `scripts/E53/capture.py.pre_topup`. The new file has the stop check.

## Prefill (paid, D61)

- `python3 -I scripts/E53/prefill.py --ic-fetch-dir datasets/E53/gold --hosts datasets/E53/topup/hosts.txt --out-dir datasets/E53/gold --out-file prefill_topup.jsonl`
  - The model is anthropic/claude-haiku-5.5 with the same settings as the full run. The new option `--out-file` sets the output file.
- Before the run:
  - The dry-run estimate was $0.0044 for 18 calls, worst case $0.0123.
  - Ledger: D61 total $0.4962 of $10, UTC 2026-11-14 $0 of $30. No row dated 2026-11-14 in any checkout's ledger.
- Result: 18 items, 0 errors, 0 parse failures, 18 calls, 30,460 in / 1,445 out tokens.
  - **$0.003769 reported** (ledger row 2026-11-14 in `docs/cost_ledger.csv`). The D61 total is now $0.4999.
  - Each item has one suggested address.
- Output: `datasets/E53/gold/prefill_topup.jsonl`, sha256 `8c10d6d7c3e31c1a967021080f1792ef99e750ce9bbc3bba1d216ad0429c21a8`.
  - `prefill.jsonl` is unchanged (`4edc04a2…`).
- Ledger path: the run wrote an absolute path, because the worktree root is not the checkout that holds `datasets/`. The row was made repo-relative by hand. `prefill._rel` now keeps the part from `datasets/` on, and a test covers this.
- Labelling tool: `Store` now reads `<data-dir>/prefill.jsonl` and then `prefill_topup.jsonl` by default. A later file wins, and missing files are skipped. `--prefill-file` can be given more than once. Tests are in `tests/test_gold_labels.py`. A check on the real files showed all 18 top-up items with a suggestion.

## Assignment (source: `datasets/E53/topup/assign_summary.json`)

- Command: `python3 -I scripts/E53/topup.py assign`, function `ic.gold.assignment.extend_assignment`, seed **20261114** (step 6 used 20261113).
- The top-up items get primary labels only: no calibration and no second labels. Their item numbers are 1869-1886.
- Each item goes to the labeller with the lightest load relative to 2:1:1. Dropped items would not count, but there are none.
- Per labeller, the new rows go after the last existing row. Old rows are unchanged; the 2,344 old lines are in the new file in the same order.

| labeller | rows before | new primary | rows after | 2:1:1 of 2,362 |
|---|---|---|---|---|
| L1 | 1,172 | 8 | 1,180 | 1,181 |
| L2 | 586 | 5 | 591 | 590.5 |
| L3 | 586 | 5 | 591 | 590.5 |
| all | 2,344 | 18 | 2,362 | |

| file | sha256 |
|---|---|
| `datasets/E53/gold/assignment.jsonl` (new, 2,362 rows) | **`d789e82a6b8d668b8f75298299193dd9a38f6b3e305eb6190aa994113cf6001e`** |
| `datasets/E53/gold/assignment_pre_topup.jsonl` (old) | `37a72fb9afe8788392efcf7ee07a57ee589fe1ba66da9e6ff824ec857f7c8259` |

## Items

| item | host | fold | labeller | order | ic fetch | capture |
|---|---|---|---|---|---|---|
| 1869 | alldiamondpainting.at | 2 | L1 | 1177 | imprint_found | landing+imprint |
| 1870 | dackelmania.com | 0 | L3 | 588 | imprint_found | landing+imprint |
| 1871 | drakensberg.de | 1 | L3 | 591 | imprint_found | landing+imprint |
| 1872 | dropsoul.ch | 0 | L2 | 589 | imprint_found | landing+imprint |
| 1873 | eratec-germany.com | 4 | L2 | 587 | imprint_found | landing+imprint |
| 1874 | frollein-kaethe.de | 0 | L1 | 1175 | imprint_found | landing+imprint |
| 1875 | haustierurnen.de | 2 | L1 | 1176 | imprint_found | landing+imprint |
| 1876 | kaminfix.de | 4 | L2 | 591 | imprint_found | landing+imprint |
| 1877 | konvolut-store.de | 4 | L1 | 1179 | imprint_found | landing+imprint |
| 1878 | liaison.life | 1 | L3 | 587 | imprint_found | landing_only |
| 1879 | little-morilu.de | 3 | L2 | 588 | imprint_found | landing+imprint |
| 1880 | murmann-verlag.de | 3 | L3 | 589 | imprint_found | landing+imprint |
| 1881 | mytola.de | 2 | L3 | 590 | imprint_found | landing+imprint |
| 1882 | nanipaw.com | 0 | L1 | 1173 | imprint_found | landing+imprint |
| 1883 | ryda.cc | 4 | L1 | 1174 | imprint_found | landing+imprint |
| 1884 | shop.schwimmbadschlueter.de | 1 | L1 | 1180 | imprint_found | landing+imprint |
| 1885 | shop.sonntagsblatt.de | 1 | L1 | 1178 | imprint_found | landing+imprint |
| 1886 | wurmli.de | 3 | L2 | 590 | imprint_found | landing+imprint |

## E52 runs

The 12 innkube runs on the 18 top-up items are in `results/E52/runs.md`, section "Top-up".
- They ran at 04:32-04:39Z with 6 workers per run.
- All 12 x 18 items are done: 0 failed, 0 HTTP errors, no 429/503.
- Predictions: `datasets/E52/preds/topup/`. Inputs: `datasets/E52/topup_inputs.jsonl`.

## Notes and doubts

- **Queue position.** The top-up rows come last in each queue. If a labeller stops early, top-up items stay unlabelled. They could be moved forward with new orders. This is not done: the old rows would then change.
- **Load reading.** "Lighter loads first" is read as load relative to 2:1:1. Absolute load would give all 18 items to L2 and L3 (L1 has 1,172 rows).
- **All top-up items are Shopify shops.** This is expected: almost all r5 additions are E48 Shopify sites (36,983 of 37,338). Shopify sites that E48 did not reach are not in r5, so the gold set does not cover them.
- **Labels of the top-up stratum.** They have no screen classes, so they are not in any POI/WZ oversample stratum. Per-class tables count them only through their labels.
