# E52-model-evaluation: protocol (draft)

Status: draft 2026-11-10. Written before gold labelling ends. Items marked "Open:" need the lead or the user.
Place in the order of work: strategy (`docs/extraction_strategy.md`, fixed) -> prompt study E50 (fixes prompts) -> gold labelling (1,000 hosts, three labellers) -> **E52** -> full run on all imprints.

## 1. Questions
| # | Question | Answer used for |
|---|---|---|
| Q1 | Which model gives the best topics (POI v3, WZ 2025) per cost? | model for topics |
| Q2 | Which model gives the best addresses per cost? | model for addresses |
| Q3 | Single model (default, D54) or ens2 per schema? | full-run setup |
| Q4 | Down to which level is P >= 0.8 for the chosen setup? | publish depth per schema |
| Q5 | What does the full run cost (GPU-hours or USD per 1M hosts)? | planning, paper |

Prompts, schemas and strategy are fixed before E52. E52 does not tune prompts. If a prompt changes, the run is a new run.

## 2. Evaluation set
### 2.1 Hosts
| Part | Hosts | Use |
|---|---|---|
| Main | the 700 gold hosts that are not in the E49 sets | main scores, decisions |
| Tuned | up to 300 gold hosts used in E49 (`results/E49/dev_hosts.txt` 200, `results/E49/heldout/hosts.txt` 100) | reported separately |
| All | 1,000 | secondary table only |

- Rule: the E49 prompts, rules and options were tuned on the 200 dev hosts. The 100 held-out hosts were used for decisions (D52, D54) too. Both are not clean for model choice.
- Check before use: how many of the 300 E49 hosts are in the final 1,000 gold hosts. Use the real intersection. The split file is `results/E52/split.json` (hosts, part), made once and frozen.
- Hosts with `site_status` not live-like have no topic reference. They count in "no-address detection", not in topic scores.
- Open: accept the 700 as the main set, or draw a fresh smaller check set? (Default: 700.)

### 2.2 Reference from three labellers
Source: gold records with `topic_labels {poi, wz}` (schema_version 2) and the address fields.

| Item | Rule |
|---|---|
| 50 calibration hosts | labelled by all three; consensus after discussion is the reference |
| about 200 hosts | labelled twice independently (primary + second labeller) |
| other hosts | labelled once from scratch (D15) |
| Two labels differ | adjudicate (see below); keep both raw labels in the file |

Open: who adjudicates (lead, third labeller, or the user), and does adjudication cover only the 200 double-labelled hosts? (Default: the other labeller of L1-L3 who has capacity, rule R1-R7 of `results/E49/labelling_spec.md` as base.)

Agreement (report in the paper):
- Addresses: exact match of main address (street, number, postcode, town) and field-level agreement. Cohen's kappa for `site_status` and `imprint_present`.
- Topics: share of equal path prefix at L1..L5 (WZ) and L1..L2 (POI), as in E49 (A=B 89.5% on dev). Krippendorff alpha on the top level as a second view.
- Use agreement as the noise ceiling: a model score close to human agreement cannot be separated from label noise.

Hosts that only one labeller labelled have unknown noise. Report scores on the double-labelled subset as a check.

### 2.3 Depth (D51)
Gold is the finest level the labeller can decide. Scoring against a reference of depth d:
- For level L <= d: compare model path with reference path at L.
- For level L > d: the host does not count at L (same as E49 "hosts whose reference reaches L").
- A model answer that stops above d counts as not covered at the next level. A model answer deeper than d is cut to d.
- Open: if two labellers stop at different depths, use the shallower (default, safe) or the deeper agreed prefix? Default: the longest common prefix, after adjudication.

## 3. Bias from the address suggestion
Facts:
- Labellers saw a model suggestion for addresses on all 1,000 hosts (D24 B, `--prefill all`).
- Prefill = `e21-v1+filter1` in `datasets/gold/prefill.jsonl`, made by model **qwen-agentworld-35b-a3b** (field `source.model`; innkube). Filter removes duplicates, rows without postcode and third-party-only rows (1,254 -> 950 rows).
- Topics have no prefill. The 11-class topic field in the prefill is not used in E52.

Risk: anchoring. A labeller who accepts the suggestion makes the reference equal to the suggestion. This favours qwen-agentworld and models that make similar errors. It lowers measured differences for the address task.

What E52 does:
| Step | Content |
|---|---|
| Per-host edit log | from the gold tool: was the suggestion accepted without change, edited, or replaced? (Open: does the tool log this? If not, compare final label with prefill offline.) |
| Report 1 | prefill model vs reference, as a row in the address table, marked "made the suggestion" |
| Report 2 | all models on two strata: hosts where the reference equals the suggestion; hosts where the labeller changed it |
| Report 3 | agreement of two labellers on the double-labelled hosts: both saw the same suggestion, so agreement is inflated (guideline section 9) |
| Rule | the prefill model is not allowed to win on address quality alone if its lead is smaller than the lead on the "changed" stratum would imply; state this in the text. Open: use this rule or only report? (Default: only report, no rule.) |
| Paper | limitations text: "reference labels were seeded by model X; scores of X are an upper-biased estimate" |

Do not run qwen-agentworld in E52 as a normal candidate without this mark. Open: include it as a candidate? (Default: yes, marked.)

## 4. Candidates
| Group | Models | Cost basis | Note |
|---|---|---|---|
| Innkube (config `MODELS` in `src/ic/config.py`) | `qwen38-27b` (reasoning_effort none via extra_body), `gemma4-31b-it`, `qwen3-next-80b-a3b-instruct` | no USD; measure s/host and tokens | endpoint `MODEL_API_ENDPOINT`; used in E49; qwen-agentworld-35b-a3b is the prefill model (check it is served) |
| Open models on FAITH Slurm | Open: list (size classes, e.g. 7-14B, about 30B, 70B+; vLLM through `--extras local`) | GPU-hours (A100/H100 per node, price Open) | docs: https://faith.pages.fim.uni-passau.de/public-docs/slurm/ |
| Paid API (optional) | Open: which models, if any | USD from token counts | limit $20 per run, $30 per UTC day |

Rules for paid runs (CLAUDE.md):
- Before each run: read `docs/cost_ledger.csv` (create on first paid run), add the day's total, estimate cost = tokens x price. Stop if run > $20 or day > $30.
- Log every paid run: date UTC, run id, model, hosts, tokens in/out, USD.
- First run a 20-host pilot; extrapolate cost before the full 1,000 hosts. 1,000 hosts at E49 token sizes: WZ about 1.5k tokens/host in; POI v3 with `--node-lang both` about 24k in per host per model (ens2 = 48k).
- Open: any paid API at all? (Default: no. Innkube and FAITH only, as in D49.) Open: is a paid model worth it as a quality ceiling only (not a deployment option)?

Variants per candidate and schema:
| Variant | Meaning |
|---|---|
| single (default, D54) | one model per schema, predict to the leaf, publish to the deepest level with P >= 0.8 |
| ens2 | level majority of two models, descends while both agree (adaptive depth) |
| Pairs for ens2 | Open: all pairs of the top-k single models, or only the E49 pair gemma + qwen? (Default: the best two singles after the single-model run, plus gemma + qwen.) |

Prompt, input (landing page + imprint) and options (WZ retrieve k30, no rules; POI flat, reasoning on, `--node-lang both`) are those fixed by E50.

Address task: one model per run. Open: do addresses and topics use the same model? (The decision rule runs per task; the final choice may be one model for both if the cost saving is real. Open for the lead.)

## 5. Metrics
Notation as in E49: acc@L counts abstention and early stop as wrong, P@L = precision among answers that reach L, cov@L = coverage among hosts whose reference reaches L.

### 5.1 Topics (per schema, per level)
| Metric | Definition |
|---|---|
| P@L | correct / answered at L |
| acc@L | correct / hosts whose reference reaches L |
| cov@L | answered / hosts whose reference reaches L |
| deepest level with P >= 0.8 | highest L where P@L >= 0.8 and the lower bound of the 95% CI at L is also reported; this is the publish depth (D54) |
| rate of "no label" | hosts with empty answer |
Levels: POI L1-L2 (L3 for ens2 depth report), WZ L1-L5. Offline hosts and online-only hosts are reported separately as in E49.
Open: use point estimate P >= 0.8 (as E49) or lower CI bound >= 0.8 for the publish depth? (Default: point estimate; CI shown.)

### 5.2 Addresses
| Metric | Definition |
|---|---|
| Field-level P/R/F1 | fields street, number, postcode, town, country; address matched by normalised key (postcode + street + number), then fields compared; per field and micro-averaged |
| Address-level P/R/F1 | full address exact after normalisation |
| Main-address accuracy | `main_address_index` points to the reference main address (roles operator, operator_other_site, representative, editor) |
| No-address detection | on hosts with no address in the reference (`no_address_reason`): precision and recall of "no address"; false-address rate |
| Role accuracy | role of matched main address (secondary) |
| Geocoded distance (optional) | Photon geocoder (`~/opt/photon`) for model and reference address; share within 100 m and within 1 km; use only if geocoding is part of the full run. Open: include? (Default: yes for the top 3 models only.) |
Evidence check: a predicted address must occur in the text (hallucination rate; E21 found 987/1,000 verbatim).

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
| Item | Method |
|---|---|
| Unit | host (all levels and fields of one host are resampled together) |
| CI | paired host bootstrap, 5,000 resamples, seed 1 (as E49), 95% percentile; for each model-vs-model difference and each metric |
| Paired tests | exact sign test on host-level win/loss (as E49) for acc@L; McNemar (exact) for binary correct/not on the same hosts; for P@L use bootstrap only (different denominators) |
| Cost ratios | bootstrap of the ratio of means |
| Agreement noise | repeat the main table on the double-labelled hosts with each of the two labels; report the spread |
| Multiple comparisons | many models x levels x fields. Declare primary tests: (1) acc@L* at the chosen level of each schema, (2) main-address accuracy; all others are descriptive. Holm correction over the primary tests. State that p-values of descriptive tests are not corrected. With 700 hosts a difference below about 3-4 points is not resolved (E49: 99 hosts exclude only about 4 points). |
| Stability | one run per model; Open: repeat the top 3 models twice to measure run-to-run noise (temperature 0 assumed)? (Default: yes for the finalists.) |
| Tuned 300 | same tables; no tests used for the decision |

## 7. Decision rule
Run per task (POI, WZ, addresses). Steps are fixed before the labelled scores are looked at.

1. **Filter.** Drop candidates with failed-reply rate > Open: X% (default 2%) or P at the first level < Open: floor (default 0.7).
2. **Pareto front.** Axes: quality Q (topics: acc@L*; addresses: field-level F1 micro) vs cost C (GPU-hours or USD per 1M hosts). A candidate is on the front if no other candidate has both higher or equal Q and lower or equal C (one strict).
3. **Pick one point.** Best-Q candidate = B. Choose the cheapest front candidate with Q >= Q(B) - m, where m is the margin and the paired bootstrap lower bound of (Q - Q(B)) is not below -m.
4. **Margin m.** Open: value of m. Proposal: m = 2 points (absolute) for acc@L* and F1; it is about the size the 700 hosts can resolve and about the human-agreement noise. Alternative: m = one bootstrap standard error of B.
5. **Single vs ens2.** ens2 enters as a candidate with its summed cost. It wins only if it passes step 3 on the primary metric. If the ens2 gain is only higher P at lower cov and acc (as E49 POI: P@2 .914 but acc@2 -3 to -5 points), compare the final product: number of hosts labelled at depth with P >= 0.8 (hosts x level) per cost. Open: which target does the lead want, high precision at lower coverage or high coverage? This decides step 5.
6. **Publish depth.** For the chosen setup, L* = deepest level with P >= 0.8 on the 700 main hosts; check on the 300 tuned hosts.
7. **Ties and shifts.** If the choice changes when the 300 tuned hosts are added, or between the two labels of double-labelled hosts, report it and take the cheaper option only if the lead agrees. Open.

Output of the rule is written as a new decision card (D-number by lead) and in `docs/decisions.md`.

## 8. Outputs
Location: `results/E52/` (untracked data stays out of git except small summaries; follow repo practice for `results/`).
| File | Content |
|---|---|
| `results/E52/split.json` | frozen host split (main, tuned) |
| `results/E52/reference/{poi,wz,address}.jsonl` | adjudicated reference + raw labels + agreement stats |
| `results/E52/preds/<task>/<model>/<variant>.jsonl` | predictions, one per host |
| `results/E52/scores/{topics,addresses,efficiency}.md` and `.csv` | tables by part (main, tuned, all) |
| `results/E52/paired.md` | bootstrap CIs and tests |
| `results/E52/pareto_<task>.csv` + `.pdf` | front data and figure |
| `results/E52/bias_address.md` | prefill bias tables (section 3) |
| `results/E52/summary.md` | verdict, choice, caveats |
| `docs/cost_ledger.csv` | paid runs only |
| `scripts/E52/` | scoring and plot scripts; one command per output |

Paper tables and figures:
| Item | Content |
|---|---|
| Table A | reference quality: agreement per task |
| Table B | topics: P@L, acc@L, cov@L per level, per model and variant (main 700) |
| Table C | addresses: field F1, main-address accuracy, no-address detection |
| Table D | efficiency: tokens, s/host, failed replies, cost per 1M hosts |
| Figure 1 | Pareto plot quality vs cost per task, chosen point marked, tuned 300 as open markers |
| Figure 2 | P by level for the chosen setup with the 0.8 line (publish depth) |
| Figure 3 | single vs ens2: P vs coverage by level |
| Text | bias statement (section 3), multiple-comparison note, margin rule |
Per `honest-current-numbers`: report only current counts; no comparison to the old 3.2M.

## 9. Order of steps
1. Freeze split and metrics code; test scorers on E49 refs (numbers must match `results/E49/poi3c/summary.md`).
2. Build the reference from the labels (after labelling ends); compute agreement.
3. 20-host pilot per candidate (cost and failure check; paid: ledger first).
4. Full runs on 1,000 hosts, all candidates, single variants.
5. ens2 runs from stored single predictions (no extra model calls).
6. Throughput run on FAITH.
7. Scores, tests, Pareto, decision card for the lead.

## 10. Open items (summary)
1. Accept the 700 main set (or a fresh check set).
2. Who adjudicates; adjudication scope.
3. Depth rule when labellers stop at different levels.
4. Does the tool log suggestion accepted/edited?
5. Prefill bias: report only, or add a rule.
6. Include qwen-agentworld as a (marked) candidate.
7. List of FAITH open models and GPU price.
8. Paid API models: none, or ceiling only.
9. ens2 pairs.
10. Same model for addresses and topics, or one per task.
11. Publish-depth criterion: point estimate or CI bound.
12. Geocoded distance: include or not.
13. Shadow price for innkube.
14. Planning figure for number of hosts.
15. Repeat finalists for run-to-run noise.
16. Filter thresholds (X% failed, P floor).
17. Margin m.
18. Precision vs coverage target (decides ens2).
19. Tie rule at step 7.
