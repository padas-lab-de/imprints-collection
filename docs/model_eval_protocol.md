# Model evaluation protocol

This protocol says how candidate models are run on the gold set and how they are scored. The gold set is described in `docs/gold_set_design.md`. The commands are in `docs/reproduce_goldset.md` (section "Model evaluation").

Prompts, schemas and the extraction strategy are fixed before the evaluation. The evaluation does not tune prompts. If a prompt changes, the run is a new run.

## 1. Questions

| # | Question | Answer used for |
|---|---|---|
| Q1 | Which model gives the best topics (POI v3, WZ 2025) per cost? | model for topics |
| Q2 | Which model gives the best addresses per cost? | model for addresses |
| Q3 | Single model or a two-model ensemble (ens2) per schema? | full-run setup |
| Q4 | Down to which level is P >= 0.8 for the chosen setup (out-of-fold)? | publish depth per schema |
| Q5 | What does the full run cost (GPU-hours or USD per 1M hosts)? | planning |

## 2. Evaluation set

### 2.1 Items

| Property | Value |
|---|---|
| Population | sites of the release (frame of 3,908,045 sites, plus the top-up from the final list) |
| Size | 1,869 items (core 600 + oversample 1,195 + stratum top-up 74), plus 18 top-up items |
| Design | two-phase probability sample |
| Weights | every item has an inclusion probability and a design weight `w_i = 1 / pi_i` (`design_weight`, `priority_stratum`, `strata`, `in_core`) |
| Input | same-day `ic fetch` text for models; same-day capture for labellers |

- All items are clean test items. Hosts used in earlier gold, pilot or prompt studies are out of the frame. There is no development part.
- No tuning on the gold set. The only choices made on it are the model choice and the depth cut-off (§2.3, §7).
- Hosts where `ic fetch` finds no imprint stay in the set. They measure the fetch step. The address model is not called for them, and the prediction is "no address". Hosts whose `site_status` is not live-like have no topic reference. They count in "no-address detection", not in topic scores.
- Top-up items have their own known `pi`. They enter all estimates with their weight.
- Folds: the items are split once into 5 folds, at random, stratified by priority stratum (strata with fewer than 5 items are pooled into one "rare" stratum per schema). The fold is stored in the sample file and frozen before any model score is looked at.
- Screen models: gemma4-31b-it and qwen38-27b chose the strata in the phase-1 screen. They are also candidates (§6).

### 2.2 Reference from three labellers

Source: gold records (schema v3) with `topic_labels {poi, wz}` and the address fields.

| Item | Rule |
|---|---|
| 50 calibration hosts | labelled by all three; consensus after discussion is the reference |
| about 375 hosts | labelled twice independently (primary + second labeller) |
| other hosts | labelled once; address suggestion shown, topics not pre-filled |
| Two labels differ | adjudicate; keep both raw labels in the file |

Annotator names, access and the adjudicator: to be set.

Agreement (reported):
- Addresses (main address only): agreement by location match (same measure as the model score) and exact match per field. Cohen's kappa for `site_status` and `imprint_present`. Both labellers saw the same suggestion, so address agreement is reported as "agreement with suggestions shown".
- Topics: share of equal path prefix at L1..L5 (WZ) and L1..L2 (POI). Krippendorff alpha on the top level as a second view.
- Agreement is the noise ceiling: a model score close to human agreement cannot be separated from label noise.

Items that only one labeller labelled have unknown noise. Scores on the double-labelled subset are reported as a check. That subset is not a random sample of the set, so it uses its weights and is labelled as a check.

### 2.3 Depth and depth cut-off

Gold is the finest level the labeller can decide. Scoring against a reference of depth d:
- For level L <= d: compare the model path with the reference path at L.
- For level L > d: the item does not count at L.
- A model answer that stops above d counts as not covered at the next level. A model answer deeper than d is cut to d.
- If two labellers stop at different depths, the default is the longest common prefix after adjudication (`depth_rule=lcp`).

Depth cut-off and model choice:
- **Cut-off by 5-fold cross-fitting.** For each fold, find the deepest level with P >= 0.8 on the other 4 folds. Apply that cut-off to this fold. The headline numbers are out-of-fold.
- **Model choice** is made on the full set and reported as such. With 3 to 5 candidates the selection effect is small.

## 3. Bias from the address suggestion

- Labellers see a model suggestion for the main address on every item. Topics are not pre-filled. The suggestion prompt is main-address-only.
- The suggestions come from `anthropic/claude-haiku-5.5` (through OpenRouter, `goldset/prefill.py`). It is not a candidate, so no candidate is marked "made the suggestion". The suggestion model is recorded per item (`prefilled_from`).

Risk: anchoring. A labeller who accepts the suggestion makes the reference equal to the suggestion. This favours models that make errors similar to the suggestion model. It lowers measured differences for the address task.

| Step | Content |
|---|---|
| Edit status | per item: was the suggestion accepted without change, edited, or replaced (final label compared with the suggestion) |
| Report 1 | the suggestion model vs. the reference, as a row in the address table |
| Report 2 | all models on two strata (weighted): items where the reference equals the suggestion; items where the labeller changed it |
| Report 3 | agreement of two labellers on the double-labelled items; both saw the same suggestion, so agreement is inflated |
| Paper | limitations text: "reference labels were seeded by model X" |

## 4. Candidates

| Model | Runs | POI reasoning | Note |
|---|---|---|---|
| `gemma4-31b-it` | address, poi_k30, poi_flat, wz | short | screen model (mark it) |
| `qwen38-27b` | address, poi_k30, poi_flat, wz | low | screen model (mark it) |
| `qwen-agentworld-35b-a3b` | address, poi_k30, poi_flat, wz | short | |
| `soofi-s-isar-preview` | address, poi_k30, poi_flat, wz | low | license caveat: the model page gives "None/Beta Preview: See HuggingFace"; state this in the paper |

All candidates are served by one OpenAI-compatible endpoint. The endpoint and key come from `MODEL_API_ENDPOINT` and `MODEL_API_KEY` (environment or `.env`, see `.env.template`). The model names are in `MODELS` in `src/ic/config.py`. Other open models (for example vLLM through `--extras local`) can be added as candidates with the same runs.

Runs per candidate (`evaluation/run_candidates.sh`):

| Run | Meaning |
|---|---|
| `address` | main address, JSON schema, no reasoning, imprint text only |
| `poi_k30` (default) | POI v3 prompt with retrieval of the 30 nearest nodes |
| `poi_flat` (variant) | POI v3 prompt with all nodes; measures the loss of k30 retrieval |
| `wz` | WZ 2025 prompt, no reasoning, 1,500 characters of site text per field |
| ens2 | level majority of two models, descends while both agree; built from stored single predictions, no extra model calls |

Paid APIs (optional, as a quality ceiling only): a spend limit per run and per UTC day applies, kept in a cost ledger. Run a 20-host pilot first and extrapolate the cost before the full set.

## 5. Metrics

acc@L counts abstention and early stop as wrong, P@L = precision among answers that reach L, cov@L = coverage among hosts whose reference reaches L.

All population figures are weighted Hajek ratio estimators: theta = sum(w_i y_i) / sum(w_i z_i), where z_i = 1 if the item counts for the metric (§6). The same tables are also made unweighted on the random core, and per stratum.

### 5.1 Topics (per schema, per level)

| Metric | Definition |
|---|---|
| P@L | correct / answered at L |
| acc@L | correct / hosts whose reference reaches L |
| cov@L | answered / hosts whose reference reaches L |
| deepest level with P >= 0.8 | highest L where P@L >= 0.8 (point estimate by default; the lower bound of the 95% CI is also reported); this is the publish depth, out-of-fold |
| rate of "no label" | hosts with an empty answer |

Levels: POI L1-L2, WZ L1-L5. Offline hosts and online-only hosts are reported separately. Per-class tables are by true label; the screen models are marked.

### 5.2 Addresses

Main address only. Other addresses on the imprint are only the flag `multi_address`.

| Metric | Definition |
|---|---|
| **Primary: location match** | model main address and reference main address are geocoded with Photon; a match is the same postcode + street, or a distance of at most 100 m. Weighted share of items with a match. The share within 1 km is a secondary view. |
| Field-level P/R/F1 | fields street, number, postcode, town, country; compared after normalisation; per field and micro-averaged |
| Exact main-address match | full main address exact after normalisation |
| No-address detection | on items with no address in the reference (`no_address_reason`): precision and recall of "no address"; false-address rate |
| Geocoding failures | share of addresses that Photon cannot place; scored by the normalised postcode + street match only |
| Evidence check | a predicted address must occur in the text (hallucination rate) |

### 5.3 Efficiency

| Metric | Definition |
|---|---|
| tokens in / out per host | mean and p95, from API usage |
| s/host | latency per call, median and p95; differences of a few seconds under server load are not reliable |
| failed replies | empty, malformed, truncated, timeout; rate per 1,000 calls; retries counted in cost |
| GPU-hours or USD per 1M hosts | measured throughput, or tokens x price for a paid API |
| ens2 cost | sum of both members |

## 6. Statistics

The set is a weighted two-phase sample. Population figures use the design weights. A plain host bootstrap and unweighted means are not valid for the population.

| Item | Method |
|---|---|
| Unit | item (all levels and fields of one item are resampled together) |
| Point estimate | Hajek ratio for every share, accuracy and P@L |
| CI | Taylor linearisation with phase-2 strata as strata and the finite population correction 1 - m_h / M_h (default); or a weighted, stratified bootstrap within the phase-2 strata (5,000 resamples, 95% percentile). Each table says which. The phase-1 component is treated as fixed; it is small for common strata and not small for rare ones. |
| Model differences | paired: Hajek ratio of the per-item difference |
| Unweighted check | plain share on the random core (SRS, 600 items), Wilson CI; the weighted headline must agree within its CI |
| Per stratum | unweighted, by the **true** (labelled) stratum; n shown; Wilson CI; rates only for n >= 10. Descriptive only. |
| Screen models | in a rare class an unweighted recall favours them; per-class comparisons are weighted and the screen models are marked |
| Paired tests | exact sign test and exact McNemar on unweighted core items, as a descriptive check; the weighted CI of the difference decides |
| Label noise | the main table is repeated on the double-labelled items with each of the two labels; the spread is reported |
| Multiple comparisons | primary tests: (1) acc@L* at the chosen level of each schema, (2) location match of the main address; Holm correction over them; all others are descriptive. The Kish effective n is reported. |
| Out-of-fold | publish-depth numbers are out-of-fold; CIs on the pooled out-of-fold results |

## 7. Decision rule

Run per task (POI, WZ, addresses). The steps are fixed before the labelled scores are looked at. The defaults below are the `ic.eval.score.Params` defaults; each one can be changed with `--set`.

1. **Filter.** Drop candidates with a failed-reply rate above 2% (`max_fail`) or P at the first level below 0.7 (`p_floor`).
2. **Pareto front.** Axes: quality Q (topics: weighted acc@L*; addresses: weighted location match within 100 m) vs. cost C. A candidate is on the front if no other candidate has both higher or equal Q and lower or equal C (one strict).
3. **Pick one point.** Best-Q candidate = B. Choose the cheapest front candidate with Q >= Q(B) - m, where the lower bound of the weighted paired CI of (Q - Q(B)) is not below -m.
4. **Margin m.** 2 points absolute (`margin=0.02`), or one standard error of B (`margin=se`).
5. **Single vs. ens2.** ens2 enters as a candidate with its summed cost. It wins only if it passes step 3 on the primary metric (`target=acc`), or on hosts labelled at depth with P >= 0.8 per cost (`target=depth`).
6. **Publish depth.** For the chosen setup, L* = deepest level with P >= 0.8 by 5-fold cross-fitting.
7. **Ties and shifts.** If the choice changes between the two labels of double-labelled items, between the weighted and the core-only result, or when the screen models are left out of the per-class view, the report says so (`tie_rule=report`). The final choice is to be decided by the authors.

## 8. How to run

Predictions: `evaluation/run_candidates.sh` (§4; commands in `docs/reproduce_goldset.md`). Output: `datasets/evaluation/preds/<stage>/`, logs in `datasets/evaluation/logs/<stage>/`. `evaluation/runs_table.py` writes a table of all runs (hosts, failures, tokens, time).

Scorer: package `ic.eval`. It makes no model calls; it reads stored predictions only. Run from the repository root.

```
PYTHONPATH=src python3 -m ic.eval --sample datasets/goldset/phase2/gold_sample.jsonl \
  --labels 'datasets/goldset/gold/labels/L*.jsonl' --assignment datasets/goldset/gold/assignment.jsonl \
  [--adjudication <adjudicated.jsonl>] [--geocodes <geocodes.jsonl>] [--texts datasets/evaluation/gold_inputs.jsonl] \
  --preds datasets/evaluation/preds/full [--preds datasets/evaluation/preds/topup] \
  [--manifest <cost fields per prediction set>] [--params params.json] [--set key=value ...] [--run-id <id>]
```

- Candidates: every prediction file is one candidate. Grouping is by task and schema (`poi`, `wz`, `address`). A new model needs only a new file. ens2 is built from stored single predictions (`--set ens2_pairs=all` or a list `["A+B"]`).
- Parameters: `method=taylor` (or `bootstrap`, `B=5000`); `adjudication_scope=disagreements`, `depth_rule=lcp`, `unresolved_topic=lcp`; `min_precision=0.8`, `depth_criterion=point` (or `ci`); `max_fail=0.02`, `p_floor=0.7`; `margin=0.02` (or `se`); `target=acc` (or `depth`); `tie_rule=report` (or `cheaper`, `better`); `ens2_pairs=top2`; `fpc=phase2` (`none` = with-replacement variance).
- `--geocodes`: a JSONL file `{key|address, lat, lon}` for the 100 m match, made with a Photon instance. Without it, the location match falls back to postcode + street.
- Output: `results/score/<run-id>/` with `params.json`, `summary.json`, `summary.md` (decision per task), `agreement.md`, `reference/`, `scores/all.csv` (all estimates with SE and CI, long format), `scores/topics_<schema>.md`, `scores/depth_<schema>.md`, `scores/addresses.md`, `scores/efficiency.md`, `scores/per_stratum.md`, `scores/pareto_<schema>.csv`, `paired.md`.
- Before the gold labels exist: `--gold <one label per host>` or `--refs <reference file>` replaces `--labels`.
- Estimator check: `PYTHONPATH=src python3 -m ic.eval.simulate --sample datasets/goldset/phase2/gold_sample.jsonl --reps 2000 --boot-reps 300 --B 1000` (bias and CI coverage on the real design). Tests: `pytest tests/test_eval_*.py`; the long simulation tests run with `IC_RUN_SLOW=1`.

## 9. Paper tables and figures

| Item | Content |
|---|---|
| Table A | reference quality: agreement per task |
| Table B | topics: weighted P@L, acc@L, cov@L per level, per model and run (POI k30 and flat), with CIs; out-of-fold publish depth |
| Table C | addresses: location match within 100 m (primary), field F1, no-address detection |
| Table D | efficiency: tokens, s/host, failed replies, cost per 1M hosts |
| Figure 1 | Pareto plot quality vs. cost per task, chosen point marked, CIs as bars |
| Figure 2 | P by level for the chosen setup with the 0.8 line (publish depth) |
| Figure 3 | single vs. ens2: P vs. coverage by level |
