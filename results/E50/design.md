# E50 extraction prompt study: design

Status 2026-11-10, phase 1. Owner: E50 agent, branch `E50-prompt-study`. Language: Simplified Technical English.

## 1. Goal

Fix the prompts for the full run (topics POI v3, WZ 2025, addresses) before gold labelling ends and before the model evaluation E52 picks the model.

Constraints:
- The strategy is fixed (`docs/extraction_strategy.md`): POI flat, node names "English (Deutsch)"; WZ retrieve k30, node text = path; input landing page + imprint; one model per schema by default.
- The final model is not known. A prompt must work on all candidate models, not on one model only.
- The full run has millions of imprints. Tokens per host, calls per host and failed replies are part of the result, not a side note.
- E52 does not tune prompts. E50 gives E52 one fixed prompt per task, plus one reasoning setting per model.

## 2. Facts found before the design (probes 2026-11-10)

| Fact | Effect on the design |
|---|---|
| Innkube serves qwen38-27b, gemma4-31b-it, qwen-agentworld-35b-a3b, soofi-s-isar-preview (+ embedding, reranker). | Models: gemma, qwen (main); agentworld (robustness: MoE, 3B active, other family member). soofi is out (E49: weakest, prose instead of JSON). |
| gemma4 thinks only with `reasoning_effort` low/medium/high. With no `reasoning_effort` it does not think. | E49 "gemma think" was no reasoning (26 out tokens). Native gemma reasoning was never tested. E50 tests it. |
| gemma low, medium and high gave the same reasoning length on a probe. | gemma levels: none, short, low. medium/high only in a spot check. |
| qwen38 accepts `reasoning_effort` none, low, medium, xhigh (default). "high" gives HTTP 400. | qwen levels: none, short, low, medium, default (= xhigh = E49 "think"). |
| agentworld: any `reasoning_effort` other than none gives the same long reasoning (~700 tokens on a 3-line probe). | agentworld levels: none, short, default. |
| The server has prefix caching (`prompt_tokens_details.cached_tokens`). | A static prompt prefix (instructions + POI list first, site text last) can make most of the 24k POI prompt tokens a cache hit. This is a cost factor ("layout"). |
| Guided JSON (`response_format` json_schema) works on qwen and agentworld. On gemma it can run away: it writes whitespace until `max_tokens` when the schema requires a key that the prompt does not ask for. `disable_any_whitespace` has no effect. | The schema must match the answer format of the prompt exactly. Runaways count as failed replies. `max_tokens` stays bounded. |
| The LiteLLM proxy returns cached answers for repeated requests; its cache key ignores some extra fields (`structured_outputs`, `chat_template_kwargs`). | Use only standard fields (`response_format`, `reasoning_effort`). Take latency only from calls that are not cache hits. |

## 3. Data

| Set | Hosts | Refs | Use |
|---|---|---|---|
| dev (phase 1) | E49 dev 200 (`results/E49/dev_hosts.txt`) | `results/E49/refs/poi_v3.jsonl`, `results/E49/refs/wz.jsonl` | topic screening (now) |
| dev2 | 300 new non-gold hosts (E51) | E51 POI, WZ, address refs | phase 2 |
| dev (phase 2) | E49 dev 200 + dev2 300 = 500 | + E51 address refs for the E49 hosts | address and joint factors, combination, selection |
| held-out | E49 held-out 100 + heldout2 200 = 300 | E49 held-out refs + E51 refs | one final check of the chosen prompts, after selection; never used to select |

Input form: E49 inputs come from rendered gold captures (text cut to 6,000 characters per field). The full run uses crawl text. E51 hosts come from crawl text, so phase 2 checks that the choice holds on the crawl form (compare the E49 200 and the dev2 300 parts).

## 4. Factors

B = baseline level (current prompt). All factors except reasoning are prompt or request properties that must be the same for all models. Reasoning is a per-model API setting.

### 4.1 Topic factors (phase 1, screening on dev 200)

| ID | Factor | Levels | Notes |
|---|---|---|---|
| R | reasoning | none; short (`begruendung` field in the JSON, max 2 sentences); low; medium; default | per model (section 2). B = E49 choice: qwen default (POI), gemma short. |
| L | instruction language | de (B); en | all fixed prompt text; site text and node names unchanged |
| W | task wording | base (B); minimal (one task sentence, no rules); guide (the decision steps of the gold guideline 5.2/5.3: activity the site presents, homepage first, deepest node that clearly fits, no guessing a leaf, nothing fits -> KEINE) | guide is not tuned on dev errors; it copies the guideline the gold labellers use |
| F | output format | free JSON (B; parse first `{...}`); json_object (`response_format` json_object); schema (`response_format` json_schema, strict, `id` restricted to the offered ids + KEINE) | schema makes unresolvable ids impossible |
| S | few-shot | 0 (B); 4 (`results/E49/fewshot.jsonl`, fictional sites, no dev host) | |
| T | input budget (characters per field, landing and imprint) | 6000 (B); 3000; 1500 | E49 inputs are cut at 6000; longer budgets need crawl text (phase 2 on dev2) |
| P | prompt layout | site first (B: user = site + candidate list + answer format); list first (system = instructions + candidate list + answer format; user = site) | list first gives a static prefix for prefix caching (POI: ~22k of 24k tokens) |

### 4.2 Address factors (phase 2, need E51 refs)

| ID | Factor | Levels |
|---|---|---|
| A | address output | main (one address or null, with `no_address_reason`); list (all addresses of parties in the imprint, each with role and `main` flag, plus `no_address_reason`) |
| AL, AW, AF, AS, AR | language, wording, format, few-shot, reasoning | as for topics; wording "guide" = guideline 3.1-3.4 in short |
| AT | address input | imprint only (B); imprint + landing (joint call sees both) |
| AB | imprint budget | 6000; 3000; 1500 characters |

Address output schema (both levels; fixes the old schema, which could not say "no address"):

```json
{"addresses": [{"street": "", "number": "", "postcode": "", "town": "", "country": "",
                "role": "operator|operator_other_site|representative|editor|agency|host|other", "main": true}],
 "no_address_reason": null}
```
`no_address_reason` is null, `no_imprint` or `imprint_without_address`; `addresses` is then empty. Level "main" allows at most one address. Fields follow the gold guideline 3.3 (copy as written, postcode digits only, country empty if not named).

### 4.3 Call layout (phase 2)

| Level | Calls per host | Content |
|---|---|---|
| separate (B) | 3 (+1 embedding) | POI flat; WZ retrieve k30; address |
| topics joint + address separate | 2 (+1 embedding) | one call returns POI id + WZ id; one address call |
| joint | 1 (+1 embedding) | one call returns POI id, WZ id and addresses |

Joint prompts list the POI candidates (static, first) and the 30 WZ candidates of the host (after the site text). One JSON object answers all parts.

## 5. Sequential plan

Stage | Set | What | Runs (approx.)
---|---|---|---
A | dev 200 | reasoning levels per model, POI and WZ, base prompt | qwen 5 + gemma 3 + agentworld 3 levels x 2 schemas = 22 (6 cached from E49)
B | dev 200 | one factor at a time from the stage-A base of each model (L, W x2, F x2, S, T x2, P = 9 variants), POI and WZ, gemma + qwen + agentworld | 9 x 3 x 2 = 54
gate | | phase 1 ends; report |
C | dev 500 | address factors (A, AL, AW, AF, AS, AR, AT, AB), one at a time, same models | ~12 x 3 = 36 (address calls are short)
D | dev 500 | call layout (3 levels) with the stage-B/C winners | 3 x 3 = 9
E | dev 500 | combine all winners; confirm each kept change against the base on 500 hosts (paired); drop a change that does not hold | ~4 x 3
F | held-out 300 | one run of the final prompts (+ base for reference), all three models. No change after this. | ~6 x 3

Screening (A, B) runs on 200 hosts and keeps a change only with the rule in section 7. Stage E re-tests the kept changes together on 500 hosts. This limits the number of runs to about 150 and protects against chance wins from the screening.

Concurrency: one run at a time per model (separate deployments), 6 workers each (E49: 8). Responses are cached on disk (`datasets/E49/cache`, shared with E49, key = full request body), so the E49 baseline runs are not sent again.

## 6. Metrics

Topics (per schema, per model; script `scripts/E50/compare.py`):
- POI: acc@2 (primary; abstention and stopping above L2 count as wrong; over all scored hosts), P@2, cov@2; also acc@1, acc@3.
- WZ: acc@3 (primary), P@3, cov@3; acc and P per level 1-5.
- failed replies: error, empty or unparsable reply, reply cut at `max_tokens`.
Addresses (`scripts/E50/addr_score.py`, adapter for the E51 format):
- main address: field-level P/R/F1 (street, number, postcode, town, country) and exact match of (street, number, postcode, town) after normalisation.
- all addresses: matched by normalised key, then field-level P/R/F1 micro.
- no-address detection: P/R/F1 of "no address" on hosts whose ref has no address; false-address rate.
- evidence: share of predicted main addresses whose postcode and street occur in the input text (hallucination proxy).
Cost (per host): calls, prompt tokens, cached prompt tokens, completion tokens (incl. reasoning), s/host (from calls that were not cache hits).

Cost unit: C = (prompt tokens - cached prompt tokens) + 10 x completion tokens ("prefill-equivalent tokens"). The factor 10 comes from E49 latencies (gemma b vs qwen b: ~600 more output tokens cost ~3.7 s, 24k input tokens cost ~15 s at the same load). It is a GPU-time proxy, not a price. Tables also show the raw counts.

## 7. Selection rule (dev only)

Statistics: paired over hosts. d = metric(variant) - metric(base) on the same hosts. 95% CI from a host bootstrap (5,000 resamples, seed 1); for pooled values the bootstrap resamples hosts and keeps all models of a host together. Exact two-sided sign test on the per-host hit of the primary metric.

Pooled quality: mean d over the two main models (gemma, qwen). agentworld is a guard only.

Rule "cheapest non-inferior" (per factor, per task):
1. A level is **admissible** if: its failed-reply rate is <= 1% on each model; pooled d of the primary metric >= -0.01 (point) and its 95% CI lower bound >= -0.04 (non-inferiority margin, about the CI half-width at n = 200); and no model (gemma, qwen, agentworld) has d < -0.03.
2. Among admissible levels, a level that is **better** (pooled CI lower bound > 0, or sign test p < 0.05 with d > 0) is chosen if its cost C is at most 1.5 x base cost, or if d >= +0.02 per doubling of C.
3. Else choose the admissible level with the **lowest cost C**, if it saves at least 10% of C. Ties in C (within 10%): keep the base (no change without evidence).
4. For reasoning (per model): the same rule, but per model (not pooled); margin as in 1.
5. Precision guard: P@L* (L* = 2 POI, 3 WZ) must not drop by more than 0.03 (point estimate).
6. If the same level is chosen for POI and WZ, or if the difference between the two choices is not significant, use one common level (one prompt style for both schemas).

Phase-2 margins are the same; the CIs are narrower at n = 500. The final held-out check reports d and CI against base and does not change the choice. If the held-out d of the primary metric is below -0.03 for a model, the report says so and the lead decides.

Why this rule: the full run makes cost differences large (millions of hosts), but small quality differences on 200 hosts are noise. The rule takes a cheaper prompt when it is not measurably worse, and a more expensive prompt only when it is measurably better.

## 8. Risks and limits

- 200 hosts: one host = 0.005; CI half-width about 0.03-0.05 for paired differences. Screening can miss gains below 3 points. Stage E re-tests on 500 hosts.
- The E49 base prompts were tuned on the dev 200 (E49 rules were dropped after held-out, D52). Variants are not tuned on dev errors.
- References: dev 200 by two Opus passes (A=B 89.5%); E51 refs by agents too. Label noise lowers all scores but is the same for all variants.
- Factor interactions: OFAT screening does not see them. Stage E tests the combination.
- Server load changes latency; s/host is indicative. Tokens are exact.
- Few-shot: only 4 fictional examples exist. A negative result says "these 4 examples do not help", not "few-shot does not help".
