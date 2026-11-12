# Gold set design: a stratified probability sample of the German imprints release

Status: **v0.3 draft (2026-11-12)**, experiment E53-gold-set-redraw. This version defines a NEW 1,000-item gold set. It replaces the E12 sample of v0.2. Four design cards are open (D55-D58). Every section that depends on an open card names the card and the option. The option in the text is the recommended one ("pending Dnn, recommended").

Decisions this version uses: D12 A (location match by geocoding is the primary address metric), D14 A (labels from the rendered site, frozen in a capture), D15 C as amended (three labellers, about 200 double labels), D17 B (1,000 items, no head-to-head comparison of site groups), D24 B (a model suggestion on every item, addresses only), D49 (one main label + up to 2 extra labels), D51 B (topic labels at the finest decidable level), D54 A (single model per schema; publish depth from the gold set), user 2026-11-12 (main address only).

## What changed from v0.2, and why

| v0.2 (E12 sample) | Problem | v0.3 |
|---|---|---|
| Frame: the seed list `seed_hosts.txt.gz` (6.56M hosts). | The dataset is not the seed list. The release contains only sites with an imprint. Results on the seed list do not speak for the release. | Frame: the release population (r4 + E40 r2, 3,908,045 sites) minus all used hosts (§2). |
| 420 of 1,000 items are negatives (219 no imprint, 201 not live), all from the core. | These items have no address and no topic. They are useless for extraction and topic scores. | The frame has only release sites. Negatives come only from site change and from fetch failures on the day of capture (§3). |
| 300 items were used in E49 prompt development. E50 tuned on them. | They are not clean test items. E52 had to split 700 vs 300. | All used hosts are excluded (§2.2). All 1,000 items are clean. |
| Topic strata use the old 11 classes (D5). | The tasks are now POI v3 (2 levels) and WZ 2025 (5 levels). | Strata: POI top-level classes, WZ sections, address hard cases (§4). |
| Strata for site age, technology, rendering need, operator type. | They need new fetches for the whole screen. The paper does not compare site groups (D17 B). | Not strata. The capture still records them as descriptive tags (§3.3). |
| D15 text: "no model pre-labels". | D24 B reversed this on 2026-10-26. | Model suggestions for addresses on every item; topics not pre-filled (§5). |
| Location match within 250 m. | D12 says 100 m. | 100 m, as in D12 (§1). |

## History

- **v0.1** (2026-10-23, E8-gold-strata-pilot): defined diversity dimensions and unit-tested detectors (`src/ic/gold/detectors.py`). Screened a pilot of 1,000 seed-list hosts.
- **v0.2** (2026-10-24, E12): screened 10,000 seed-list hosts and drew a 1,000-item two-phase sample (700 random core + 300 oversample, T = 30) with Horvitz-Thompson weights (`datasets/E12/gold_sample.jsonl`). E17 captured the items, E18 assigned them to three labellers, E21 made address suggestions. Only 4 tool-test labels exist (`datasets/gold/labels/L1.jsonl`).
- The full v0.1 and v0.2 text, with the E12 screening prevalences and the quota table, is in git history (`git log -p docs/gold_set_design.md`, last v0.2 commit before E53).
- v0.3 reuses the v0.2 sampling method (§4), the capture method (§3) and the labelling tool (§7). It changes the frame, the strata and the input form.

## Summary

- **Population**: the sites of the German Imprints release (pending D55). The gold set evaluates the release pipeline on what it publishes.
- **Size**: 1,000 items, plus a small r5 top-up (about 9 items, §2.3).
- **Design** (pending D57): two-phase probability sample. Phase 1 screens a random 20,000 frame sites with the fixed E50 prompts on stored crawl text. Phase 2 draws a random core of 600 and an oversample of 400. The oversample gives each rare POI class, WZ section and address hard case about 25 items where the population allows. Every item has a known inclusion probability.
- **Input** (pending D56): on one day per item, `ic fetch` makes the model input and a gold capture makes the labeller input.
- **Labels**: site status, imprint found, main address, POI v3 label, WZ 2025 label. Three labellers. 50 calibration items, about 200 double-labelled items, adjudication.
- **Use** (pending D58): all 1,000 items are test items. The publish depth is set by 5-fold cross-fitting.

## 1. Purpose and tasks

The gold set measures how well the release pipeline extracts the data that the release publishes. The unit is one site (one canonical host). The set serves four tasks.

| Task | Gold label | Primary metric | Secondary metrics |
|---|---|---|---|
| Site status, imprint found | `site_status`; `imprint_present`; `imprint_url` | imprint found: recall and precision of the fetch step against `imprint_present` | `site_status` agreement |
| Main address | the main address (street, number, postcode, town, country, P.O. box) or `no_address_reason` | location match by geocoding (D12 A): gold and prediction are geocoded with Photon; a match is the same postcode + street, or a distance of at most 100 m | field-level exact and normalised match; no-address precision and recall; false-address rate on items without an address |
| POI topic (`topics/poi_v3.jsonl`, 2 levels, 8 top-level classes) | one main node + up to 2 extra nodes, at the finest decidable level | acc@L and P@L per level (L1, L2) | lenient score with extra labels; coverage |
| WZ 2025 topic (`topics/wz2025.jsonl`, 5 levels, 22 sections A-V) | one main node + up to 2 extra nodes, at the finest decidable level | acc@L and P@L per level (L1-L5) | lenient score with extra labels; coverage |

Rules:
- **Main address only** (user 2026-11-12). The pipeline returns one address per site. The gold set scores that address. The label records other postal addresses on the imprint only as the flag `multi_address` (§5.1).
- **Distance threshold.** D12 sets 100 m. v0.2 used 250 m. That was an error in v0.2. v0.3 uses 100 m.
- **Finest decidable level** (D51 B). A labeller stops at an inner node when the site text does not decide the child. A host counts at level L only if its label reaches L (`docs/model_eval_protocol.md` §2.3).
- **One main + up to 2 extra labels** per schema (D49). The strict score uses the main label. The lenient score accepts the main label or an extra label.
- **Operator type and the old 11-class topic** are not evaluation targets in v0.3. See §7 for the tool change.

## 2. Frame (pending D55, recommended option A)

### 2.1 Population

The target population U is the set of sites in the release. Today U is r4 after the E40 r2 parking filter:
- File: `/home/dinzinger/GitHub/imprints-collection-e35/datasets/E40/r2/canonical_sites_after_filter.txt`.
- Count: 3,908,045 sites, one canonical host per line.
- Origin: r4 has 4,020,137 sites (`.../E31/r4/E31_out/canonical_sites.txt`). E40 r2 drops 112,092 parked sites (`.../E40/r2/flagged_sites.tsv`).

All these sites had an imprint at crawl time. So the frame has no "no imprint" sites by construction.

### 2.2 Exclusions

A site is out of the frame if it was used before in any gold, pilot or prompt study. The match key is the canonical host, lower case, with a leading `www.` removed. Both variants (`x.de`, `www.x.de`) are excluded.

| List | Hosts | Location | Note |
|---|---|---|---|
| Old gold set (pre-E12) | 1,000 | `evaluation/gold_standard_data.jsonl` | in the repo |
| E8 pilot | 1,000 | `datasets/E8/hosts.txt` | **on aspe only** |
| E12 screened hosts | 10,000 | `datasets/E12/` | **on aspe only**; contains the E12 sample |
| E12 gold sample | 1,000 | `datasets/gold/assignment.jsonl`, `datasets/gold/prefill.jsonl` | subset of the E12 screen |
| E49 dev + held-out | 300 | `results/E49/dev_hosts.txt`, `results/E49/heldout/hosts.txt` | subset of the E12 sample |
| E51 dev2 + heldout2 | 500 | `results/E51/dev2_hosts.txt`, `results/E51/heldout2_hosts.txt` | from the E16 seed crawl |
| E50 dev 500 + held-out 300 | (800) | E49 ∪ E51 | no new hosts |

The union has at most 12,500 hosts. Many of them are not in the release, so the frame loses fewer. The frame builder reports how many hosts of each list it removes.

Frame: F0 = U minus the union of the lists. N0 = |F0|.

### 2.3 Top-up when r5 is final

r5 will add the E48 Shopify sites (crawl stopped at about 84% on 2026-11-11, about 34k imprint sites so far) and 88 E34r4 sites. A later filter can also drop sites. No other crawls are planned (D47).

Rules:
1. **Added sites.** F_A = sites in r5 and not in r4/E40 r2, minus the exclusion lists. N_A = |F_A|. Draw a simple random sample of n_A = round(1,000 x N_A / N0) sites from F_A (about 9 items). Each has pi = n_A / N_A. These items get no phase-1 screen and no oversample. They are labelled like all other items.
2. **Dropped sites.** A drawn F0 site that r5 removes leaves the set. It is not replaced.
3. **Weights stay exact.** F0 and F_A are two frame strata with known designs. Removing dropped sites is a domain restriction: it does not change any selection probability.

Estimator for the r5 population U5 = (F0 ∩ U5) ∪ F_A, with y_i the item's score and w_i = 1 / pi_i:

    total(y)  =  sum over drawn i in F0 ∩ U5 of w_i y_i   +   sum over drawn i in F_A of (N_A / n_A) y_i

Option B (wait for r5, then draw once) avoids the top-up but waits for a crawl that is stopped.

## 3. Input and capture (pending D56, recommended option A)

### 3.1 Two inputs from the same day

The release pipeline extracts from `ic fetch` text: the resiliparse `main_content` of the static HTML of three pages (main, kontakt, impressum). The crawl keeps no HTML. The crawl is weeks old, and sites change.

For each item, on one day:
1. **Model input.** Run `ic fetch` (the release fetch code) from the crawl VM. The output is the model input for all tasks. It is the same input form as the release.
2. **Labeller input.** Run the gold capture (§3.2) on the same day. Labellers label the site from the capture.

Rules:
- An item where `ic fetch` finds no imprint stays in the set. It measures the fetch step. The models get what the pipeline would get. With no imprint text, the address model is not called (E50 rule), and the prediction is "no address".
- The labeller labels the site, not the `ic fetch` output. A site that changed since the crawl is labelled as it is on the capture day.
- The capture runs from a different IP than the crawl VM if possible (for example a FAITH node). Reason: in E8 and E12, Strato answered 503 to the crawl VM for 578 of 642 hosts. A block of the crawl VM is a fetch failure, not a property of the site. `ic fetch` stays on the crawl VM, so that fetch failures match the release.
- If `ic fetch` and the capture run on different days for an item, the item gets a flag `input_day_mismatch`.

Option B (stored crawl text for models, fresh capture as help for labellers) mixes two dates. Option C (rendered DOM for both, as E49) gives clean labels, but the input differs from the release.

### 3.2 Per-item archive

One directory per item, `datasets/E53/gold/<host>/`, made by `scripts/gold/e17_capture.py` (adapted, §7).

| Artifact | How | Why |
|---|---|---|
| `ic_fetch.jsonl` | `ic fetch` record of the item: main, kontakt, impressum with url, title, `main_content`, `content_language` | model input (D56 A) |
| `landing.static.html`, `imprint.static.html`, response headers | plain HTTP GET | static vs. rendered comparison |
| `landing.dom.html`, `imprint.dom.html` | Playwright Chromium, `networkidle` + 2 s, `page.content()` | labeller reference text |
| `landing.txt`, `imprint.txt` | `document.body.innerText` of the rendered page | check of verbatim address fields |
| `landing.png`, `imprint.png` | full-page screenshot, 1280 px wide, up to 20,000 px tall | labeller view; image-only addresses |
| `imprint.pdf` | the file, if the imprint is a PDF | PDF imprints |
| `meta.json` | UTC timestamps of the capture and of `ic fetch`, final URLs, redirect chains, HTTP status, user agent, viewport, browser version, cookie-banner action, capture IP group | provenance |

Rules:
- One capture per item, with a timestamp. The labeller labels from the screenshot and DOM text. The labeller opens the live site only when the capture lacks something, and records this (`used_live_site`, `comment`).
- Cookie banners: the capture clicks a "reject" or "only necessary" button from a fixed list of labels. Otherwise it leaves the banner. `meta.json` records which.
- No WARC (as E17).
- Release (D13 B): HTML, DOM text and screenshots are released with the gold set.

### 3.3 Descriptive tags

The E8 detectors run on each capture after labelling: technology family, rendering need, imprint location, obfuscation, image-only candidate. Wayback first-capture year is added for site age. These tags describe the set. They are not strata, and they do not change weights. Error analysis can use them.

## 4. Sampling design (pending D57, recommended option A)

### 4.1 Overview

| Phase | What | Size |
|---|---|---|
| 1 | Simple random sample S1 from F0, screened on stored crawl text | n1 = 20,000 |
| 2a | Random core: the first 600 sites of a seeded permutation of S1 | 600 |
| 2b | Coverage oversample: rarest stratum first, from S1 minus the core | 400 |
| Top-up | SRS from the r5 additions (§2.3) | about 9 |

Code base: `src/ic/gold/sampling.py` (§7). Seeds are fixed and recorded before each draw.

### 4.2 Phase 1: screen

Input: the stored crawl record of each site in S1 (`/home/dinzinger/imprints-release-20261109/crawls/<source>/<vm>/<dir>/imprints_batch*.jsonl.gz`). No new fetches. Cost: innkube only, no paid API.

Per site:
- **Two models with the fixed E50 prompts** (`docs/extraction_strategy.md`, `results/E50/final_config.md`): POI (retrieve k30, default since 2026-11-12), WZ (retrieve k30, 1500 chars per field), address (mode main, JSON schema). Prompts are not changed for the screen. Which two models: §9 (assumed gemma4-31b-it and qwen38-27b).
- **Text detectors** (`src/ic/gold/detectors.py`) on the imprint text: `find_addresses` and `address_flags` (P.O. box, several addresses, AT or CH postcode and country words, no postal address).
- **Free fields**: TLD, crawl source, `content_language`, text length.

Output per site: one record with both models' predictions, the detector flags and the free fields.

### 4.3 Strata

A site in S1 is a **member** of every stratum below that it meets. One site can be a member of many strata.

| Group | Strata | Membership rule |
|---|---|---|
| POI | the 8 top-level classes of POI v3 | either model predicts the class (L1 of its path) |
| WZ | the 22 sections A-V of WZ 2025 | either model predicts the section |
| Address | `addr:at`, `addr:ch` | either model's main address, or a detector address, has an AT or CH postcode or country |
| Address | `addr:po_box` | detector or either model finds a P.O. box |
| Address | `addr:none` | imprint text present, and neither model nor detector finds a postal address |
| Address | `addr:multi` | detector finds 2 or more distinct postal addresses |
| Address | `lang:non_de` | `content_language` of landing page or imprint is not German |
| Frame (as needed) | TLD (`.at`, `.ch`, other non-`.de`); crawl source | from the frame files, exact |

**Union of two models.** A site is a member of a model-based stratum if either model predicts it. So no single model decides the oversample. Frame strata are added only if a source or TLD would otherwise get fewer than about 10 items.

### 4.4 Phase 2: core and oversample

1. **Priority stratum.** Each site gets the rarest stratum it is a member of (fewest members in S1). A site in no stratum gets `other:none`, which is never oversampled.
2. **Core.** The first n0 = 600 sites of a seeded permutation of S1. The core is a simple random sample of F0 on its own.
3. **Oversample.** Rarest stratum first: draw at random from the not-yet-selected sites whose priority stratum is h. Stop when the marginal count of h in the sample (core and extras, all memberships) reaches T, or when the pool is empty.
4. **Choice of T.** Take the largest T in 20-30 for which the oversample fits into 400 items. Spend leftover items in later passes at T+1, T+2, ... (rarest first). The rule is fixed before the draw. Target: T about 25.
5. **Shortfall.** If a stratum has fewer than T members in S1, all of them are drawn (phase-2 probability 1). The quota table records this.

### 4.5 Inclusion probabilities and weights

Within priority stratum h, the m_h selected sites are a uniform random subset of the M_h sites of S1 in h. Conditional on the realised M_h:

    pi_i  =  (n1 / N0)  x  (m_h / M_h)          w_i  =  1 / pi_i

Each item stores `priority_stratum`, `strata` (all memberships), `pi_phase1`, `pi_phase2`, `inclusion_probability`, `design_weight`, `frame_stratum` (F0 or F_A) and `in_core`.

### 4.6 Estimators and reporting

| Figure | Estimator | 95% CI |
|---|---|---|
| Population figure (share, accuracy, P@L) | Hajek ratio: theta = sum(w_i y_i) / sum(w_i z_i), z_i = 1 if the item counts for the metric | Taylor linearisation, phase-2 strata as strata, with finite population correction 1 - m_h / M_h |
| Model difference (population) | Hajek ratio of the paired item difference | same linearisation |
| Check on the core | plain share over the 600 core items (SRS) | Wilson |
| Per stratum | unweighted, by the **labelled** (true) stratum; n shown | Wilson; rates only for n >= 10, counts below |

Rules:
- Population figures are the headline numbers. Per-stratum figures are descriptive.
- The linearised variance treats the M_h as fixed. With n1 = 20,000 the phase-1 component is small for common strata. It is not small for rare strata. The paper says so.
- Per-stratum figures use the label's true stratum (POI class, WZ section, address case). They do not use the screen prediction.

### 4.7 Known biases

- **Strata come from model predictions.** True members of a rare class that both screen models missed enter only through the core, with a large weight. Weighted estimates stay unbiased (every frame site has pi > 0), but their variance is high.
- **Unweighted per-class scores favour the screen models.** In a rare class, most sample items are items that a screen model predicted as that class. So an unweighted recall for that class is biased upward for the screen models. Report per-class model comparisons weighted, or mark the screen models.
- **Models and detectors decide strata only, never labels.** Labellers do not see strata or screen predictions. A mis-stratified item changes only its weight. Its label records its true stratum.
- **Stale screen input.** The screen uses crawl text that is weeks old. The label uses a fresh capture. A site that changed may sit in the wrong stratum. This affects weights, not labels.
- **Conditional probabilities.** pi is conditional on the realised M_h and on the screen outputs.

## 5. Labelling protocol

### 5.1 Label schema

Tool schema v2 (`src/ic/gold/annotate/schema.py`). Fields used in v0.3:

| Field | Values |
|---|---|
| `site_status` | live, unreachable, http_error, parked, redirect_other_domain, not_a_website |
| `imprint_present`, `imprint_url`, `imprint_location` | as in `docs/annotation_guideline.md` §2 |
| `addresses` + `main_address_index` | the main address with all fields, verbatim from the capture (town as written, D12) |
| `no_address_reason` | site_dead, no_imprint, imprint_without_address |
| `flags` | multi_address, po_box, obfuscated, non_dach, ... |
| `topic_labels.poi`, `topic_labels.wz` | main node, 0-2 extra nodes, confidence, note; POI `online_only` |
| `used_live_site`, `capture_problem`, `comment`, `seconds_spent`, `prefilled_from` | provenance |

Main address rules: guideline §3.2. Other addresses: the labeller sets `multi_address` and may list them. Listing them is not required (main-address-only evaluation). The guideline needs this change (§7).

### 5.2 Labellers and workload

| Step | Items | Labels |
|---|---|---|
| Calibration: all three label the same 50 items, without talking; then discuss every difference; update the guideline | 50 | 150 |
| Primary labels: each item has one primary labeller; load split 2:1:1 (D15 note 2026-10-24) | 950 | 950 |
| Second labels: an independent second labeller, other than the primary | about 200 | about 200 |
| Total | 1,000 | about 1,300 |

- Calibration items are gold items. Their gold label is the consensus after discussion.
- The double-labelled items are chosen so that every stratum with >= 10 items in the sample gets at least 10 double-labelled items where possible (set cover, `src/ic/gold/assignment.py`). The rest is spread over priority strata.
- Each labeller sees the calibration block first, then the rest in random order.
- Annotator names, access and dates: to be set.

### 5.3 Model suggestions (D24 B)

- Addresses: every item opens with a model suggestion for the main address (accept, correct or delete). Fields not found verbatim in the capture text are marked.
- Topics (POI, WZ): not pre-filled. The labeller decides them from the capture.
- Site status and imprint URL come from the capture, not from a model.
- The suggestion prompt must be main-address-only (§7).
- The suggestion model is recorded per item (`prefilled_from`). See §10 for the conflict with E52 candidates.

### 5.4 Adjudication and agreement

- Two labels that differ are adjudicated. The adjudicated label is the gold label. Both raw labels stay in the files.
- Adjudicator: to be set (`docs/model_eval_protocol.md` §10 item 2).
- Agreement on the double-labelled items: site status and `imprint_present` (Cohen's kappa); main address (location match per D12, and exact match per field); POI and WZ (share of equal path prefix per level; Krippendorff alpha on the top level).
- Address agreement is reported as "agreement with suggestions shown". Both labellers saw the same suggestion, so the two labels are independent of each other but not of the suggestion.
- Calibration agreement (before discussion) is reported too.

## 6. Use of the set in evaluation (pending D58, recommended option A)

- All 1,000 items (and the top-up) are test items. There is no development split.
- **Publish depth by cross-fitting.** Split the items into 5 folds at random, stratified by priority stratum (strata with fewer than 5 items are pooled into one "rare" stratum per schema, so every fold gets a fair share). For each fold, choose the depth cut-off (deepest level with P >= 0.8, D54) on the other 4 folds and apply it to this fold. Report the out-of-fold numbers.
- **Model choice** is made on the full set. The paper reports it as such. With 3 to 5 candidates the selection effect is small.
- Details of scoring, candidates, statistics and the decision rule: `docs/model_eval_protocol.md` (E52). That document matches v0.3 since 2026-11-12 (protocol draft v0.2).

Option B (fixed split: 200 items for cut-off and choice, 800 for reported numbers) is simpler but has 20% fewer test items.

## 7. Reuse of tooling

| Part | Status | Change for E53 |
|---|---|---|
| `src/ic/gold/sampling.py` (core + rarest-first oversample, HT weights, Wilson) | reuse | new `memberships()` for the §4.3 strata (POI, WZ, address, frame); union of two models; `frame_stratum` field |
| `src/ic/gold/assignment.py`, `scripts/gold/e18_assign.py` (3 labellers, 50 calibration, about 200 double) | reuse | input from the new sample file |
| `scripts/gold/e17_capture.py` (static HTML, DOM, text, screenshot, meta) | reuse | output `datasets/E53/gold/`; add the `ic fetch` record and its timestamp to each item; capture IP group in `meta.json` |
| `src/ic/gold/annotate` (tool, schema v2 with POI and WZ labels) | reuse | make operator type and the 11-class topic optional (today required for live sites); hide or drop the full address list requirement |
| `scripts/gold/e21_prefill.py` (qwen-agentworld; addresses, operator, 11-class topic) | adapt | main-address-only prompt; no topic, no operator type; model choice per §10 |
| `docs/annotation_guideline.md` | adapt | main address only; other addresses as a flag; no 11-class topic and operator type (if dropped) |
| `src/ic/gold/detectors.py` | reuse | address detectors on crawl text in the screen; descriptive tags on the capture |
| E50 runner (`scripts/E50/e50_run.py`) | reuse | screen inputs from crawl records; prompts unchanged |

To build:
1. **Frame builder**: reads the release site list, the exclusion lists and the host-to-source tables (`.../E31/r4/E31_in/*.tsv`, first source wins); writes F0, N0 and a report of removed hosts per list.
2. **Phase-1 screen on crawl text**: reads the crawl records for S1, builds E50 inputs, runs two models and the text detectors, writes one record per site.
3. **Top-up draw**: compares r5 with r4/E40 r2, applies the exclusions, draws n_A, and marks dropped items.
4. **Same-day fetch driver**: runs `ic fetch` for a batch of items on the crawl VM and the capture for the same batch on the same day.

## 8. Steps of E53

| # | Step | Output |
|---|---|---|
| 1 | Fact-finding (done) | `results/E53/facts.md` |
| 2 | Settle D55-D58 | `docs/decisions/D55`-`D58` outcomes |
| 3 | Copy the E8 and E12 host lists from aspe; record sha256 | `datasets/E53/exclude/{old_gold,e8,e12_screen,e12_sample,e49,e51}.txt`, `datasets/E53/exclude/manifest.tsv` |
| 4 | Build the frame F0 | `datasets/E53/frame/frame.txt`, `datasets/E53/frame/host_source.tsv`, `results/E53/frame.md` (N0, removed per list) |
| 5 | Draw S1 (n1 = 20,000, seed recorded) | `datasets/E53/phase1_hosts.txt` |
| 6 | Screen S1 (two models, detectors, free fields) | `datasets/E53/screen/screen_features.jsonl`, `results/E53/screen_prevalence.md` (shares with Wilson CIs, model agreement) |
| 7 | Phase-2 draw (core 600 + oversample 400) | `datasets/E53/gold_sample.jsonl`, `results/E53/quota_table.md` |
| 8 | Lead check of the draw (counts, pi, weights sum to about N0, 0 overlap with exclusions) | entry in `docs/decisions.md` |
| 9 | Same-day `ic fetch` + capture, in batches | `datasets/E53/gold/<host>/`, `results/E53/capture_summary.md` |
| 10 | Address suggestions | `datasets/E53/gold/prefill.jsonl` |
| 11 | Assignment | `datasets/E53/gold/assignment.jsonl` |
| 12 | Calibration (50 items), guideline update | `datasets/E53/gold/labels/L{1,2,3}.jsonl`, `results/E53/calibration.md` |
| 13 | Main labelling and second labels | `datasets/E53/gold/labels/L{1,2,3}.jsonl` |
| 14 | Adjudication, gold file, agreement | `datasets/E53/gold/gold.jsonl`, `results/E53/agreement.md` |
| 15 | r5 top-up (when r5 is final): draw, capture, label | `datasets/E53/topup_sample.jsonl`, `results/E53/topup.md` |
| 16 | Hand-over to E52 | `results/E52/split.json` (5 folds) |

## 9. Related work

Web information extraction benchmarks:
- **SWDE** (Hao et al., SIGIR 2011, DOI 10.1145/2009916.2010020): about 124k detail pages from 80 hand-picked sites in 8 verticals. The target page is given. **Expanded SWDE** (Lockard et al., NAACL 2019, N19-1309) adds open relation labels.
- **WebSRC** (Chen et al., EMNLP 2021, 2021.emnlp-main.343): about 400k question-answer pairs over 6.4k pages, with HTML and screenshots.
- **Klarna Product Page Dataset** (Hotti et al., arXiv 2111.02168, TMLR 2024; Zenodo DOI 10.5281/zenodo.12605480): 51,701 product pages from 8,175 shops, with rendered DOM snapshot and screenshot.

Address extraction:
- **Schmidt, Manschitz, Rensing, Steinmetz** (i-KNOW 2013, DOI 10.1145/2494188.2494193): German postal addresses from unstructured web text with OpenStreetMap. Text only; no page discovery, no negatives.
- **Ahmadi et al.**: "Clean Me If You Can" (arXiv 2606.31983, 2026). Real-world address records for data cleaning, not extraction from web pages.

What this gold set adds:
1. **A probability sample of a released dataset.** Every item has a known inclusion probability, so each metric has a population estimate with a CI for the release. The benchmarks above pick sites by hand or by vertical.
2. **Coverage of rare topic classes and address cases** in two topic schemas (POI, WZ 2025 to 5 levels), with the sampling bias stated.
3. **End-to-end input.** The models get the same-day output of the release fetch code, including fetch failures. The labels describe the site on the same day.
4. **A frozen multimodal capture per item** (static HTML, rendered DOM, screenshot, timestamps).
5. **A legally defined genre.** The imprint (§ 5 DDG in Germany, § 5 ECG and § 25 MedienG in Austria, Art. 3 para. 1 let. s UWG in Switzerland) defines the right answer: the provider's address.
6. **Three labellers with calibration, about 200 double labels and adjudication.** Address agreement is reported with suggestions shown.

## 10. Open choices

1. **D55 frame**: A = draw now from r4 + E40 r2 minus used hosts, with r5 top-up (recommended); B = wait for r5.
2. **D56 input form**: A = same-day `ic fetch` for models + capture for labellers (recommended); B = stored crawl text + fresh capture as help; C = rendered DOM for both.
3. **D57 sampling design**: A = two-phase, core 600 + oversample 400 (recommended); B = SRS of 1,000; C = equal quotas, no core.
4. **D58 test use**: A = all items test, 5-fold cross-fitting for the depth cut-off (recommended); B = fixed 200/800 split.

Assumed by the lead (can be overruled):
- Screen models: gemma4-31b-it and qwen38-27b (both E52 candidates; see doubts).
- Main address only in the label; other addresses as the flag `multi_address`.
- Operator type and 11-class topic are not filled (tool change).

## 11. Open doubts

- **Stratifying with candidate models.** The screen models are likely E52 candidates. Unweighted rare-class scores favour them (§4.7). Mitigation: weighted comparisons, and the screen models marked in per-class tables. Alternative: use a non-candidate pair for the screen.
- **Site change between crawl and capture.** Under D56 A this affects only strata and weights. Under D56 B or C it also affects the labels or the input: B must flag and drop changed sites, C changes the input form.
- **E8 and E12 lists are on aspe only.** They must be copied before step 4. Without them the exclusion is incomplete.
- **E48 Shopify is incomplete.** The crawl stopped at about 84%. The record still says RUNNING (other module). The top-up size depends on its final state.
- **Prefill model vs. E52 candidates.** The suggestion model must not be an E52 candidate, or it is reported as "made the suggestion" with an upper-biased address score. qwen-agentworld-35b-a3b was the E21 model and is an E50 model.
- **Small strata.** At T about 25, a per-stratum Wilson CI is about ±15-20 pp. Rare WZ sections (for example B, D, E, U, V) may have fewer than 25 sites in S1. Their phase-1 variance is not small.
- **Fetch blocks.** `ic fetch` from the crawl VM can be blocked (Strato 503 in E8/E12). This is correct for the release, but it lowers model scores on blocked sites. The capture from another IP keeps the labels right.
- **Old 11-class field.** The tool requires it today. Dropping it breaks comparison with the old gold set; the paper does not need that comparison.
