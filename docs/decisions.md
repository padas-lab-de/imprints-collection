# Lead record

## In flight
- E2-gold-baseline-innkube: `ic evaluate` on all 1,000 gold items for Qwen3.8-27B (reasoning off) and Gemma4-31B, then --retry-failed. Logs results/logs/E2-<model>.log, outputs results/<model>/german/simple/eval/. Free (innkube). When done: compare, write numbers to status page.
- E4-fetch-yield-baseline: `ic fetch small_sample_seed_hosts.txt` on this crawl VM. Log results/logs/E4-fetch-sample.log, output datasets/imprints_batch*.jsonl.gz. When done: break down failures (no imprint found, JS-only, timeout, redirect).

## Cards
| ID | Date | Question | Outcome | Landed in |
|---|---|---|---|---|
| D8-gold-set-extension | 2026-10-23 | Extend the 1,000-item gold set or re-do it? | A: keep 1,000 + ~300 hard items + 2nd annotator on 200 | — |
| D9-geocoding-ground-truth | 2026-10-23 | What counts as ground truth for geocoding eval? | A: automatic consistency on all + manual check of 100 | — |
| A1-env-and-models | 2026-10-23 | Create .env; tell which open models innkube/Slurm can serve | Done: .env has INNKUBE_API_KEY; innkube serves qwen38-27b, gemma4-31b-it, qwen-agentworld-35b-a3b, soofi-s-isar-preview (no Qwen3-Next any more) | — |
| A2-original-paper-and-snapshot | 2026-10-23 | Share original paper/venue/reviews and location of the old results | Partly: paper = WebSci Companion '26 demo (arXiv 2609.03971, 5 pp., no eval numbers); this machine is the crawl VM; old results path still open | — |
| D7-gold-set-provenance | 2026-10-23 | How was the gold set made? | Human-annotated; can extend; quality not guaranteed, may be redone entirely | — |
| D6-snapshot-growth-source | 2026-10-23 | Where does the larger snapshot come from? | Better fetch yield + link expansion | — |
| D5-topic-eval-granularity | 2026-10-23 | How to score topics vs. 11-class gold? | Map predicted category to top-level ancestor, translate, macro-F1 | — |
| D4-extension-contributions | 2026-10-23 | What does the journal extension add? | Model comparison; error analysis + geocoding eval | — |
| D3-tooling-scope | 2026-10-23 | How much to modernize tooling? | Minimal fixes (keep Poetry); modernize only where necessary | — |
| D2-llm-access | 2026-10-23 | Which LLMs may we use? | Uni Passau cluster, paid APIs (within $20/run, $30/day), FAITH Slurm cluster for own GPUs | — |
| D1-revision-driver | 2026-10-23 | Why revise now? | Journal extension with better evaluation + fresh (larger) data snapshot; no hard deadline | — |

## Lead actions
- 2026-10-23 Merged e1-eval-harness (oracle 100%; 28 tests pass after fixing duplicate dev-deps table). Added Qwen3.8-27B/Gemma4-31B to config with per-model extra_body; Qwen3.8 needs reasoning_effort=none (else 6/20 topic calls hit the 2,000-token limit). Note: scoring treats all-blank addresses as failed; must change to a valid 'no address' answer once D8 negatives exist.
- 2026-10-23 Merged d3-minimal-fixes (17 smoke tests pass; vllm optional; python <3.13; README paths fixed; CLAUDE.md added).
- 2026-10-23 Appended MODEL_API_ENDPOINT/MODEL_API_KEY (interpolates INNKUBE_API_KEY)/GEOCODING_API_ENDPOINT to .env; local Photon on :2322 answers.
- 2026-10-23 Paper finding: 3,226,331 imprints -> 3,225,347 'extracted addresses' (99.97%); Address schema has only required fields, so the LLM cannot answer 'no address' -> precision unknown. Probe (gemma4-31b-it, qwen38-27b, one address-free imprint): both return all-empty fields, so no forced hallucination in the clear case; CONFIRMED src/ic/cli/stats.py:126 counts every record with an 'address' key, incl. all-empty ones -> paper's 3,225,347 'extracted address' counts responses, not addresses; recompute from old results (needs A2 path).
- 2026-10-23 Drafted docs/annotation_guideline.md v0.1 for D8 (awaits user review).
- 2026-10-23 Gold audit: 987/1000 items have all address fields verbatim in text; all 1000 have exactly one address, 999 'Deutschland'; no negatives, no multi-address, no AT/CH.
- 2026-10-23 Orientation: found gold standard unused by code; gold topic labels (11 English top-level) differ from model label space (796 German categories); gold has no empty-address cases; deps/README drift.
