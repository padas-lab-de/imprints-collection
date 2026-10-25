# Lead record

## In flight
- E16-snapshot-crawl-seeds: lead-run, full 6,560,119 seeds shuffled (scripts/E16/shuffle.py, seed 20261024) in 263 batches of 25k, cap 8 (D18 via E15), one process per 3 batches (scripts/E16/run.sh, STEP=3, nohup; restarted 2026-10-25 04:22 UTC from batch 19 after RSS 25.5 GB + swap full), started 2026-10-24 09:30 UTC -> datasets/E16/seeds, logs results/E16/logs/ (driver.log says "all done" at end). Resumes on re-run; ranges can move to other machines (run.sh FIRST LAST). Check progress daily.

## Cards
| ID | Date | Question | Outcome | Landed in |
|---|---|---|---|---|
| D22-crawl-speedup-route | 2026-10-24 | Speed up the crawl: parallel VMs + polite limits + recovery pass from a 2nd IP, or a faster first round with looser limits + slow second round? | open (recommend A) | — |
| D21-guideline-open-points | 2026-10-24 | Accept the labelling guideline's seven judgement calls as drafted? | open (recommend A) | — |
| A5-crawl-vm-access | 2026-10-24 | Hostnames + SSH access for the extra crawl-subnet VMs | open | — |
| D20-crawl-machines | 2026-10-24 | Spread the crawl over more machines: more crawl-subnet VMs, FAITH nodes, or this VM only? | A: more crawl-subnet VMs (user) | — |
| D19-link-expansion-depth | 2026-10-24 | Link expansion depth 1 all TLDs, plus depth 2-3 on .de/.at/.ch only, or depth 3 all TLDs? | C: depth 3 across all TLDs (user) | — |
| D18-snapshot-provider-cap | 2026-10-24 | Full seed crawl at 4 or 8 parallel requests per provider network? | C -> E15 run, then lead picked 8 (B): Strato block 0.7% vs 0.44%, IONOS 0.24% vs 0.53%, found rate equal, 59 vs 74 min per 25k | — |
| D17-gold-set-size | 2026-10-23 | Gold set ~1,300 items (~80 annotator h) or lean ~1,100? | B, cut to 1,000 items; no stratum comparisons needed (user) | — |
| D16-link-expansion-scope | 2026-10-23 | One round with ccTLD filter, all TLDs, or none? | B: all TLDs, keep DACH-address imprints; depth up to 3 under test (E14) (user) | — |
| D15-gold-annotation-workforce | 2026-10-23 | Who labels: model pre-label + human check, or humans from scratch? | C: every item labelled once from scratch, a second person independently ~20%; no model pre-labels (user). 2026-10-24: three labellers, one with double capacity (user) | — |
| D14-gold-label-source | 2026-10-23 | Gold labels from the live rendered site or from fetched text? | A: label from the live rendered site; archive HTML, DOM and screenshot (user) | — |
| D13-personal-data-release | 2026-10-23 | Open, two-tier or derived-only release of personal imprint data? | B: full open release, assume best case (user) | — |
| A3-dpo-consultation | 2026-10-23 | Ask Uni Passau DPO about publishing imprint personal data | dropped by user | — |
| A4-apc-funding | 2026-10-23 | Who pays the EUR 2,390 APC (DEAL agreement?) | done: covered by Uni Passau agreement | — |
| D12-town-granularity-metric | 2026-10-23 | How to score town/district differences? | A: geocoding-based location match primary; guideline copies town as written | — |
| D11-topic-eval-input | 2026-10-23 | Evaluate topics on imprint text or re-fetched homepages? | A: re-fetch homepages of the 1,000 gold hosts | — |
| D10-journal-venue | 2026-10-23 | Target journal? | Scientific Data, Data Descriptor (example s41597-026-07945-2) | — |
| D8-gold-set-extension | 2026-10-23 | Extend the 1,000-item gold set or re-do it? | A, superseded 2026-10-23: user wants a new diversity-stratified gold set (see D14) | — |
| D9-geocoding-ground-truth | 2026-10-23 | What counts as ground truth for geocoding eval? | A: automatic consistency on all + manual check of 100 | — |
| A1-env-and-models | 2026-10-23 | Create .env; tell which open models innkube/Slurm can serve | Done: .env has INNKUBE_API_KEY; innkube serves qwen38-27b, gemma4-31b-it, qwen-agentworld-35b-a3b, soofi-s-isar-preview (no Qwen3-Next any more) | — |
| A2-original-paper-and-snapshot | 2026-10-23 | Share original paper/venue/reviews and location of the old results | Partly: paper = WebSci Companion '26 demo (arXiv 2609.03971, 5 pp., no eval numbers); this machine is the crawl VM; old results no longer exist (paper figures cannot be recomputed; new snapshot replaces them) | — |
| D7-gold-set-provenance | 2026-10-23 | How was the gold set made? | Human-annotated; can extend; quality not guaranteed, may be redone entirely | — |
| D6-snapshot-growth-source | 2026-10-23 | Where does the larger snapshot come from? | Better fetch yield + link expansion | — |
| D5-topic-eval-granularity | 2026-10-23 | How to score topics vs. 11-class gold? | Map predicted category to top-level ancestor, translate, macro-F1 | — |
| D4-extension-contributions | 2026-10-23 | What does the journal extension add? | Model comparison; error analysis + geocoding eval | — |
| D3-tooling-scope | 2026-10-23 | How much to modernize tooling? | Minimal fixes (keep Poetry); modernize only where necessary | — |
| D2-llm-access | 2026-10-23 | Which LLMs may we use? | Uni Passau cluster, paid APIs (within $20/run, $30/day), FAITH Slurm cluster for own GPUs | — |
| D1-revision-driver | 2026-10-23 | Why revise now? | Journal extension with better evaluation + fresh (larger) data snapshot; no hard deadline | — |

## Lead actions
- 2026-10-25: E16 memory leak ~2.5 GB per batch in one fetch process (25.5 GB RSS at batch 19, swap full, OOM risk to the Owler service). Stopped and restarted from 19 with 3 batches per process; resume kept 9,455 done hosts of batch 19. Root cause not fixed yet.
- 2026-10-24: Merged E17-gold-capture (153fce2), 166 tests pass; recounted meta.json: 620 landing+imprint, 283 landing only, 49 failed, 48 Strato deferred. Known gaps: 8 pages with a persisting cookie banner, 10 click-found imprints may lack imprint text in the PNG (check DOM), 49 failed not retried (--retry-failed).
- 2026-10-24: Crawl-speed check on E16 batches 0-7: limiter is not the brake (IONOS ~2.7, Strato ~2.0 req/s vs cap 4; 1.4% hosts throttled); 64 workers x 7.2 s/host mean; ~18% of batch time is the tail; host_not_found 18.8% of hosts, of which retryable (403/429/503/timeout/conn/refused) ~15.2k = 7.6% of all hosts. clamd CPU is the Owler service's, not ours; left alone.
- 2026-10-24: merged E18 fix round (3ba4641): first address main by default, rejected save shows message; scripts/gold/e18_browser_check.py 22/22 PASS three runs (lead fixed relative --gold path). Labelling tool ready once D21 answered.
- 2026-10-24: merged E18 (91f44b9 -> baa795e; 155 tests). Assignment checked: L1 520 primary + 80 second + 50 calibration = 650, L2/L3 215+60+50 = 325; 950 items one primary, 50 calibration labelled by all three (consensus = gold); 200 second labels on other labeller. Calibration counted within the 2:1:1 loads.
- 2026-10-24: Assumed for D15 with three labellers: each item has one primary labeller, load split 2:1:1 across the 1,200 labels (1,000 primary + 200 second; about 600/300/300), second labels spread over all three pairs; calibration 50 items labelled by all three. No WARC in E17 (design doc says optional).
- 2026-10-24: merged E12-gold-screening (5d9490f): 10,000 screened, 1,000-item gold sample drawn (core 700 + oversample 300, T=30, seed 20261025) -> datasets/E12/gold_sample.jsonl; verified tests, counts, weight sum 6,555,096. Assumed (design doc §7): full frame incl. 201 not-live core items; LLM operator type for stratification only; WARCs internal. Strato block -> capture gold sites from another IP.
- 2026-10-24 E15 (cap 8, 25k fresh seeds) finished in 59 min; block rates at Strato/IONOS within noise of cap 4 -> D18 B, started E16 seed crawl.
- 2026-10-24 E14 merged; round 2/3 reachable and found counts checked against output (10,548/424, 7,965/134).
- 2026-10-24 E13 merged, 115 tests pass, 100,000 status rows and Strato 6,433 hosts (5,233 found) checked. Assumed: full crawl runs in ranges of ~10 batches per process (memory grows ~0.5 GB/h).
- 2026-10-23 E11 merged: E4 fetcher keyed landing links by URL path (fe4963b), losing external hosts; E9 count (34,771 unique) verified and is the right basis, E10 estimate and D16 stand.
- 2026-10-23 E8 merged, tests pass, prevalences re-counted from results/E8/pilot_features.jsonl. Assumed per design doc §7: full seed-list frame with negatives capped; LLM operator type for stratification only; WARC kept internal, not published; image-only quota 20; gold capture from a second IP with retries.
- 2026-10-23 E10 merged, 80 tests pass, 1,231/9,182 found verified from output.
- 2026-10-23 E9 merged, 80 tests pass, yield 10,246/16,129 and 49/50 precision verified from files. E8 hit an API rate limit and was resumed.
- 2026-10-23 E6 merged (8e35e07), 65 tests pass, yield 10,327/16,093 verified from output.
- 2026-10-23 E7 merged (741c7a8), 35 tests pass, Qwen street-level 0.982 checked in metrics.json.
- 2026-10-23 Checked: innkube gemma4-31b-it and qwen38-27b both accept image input (transcribed a synthetic address PNG correctly). Screenshot path stays an edge case per user; size decided after E8 prevalence.
- 2026-10-23 User: new diversity-stratified gold set may replace the old one (D8 superseded); A4 done; A3 dropped; D13 B.
- 2026-10-23 Venue research done: docs/venue_scientific_data.md (verified licence and personal-data policy quotes). Assumed: deposit on Zenodo under CC BY, code via GitHub + Zenodo DOI; model comparison goes into Technical Validation.
- 2026-10-23 D10/D11/D12 answered; annotation guideline: Town copied as written. A2: old results gone, paper's address count cannot be recomputed.
- 2026-10-23 Assumed: implement E5 static-rule fixes F1-F6, F9 under D6 (no card); F7 landing-page-as-imprint and F8 Kontakt-as-imprint left out (change what counts as an imprint). Assumed: fix stats.py/merge.py empty-address count (bug fix).
- 2026-10-23 E5 done, verified (counts match JSONL; dasekg.de base href and terontec.de query link confirmed live).
- 2026-10-23 E4 random 20k done (results in status.md); data in datasets/E4/.
- 2026-10-23 E2 done (see status.md). Created docs/status.md.
- 2026-10-23 Merged e1-eval-harness (oracle 100%; 28 tests pass after fixing duplicate dev-deps table). Added Qwen3.8-27B/Gemma4-31B to config with per-model extra_body; Qwen3.8 needs reasoning_effort=none (else 6/20 topic calls hit the 2,000-token limit). Note: scoring treats all-blank addresses as failed; must change to a valid 'no address' answer once D8 negatives exist.
- 2026-10-23 Merged d3-minimal-fixes (17 smoke tests pass; vllm optional; python <3.13; README paths fixed; CLAUDE.md added).
- 2026-10-23 Appended MODEL_API_ENDPOINT/MODEL_API_KEY (interpolates INNKUBE_API_KEY)/GEOCODING_API_ENDPOINT to .env; local Photon on :2322 answers.
- 2026-10-23 Paper finding: 3,226,331 imprints -> 3,225,347 'extracted addresses' (99.97%); Address schema has only required fields, so the LLM cannot answer 'no address' -> precision unknown. Probe (gemma4-31b-it, qwen38-27b, one address-free imprint): both return all-empty fields, so no forced hallucination in the clear case; CONFIRMED src/ic/cli/stats.py:126 counts every record with an 'address' key, incl. all-empty ones -> paper's 3,225,347 'extracted address' counts responses, not addresses; recompute from old results (needs A2 path).
- 2026-10-23 Drafted docs/annotation_guideline.md v0.1 for D8 (awaits user review).
- 2026-10-23 Gold audit: 987/1000 items have all address fields verbatim in text; all 1000 have exactly one address, 999 'Deutschland'; no negatives, no multi-address, no AT/CH.
- 2026-10-23 Orientation: found gold standard unused by code; gold topic labels (11 English top-level) differ from model label space (796 German categories); gold has no empty-address cases; deps/README drift.
