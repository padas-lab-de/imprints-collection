# E52-model-evaluation: protocol (draft)

Status: draft v0.2, 2026-11-12. Matches the gold set methodology v0.3 (`docs/gold_set_design.md`, new E53 gold set). Written before gold labelling ends. Items marked "Open:" need the lead or the user. Items marked "pending Dnn" depend on an open decision card.
Place in the order of work: strategy (`docs/extraction_strategy.md`, fixed) -> prompt study E50 (fixes prompts) -> gold set E53 (two-phase sample of 1,869 items, three labellers; D60 D) -> **E52** -> full run on all imprints.

## 1. Questions
| # | Question | Answer used for |
|---|---|---|
| Q1 | Which model gives the best topics (POI v3, WZ 2025) per cost? | model for topics |
| Q2 | Which model gives the best addresses per cost? | model for addresses |
| Q3 | Single model (default, D54) or ens2 per schema? | full-run setup |
| Q4 | Down to which level is P >= 0.8 for the chosen setup (out-of-fold, D58 A)? | publish depth per schema |
| Q5 | What does the full run cost (GPU-hours or USD per 1M hosts)? | planning, paper |

Prompts, schemas and strategy are fixed before E52. E52 does not tune prompts. If a prompt changes, the run is a new run.

## 2. Evaluation set
### 2.1 Items
The gold set is the new E53 set (`docs/gold_set_design.md` v0.3). It replaces the E12 sample.

| Property | Value |
|---|---|
| Population | sites of the release (r4 + E40 r2, 3,908,045 sites, plus the r5 top-up; D55 A) |
| Size | 1,869 items (D60 D, target (h)): core 600 random + oversample 1,195 + stratum top-up 74 (`datasets/E53/phase2/gold_sample.jsonl`, `results/E53/phase2_draw.md`). |
| Design | two-phase probability sample (D57 A): phase 1 screens 20,000 random frame sites with two models; phase 2 draws a random core (600), a coverage oversample (1,195) and a stratum top-up (74), D60 D |
| Weights | every item has an inclusion probability and a design weight `w_i = 1 / pi_i` (`design_weight`, `priority_stratum`, `strata`, `in_core`) |
| Input | same-day `ic fetch` text for models; same-day capture for labellers (D56 A) |

- All items are clean test items. All hosts used in earlier gold, pilot or prompt studies (E8, E12, E49, E51) are out of the frame. There is no "Main / Tuned" split and no development part.
- No tuning on the gold set. The only choices made on it are the model choice and the depth cut-off (section 2.3, section 7).
- Hosts where `ic fetch` finds no imprint stay in the set. They measure the fetch step. The address model is not called for them (E50 rule), and the prediction is "no address". Hosts with `site_status` not live-like have no topic reference. They count in "no-address detection", not in topic scores.
- Items from the r5 top-up (about 9) have their own known `pi`. They enter all estimates with their weight.
- Folds: the items are split once into 5 folds, at random, stratified by priority stratum (strata with fewer than 5 items are pooled into one "rare" stratum per schema, so every fold gets a fair share). The split file is `results/E52/split.json` (item, fold, weight), made once and frozen before any model score is looked at (gold design step 16).
- Screen models: the two models of the phase-1 screen (assumed gemma4-31b-it and qwen38-27b) are likely E52 candidates. Section 6 and section 8 say how to report this.

### 2.2 Reference from three labellers
Source: gold records with `topic_labels {poi, wz}` (schema_version 2) and the address fields.

| Item | Rule |
|---|---|
| 50 calibration hosts | labelled by all three; consensus after discussion is the reference |
| about 200 hosts | labelled twice independently (primary + second labeller) |
| other hosts | labelled once; address suggestion shown (D24 B), topics not pre-filled |
| Two labels differ | adjudicate (see below); keep both raw labels in the file |

Annotator names, access and dates are not set yet. Open: who adjudicates (lead, third labeller, or the user), and does adjudication cover only the 200 double-labelled hosts? (Default: the other labeller of L1-L3 who has capacity, rule R1-R7 of `results/E49/labelling_spec.md` as base.)

Agreement (report in the paper):
- Addresses (main address only): agreement by location match (D12 A, same measure as the model score) and exact match per field. Cohen's kappa for `site_status` and `imprint_present`. Both labellers saw the same suggestion, so address agreement is reported as "agreement with suggestions shown".
- Topics: share of equal path prefix at L1..L5 (WZ) and L1..L2 (POI), as in E49 (A=B 89.5% on dev). Krippendorff alpha on the top level as a second view.
- Use agreement as the noise ceiling: a model score close to human agreement cannot be separated from label noise.

Items that only one labeller labelled have unknown noise. Report scores on the double-labelled subset as a check. That subset is not a random sample of the set, so use its weights and label it as a check.

### 2.3 Depth (D51) and depth cut-off (D58 A, user 2026-11-12)
Gold is the finest level the labeller can decide. Scoring against a reference of depth d:
- For level L <= d: compare model path with reference path at L.
- For level L > d: the item does not count at L (same as E49 "hosts whose reference reaches L").
- A model answer that stops above d counts as not covered at the next level. A model answer deeper than d is cut to d.
- Open: if two labellers stop at different depths, use the shallower (default, safe) or the deeper agreed prefix? Default: the longest common prefix, after adjudication.

Depth cut-off and model choice (D58 A, user 2026-11-12):
- **Cut-off by 5-fold 5-fold cross-validation (cross-fitting).** For each fold, find the deepest level with P >= 0.8 (D54) on the other 4 folds. Apply that cut-off to this fold. Report the out-of-fold numbers. The headline numbers are out-of-fold.
- **Model choice** is made on the full set and reported as such. With 3 to 5 candidates the selection effect is small.
- Option B (fixed split, 200 items for cut-off and choice, 800 for reported numbers) is simpler but has 20% fewer test items.

## 3. Bias from the address suggestion
Facts:
- D24 B: labellers see a model suggestion for the main address on every item. Topics are not pre-filled. The suggestion prompt is main-address-only.
- The suggestion model is recorded per item (`prefilled_from`).
- The old E21 suggestions (`e21-v1+filter1`, `datasets/gold/prefill.jsonl`) were made by **qwen-agentworld-35b-a3b** for the E12 items. That is an E50 model. The E12 items are not in the new set. The new suggestion run is step 10 of the gold design. Its model is chosen there.
- The suggestion model must not be an E52 candidate. If it is one, its address score is reported as upward-biased ("made the suggestion"). Resolved (D61 A): the new suggestions come from Haiku 5.5 via OpenRouter, a non-candidate; no candidate gets the mark.

Risk: anchoring. A labeller who accepts the suggestion makes the reference equal to the suggestion. This favours the suggestion model and models that make similar errors. It lowers measured differences for the address task.

What E52 does:
| Step | Content |
|---|---|
| Per-item edit log | from the gold tool: was the suggestion accepted without change, edited, or replaced? (Open: does the tool log this? If not, compare final label with the suggestion offline.) |
| Report 1 | the suggestion model vs reference, as a row in the address table, marked "made the suggestion" if it is a candidate |
| Report 2 | all models on two strata (weighted): items where the reference equals the suggestion; items where the labeller changed it |
| Report 3 | agreement of two labellers on the double-labelled items: both saw the same suggestion, so agreement is inflated (guideline section 9) |
| Rule | the suggestion model is not allowed to win on address quality alone if its lead is smaller than the lead on the "changed" stratum would imply; state this in the text. Open: use this rule or only report? (Default: only report, no rule.) |
| Paper | limitations text: "reference labels were seeded by model X; scores of X are an upper-biased estimate" |

qwen-agentworld is a candidate if innkube serves it (it is served, 2026-11-13); unmarked, because it did not make the new suggestions.

## 4. Candidates
| Group | Models | Cost basis | Note |
|---|---|---|---|
| Innkube (config `MODELS` in `src/ic/config.py`) | `qwen38-27b` (reasoning_effort none via extra_body), `gemma4-31b-it`, `qwen3-next-80b-a3b-instruct` | no USD; measure s/host and tokens | endpoint `MODEL_API_ENDPOINT`; used in E49. gemma4-31b-it and qwen38-27b are also the screen models (mark them). qwen-agentworld-35b-a3b (E50 model) made the old E21 suggestions; it is served and is a candidate. `qwen3-next-80b-a3b-instruct` is not served on innkube (`/v1/models`, 2026-11-13; A1), so E52 does not run it |
| Open models on FAITH Slurm | Open: list (size classes, e.g. 7-14B, about 30B, 70B+; vLLM through `--extras local`) | GPU-hours (A100/H100 per node, price Open) | docs: https://faith.pages.fim.uni-passau.de/public-docs/slurm/ |
| Paid API (optional) | Open: which models, if any | USD from token counts | limit $20 per run, $30 per UTC day |

Rules for paid runs (CLAUDE.md):
- Before each run: read `docs/cost_ledger.csv` (create on first paid run), add the day's total, estimate cost = tokens x price. Stop if run > $20 or day > $30.
- Log every paid run: date UTC, run id, model, hosts, tokens in/out, USD.
- First run a 20-host pilot; extrapolate cost before the full gold set. Token sizes: WZ about 1.5k tokens/host in; POI flat about 25k in per host per model (ens2 = 2x); POI k30 about 0.21 of flat.
- Open: any paid API at all? (Default: no. Innkube and FAITH only, as in D49.) Open: is a paid model worth it as a quality ceiling only (not a deployment option)?

Variants per candidate and schema:
| Variant | Meaning |
|---|---|
| single (default, D54) | one model per schema, predict to the leaf, publish to the deepest level with P >= 0.8 (out-of-fold cut-off, section 2.3) |
| POI retrieve k30 (default) | POI prompt with k30 retrieval, about 0.21 of the flat cost (user 2026-11-12) |
| POI flat (variant) | POI prompt with all nodes, about 25k tokens per host; measures the loss of k30 on gold (E50: -0.027 acc@2 on dev) |
| ens2 | level majority of two models, descends while both agree (adaptive depth) |
| Pairs for ens2 | Open: all pairs of the top-k single models, or only the E49 pair gemma + qwen? (Default: the best two singles after the single-model run, plus gemma + qwen.) |

Prompt, input (landing page + imprint) and options are those fixed by E50 (`results/E50/final_config.md`, `docs/extraction_strategy.md`): POI retrieve k30 (default; flat is the variant above); WZ retrieve k30, no reasoning, 1500 chars per field; address mode main, JSON schema, no reasoning, imprint text only. Input is the same-day `ic fetch` text (D56 A).

Address task: one model per run. Open: do addresses and topics use the same model? (The decision rule runs per task; the final choice may be one model for both if the cost saving is real. Open for the lead.)

## 5. Metrics
Notation as in E49: acc@L counts abstention and early stop as wrong, P@L = precision among answers that reach L, cov@L = coverage among hosts whose reference reaches L.

All population figures below are weighted Hajek ratio estimators: theta = sum(w_i y_i) / sum(w_i z_i), where z_i = 1 if the item counts for the metric (section 6). Counts in the definitions are weighted sums. The same table is also made unweighted on the random core, and per stratum (section 6).

### 5.1 Topics (per schema, per level)
| Metric | Definition |
|---|---|
| P@L | correct / answered at L |
| acc@L | correct / hosts whose reference reaches L |
| cov@L | answered / hosts whose reference reaches L |
| deepest level with P >= 0.8 | highest L where P@L >= 0.8 and the lower bound of the 95% CI at L is also reported; this is the publish depth (D54). Headline: out-of-fold cut-off (D58 A A, section 2.3) |
| rate of "no label" | hosts with empty answer |
Levels: POI L1-L2 (L3 for ens2 depth report), WZ L1-L5. Offline hosts and online-only hosts are reported separately as in E49. Per-class tables are by true label; mark the screen models (section 6).
Open: use point estimate P >= 0.8 (as E49) or lower CI bound >= 0.8 for the publish depth? (Default: point estimate; CI shown.)

### 5.2 Addresses
Main address only (user 2026-11-12; the pipeline returns one address per site). Other addresses on the imprint are only the flag `multi_address`.

| Metric | Definition |
|---|---|
| **Primary: location match** (D12 A) | model main address and reference main address are geocoded with Photon (`~/opt/photon`); a match is the same postcode + street, or a distance of at most 100 m. Report the weighted share of items with a match. Also report the share within 1 km as a secondary view. |
| Field-level P/R/F1 (secondary) | fields street, number, postcode, town, country; fields compared after normalisation; per field and micro-averaged |
| Exact main-address match (secondary) | full main address exact after normalisation |
| No-address detection | on items with no address in the reference (`no_address_reason`): precision and recall of "no address"; false-address rate |
| Role accuracy | role of the main address (secondary) |
| Geocoding failures | share of addresses that Photon cannot place; report them, and score them by the normalised postcode + street match only |
Evidence check: a predicted address must occur in the text (hallucination rate; E21 found 987/1,000 verbatim).
Geocoding is part of the full run, so it is part of the address score for all candidates, not only the top 3.

### 5.3 Efficiency
| Metric | Definition |
|---|---|
| tokens in / out per host | mean and p95, from API usage |
| s/host | model latency per call, median and p95; note server load (E49 caveat: differences of a few s are not reliable). Repeat timing on a quiet endpoint, same time of day for all models. |
| failed replies | empty, malformed, truncated, timeout; rate per 1,000 calls; retries counted in cost |
| GPU-hours per 1M hosts | FAITH: measured throughput with batching (hosts/s on N GPUs) -> hours x GPUs |
| USD per 1M hosts | paid API: tokens x price; innkube: not priced (Open: assign a shadow price per GPU-hour so innkube and FAITH compare?) |
| ens2 cost | sum of both members |
Cost for the full run uses the number of hosts with an imprint (Open: lead gives the planning figure; "millions" now).
Throughput measurement on FAITH is a separate small run (500 hosts, fixed batch size), not the same as quality runs.

## 6. Statistics
The set is a weighted two-phase sample. Population figures use the design weights. Plain host bootstrap and unweighted means are not valid for the population.

| Item | Method |
|---|---|
| Unit | item (all levels and fields of one item are resampled together) |
| Point estimate | Hajek ratio theta = sum(w_i y_i) / sum(w_i z_i) for every share, accuracy and P@L (gold design §4.6) |
| CI | Taylor linearisation with phase-2 strata as strata and the finite population correction 1 - m_h / M_h; or a weighted, stratified bootstrap that resamples items within the phase-2 strata (5,000 resamples, seed 1, 95% percentile). Say which one a table uses. The phase-1 component is treated as fixed; it is small for common strata and not small for rare ones (state this in the paper). |
| Model differences | paired: Hajek ratio of the per-item difference, same linearisation or same bootstrap draws for both models |
| Unweighted check | plain share on the random core (SRS, 600 items), Wilson CI; the weighted headline must agree within its CI |
| Per stratum | unweighted, by the **true** (labelled) stratum, not the screen prediction; n shown; Wilson CI; rates only for n >= 10, counts below. Descriptive only. |
| Screen models | gemma4-31b-it and qwen38-27b chose the strata. In a rare class, an unweighted recall favours them (gold design §4.7). Compare models per class with weights, and mark the screen models in every per-class table. |
| Paired tests | exact sign test on win/loss and exact McNemar are valid on unweighted items only. Use them as a descriptive check on the core; the weighted CI of the difference decides. For P@L use the weighted CI only (different denominators). |
| Cost ratios | bootstrap of the ratio of means (cost is per item; weight the means the same way) |
| Agreement noise | repeat the main table on the double-labelled items with each of the two labels; report the spread |
| Multiple comparisons | many models x levels x fields. Declare primary tests: (1) acc@L* at the chosen level of each schema, (2) location match of the main address; all others are descriptive. Holm correction over the primary tests. State that p-values of descriptive tests are not corrected. The effective sample size is lower than the item count because weights vary (report the Kish effective n); a difference of a few points may not be resolved (E49: 99 hosts exclude only about 4 points). |
| Stability | one run per model; Open: repeat the top 3 models twice to measure run-to-run noise (temperature 0 assumed)? (Default: yes for the finalists.) |
| Out-of-fold | publish-depth numbers are out-of-fold (section 2.3); CIs are computed on the pooled out-of-fold results |

## 7. Decision rule
Run per task (POI, WZ, addresses). Steps are fixed before the labelled scores are looked at.

1. **Filter.** Drop candidates with failed-reply rate > Open: X% (default 2%) or P at the first level < Open: floor (default 0.7).
2. **Pareto front.** Axes: quality Q (topics: weighted acc@L*; addresses: weighted location match within 100 m) vs cost C (GPU-hours or USD per 1M hosts). A candidate is on the front if no other candidate has both higher or equal Q and lower or equal C (one strict).
3. **Pick one point.** Best-Q candidate = B. Choose the cheapest front candidate with Q >= Q(B) - m, where m is the margin and the lower bound of the weighted paired CI of (Q - Q(B)) is not below -m. Rare-class results of the screen models do not enter Q unweighted.
4. **Margin m.** Open: value of m. Proposal: m = 2 points (absolute) for acc@L* and location match; check against the CI width of the weighted estimate and the human-agreement noise. Alternative: m = one bootstrap standard error of B.
5. **Single vs ens2.** ens2 enters as a candidate with its summed cost. It wins only if it passes step 3 on the primary metric. If the ens2 gain is only higher P at lower cov and acc (as E49 POI: P@2 .914 but acc@2 -3 to -5 points), compare the final product: number of hosts labelled at depth with P >= 0.8 (hosts x level) per cost. Open: which target does the lead want, high precision at lower coverage or high coverage? This decides step 5.
6. **Publish depth (D58 A, user 2026-11-12).** For the chosen setup, L* = deepest level with P >= 0.8 by 5-fold 5-fold cross-validation (cross-fitting): the cut-off comes from 4 folds and is applied to the 5th; report the out-of-fold numbers. Option B: cut-off and model choice on 200 items, numbers on 800.
7. **Ties and shifts.** If the choice changes between the two labels of double-labelled items, between the weighted and the core-only result, or when the screen models are left out of the per-class view, report it and take the cheaper option only if the lead agrees. Open.

Output of the rule is written as a new decision card (D-number by lead) and in `docs/decisions.md`.

## 8. Outputs
Location: `results/E52/` (untracked data stays out of git except small summaries; follow repo practice for `results/`).
| File | Content |
|---|---|
| `results/E52/split.json` | frozen item list with fold (5 folds), design weight, priority stratum, `in_core` |
| `results/E52/reference/{poi,wz,address}.jsonl` | adjudicated reference + raw labels + agreement stats |
| `results/E52/preds/<task>/<model>/<variant>.jsonl` | predictions, one per host |
| `results/E52/scores/{topics,addresses,efficiency}.md` and `.csv` | tables: weighted population, unweighted core check, per true stratum (screen models marked) |
| `results/E52/paired.md` | bootstrap CIs and tests |
| `results/E52/pareto_<task>.csv` + `.pdf` | front data and figure |
| `results/E52/bias_address.md` | suggestion bias tables (section 3) |
| `results/E52/summary.md` | verdict, choice, caveats |
| `docs/cost_ledger.csv` | paid runs only |
| `scripts/E52/` | scoring and plot scripts; one command per output |

Paper tables and figures:
| Item | Content |
|---|---|
| Table A | reference quality: agreement per task |
| Table B | topics: weighted P@L, acc@L, cov@L per level, per model and variant (POI k30 and flat), with CIs; out-of-fold publish depth |
| Table C | addresses: location match within 100 m (primary), field F1, no-address detection |
| Table D | efficiency: tokens, s/host, failed replies, cost per 1M hosts |
| Figure 1 | Pareto plot quality vs cost per task, chosen point marked, CIs as bars |
| Figure 2 | P by level for the chosen setup with the 0.8 line (publish depth) |
| Figure 3 | single vs ens2: P vs coverage by level |
| Text | suggestion-bias statement (section 3), screen-model note (section 6), multiple-comparison note, margin rule |
Per `honest-current-numbers`: report only current counts; no comparison to the old 3.2M.

## 9. Order of steps
1. Freeze folds, weights and metrics code; test scorers on E49 refs (unweighted; numbers must match `results/E49/poi3c/summary.md`); test the weighted estimators on a simulated sample with known truth.
2. Build the reference from the adjudicated gold file (gold design step 14); compute agreement.
3. 20-host pilot per candidate (cost and failure check; paid: ledger first).
4. Full runs on all gold items, all candidates, single variants (POI k30 and flat).
5. ens2 runs from stored single predictions (no extra model calls).
6. Throughput run on FAITH.
7. Scores, tests, Pareto, decision card for the lead.

## 10. Open items (summary)
1. Gold set size and coverage depth (card D60, after the phase-1 screen).
2. D58: 5-fold cross-validation (cross-fitting) (A, recommended) or fixed 200/800 split (B).
3. Who adjudicates; adjudication scope.
4. Depth rule when labellers stop at different levels.
5. Does the tool log suggestion accepted/edited?
6. Resolved (D61 A): the address suggestion model is Haiku 5.5 via OpenRouter (`anthropic/claude-haiku-5.5`), a non-candidate, so no candidate gets the "made the suggestion" mark.
7. Resolved: qwen-agentworld-35b-a3b is a candidate if innkube serves it (served 2026-11-13, E52 runs). It made no suggestions for the new set, so it is not marked.
8. List of FAITH open models and GPU price.
9. Paid API models: none, or ceiling only.
10. ens2 pairs.
11. Same model for addresses and topics, or one per task.
12. Publish-depth criterion: point estimate or CI bound.
13. Shadow price for innkube.
14. Planning figure for number of hosts.
15. Repeat finalists for run-to-run noise.
16. Filter thresholds (X% failed, P floor).
17. Margin m.
18. Precision vs coverage target (decides ens2).
19. Tie rule at step 7.
20. CI method per table: Taylor linearisation or weighted stratified bootstrap.

## 11. How to run the scorer
Code: `src/ic/eval/` (package `ic.eval`), command `ic score`. No model calls; it reads stored predictions only. Run from the repository root.

```
ic score --sample datasets/E53/phase2/gold_sample.jsonl \
  --labels 'datasets/gold/labels/L*.jsonl' --assignment datasets/E53/gold/assignment.jsonl \
  [--adjudication <adjudicated.jsonl>] [--geocodes <geocodes.jsonl>] [--texts <gold_inputs.jsonl>] \
  --preds datasets/E52/preds/full/poi3 --preds datasets/E52/preds/full/address \
  [--manifest <cost fields per prediction set>] [--params params.json] [--set key=value ...] [--run-id <id>]
```

- Candidates: every prediction file (E50 run format) is one candidate. Grouping is by task and schema (`poi`, `wz`, `address`). A new model needs only a new file. ens2 is built from stored single predictions (`--set ens2_pairs=all` or a list `["A+B"]`).
- Parameters (open items): `--set` overrides one field of `ic.eval.score.Params`. The defaults are the protocol defaults: `method=taylor` (or `bootstrap`, `B=5000`, item 20); `adjudication_scope=disagreements`, `depth_rule=lcp`, `unresolved_topic=lcp` (items 3, 4); `min_precision=0.8`, `depth_criterion=point` (or `ci`, item 12); `max_fail=0.02`, `p_floor=0.7` (item 16); `margin=0.02` (or `se`, item 17); `target=acc` (or `depth`, item 18); `tie_rule=report` (or `cheaper`, `better`, item 19); `ens2_pairs=top2` (item 10); `fpc=phase2` (phase 1 fixed, as in section 6; `none` = with-replacement variance).
- Output: `results/E52/score/<run-id>/` with `params.json`, `summary.json`, `summary.md` (decision per task), `agreement.md`, `reference/` (per-item reference and how it was built), `scores/all.csv` (all estimates with SE and CI, long format), `scores/topics_<schema>.md`, `scores/depth_<schema>.md`, `scores/addresses.md`, `scores/efficiency.md`, `scores/per_stratum.md`, `scores/pareto_<schema>.csv`, `paired.md`.
- Before the gold labels exist: `--refs results/E49/refs/poi_v3.jsonl` (E49 reference) or `--gold <one label per host>` replaces `--labels`.
- Estimator check: `python -m ic.eval.simulate --sample datasets/E53/phase2/gold_sample.jsonl --reps 2000 --boot-reps 300 --B 1000` (bias and CI coverage on the real design). Tests: `pytest tests/test_eval_*.py`; long simulation: `pytest -m slow`.
