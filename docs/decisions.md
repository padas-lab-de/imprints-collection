# Lead record

## In flight
- E8-gold-strata-pilot: Opus subagent, worktree branch E8-gold-strata-pilot. Writes docs/gold_set_design.md (diversity strata, detectors, quotas, archive, protocol, eval plan, related work) and pilots detectors on 1,000 random hosts -> results/E8/pilot_features.jsonl, datasets/E8/. D14 A, D15 C (told the agent); screenshot stratum is an edge case per user. On return: tests, spot-check prevalences, turn open choices into cards.
- E6-fetch-rule-fixes: Sonnet subagent in a worktree, branch E6-fetch-rule-fixes (from lead-record). Implements E5 fixes F1-F6, F9 + stats.py/merge.py empty-address count fix, re-runs fetch on datasets/E4/random20k_seed_hosts.txt -> datasets/E6/random20k/, precision sample -> results/E6/precision_sample.jsonl, report docs/experiments/E6-fetch-rule-fixes.md on branch. On return: run tests, read diff, check precision sample, merge into lead-record.

## Cards
| ID | Date | Question | Outcome | Landed in |
|---|---|---|---|---|
| D15-gold-annotation-workforce | 2026-10-23 | Who labels: model pre-label + human check, or humans from scratch? | C: one human all items, second human ~20% | — |
| D14-gold-label-source | 2026-10-23 | Gold labels from the live rendered site or from fetched text? | A: live rendered site + archive | — |
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
