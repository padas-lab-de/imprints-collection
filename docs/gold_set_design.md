# Gold set design: a stratified probability sample of the German imprints release

The gold set measures how well the release pipeline extracts what the release publishes. It is a two-phase probability sample of the released sites. Every item has a known inclusion probability, so each metric has a population estimate with a confidence interval for the release.

The commands for each step are in `docs/reproduce_goldset.md`. Scoring is in `docs/model_eval_protocol.md`. The labelling rules are in `docs/annotation_guideline.md`.

## Summary

- **Population**: the sites of the German Imprints release.
- **Size**: 1,869 items from the main draw, plus a top-up of 18 items from sites added in the final release list. 1,887 items in all.
- **Design**: two-phase probability sample. Phase 1 screens a random 20,000 frame sites with fixed extraction prompts on stored crawl text. Phase 2 draws a random core of 600 and a coverage oversample of 1,195, plus 74 stratum top-up items. Every item has a known inclusion probability.
- **Input**: on one day per item, `ic fetch` makes the model input and a gold capture makes the labeller input.
- **Labels**: site status, imprint found, main address, POI v3 label, WZ 2025 label. Three labellers (L1, L2, L3). 50 calibration items, about 375 double-labelled items, adjudication.
- **Use**: all items are test items. The publish depth is set by 5-fold cross-fitting.

## 1. Purpose and tasks

The unit is one site (one canonical host). The set serves four tasks.

| Task | Gold label | Primary metric | Secondary metrics |
|---|---|---|---|
| Site status, imprint found | `site_status`; `imprint_present`; `imprint_url` | imprint found: recall and precision of the fetch step against `imprint_present` | `site_status` agreement |
| Main address | the main address (street, number, postcode, town, country, P.O. box) or `no_address_reason` | location match by geocoding: gold and prediction are geocoded with Photon; a match is the same postcode + street, or a distance of at most 100 m | field-level exact and normalised match; no-address precision and recall; false-address rate on items without an address |
| POI topic (`topics/poi_v3.jsonl`, 2 levels, 8 top-level classes) | one main node + up to 2 extra nodes, at the finest decidable level | acc@L and P@L per level (L1, L2) | lenient score with extra labels; coverage |
| WZ 2025 topic (`topics/wz2025.jsonl`, 5 levels, 22 sections A-V) | one main node + up to 2 extra nodes, at the finest decidable level | acc@L and P@L per level (L1-L5) | lenient score with extra labels; coverage |

Rules:
- **Main address only.** The pipeline returns one address per site. The gold set scores that address. Other postal addresses on the imprint are recorded only as the flag `multi_address`.
- **Finest decidable level.** A labeller stops at an inner node when the site text does not decide the child. A host counts at level L only if its label reaches L.
- **One main + up to 2 extra labels** per schema. The strict score uses the main label. The lenient score accepts the main label or an extra label.
- Operator type and an older 11-class topic are not evaluation targets.

## 2. Frame

### 2.1 Population

The target population U is the set of sites in the release list (one canonical host per line, after the parked-site filter). The frame was drawn from the release list of 3,908,045 sites. All these sites had an imprint at crawl time, so the frame has no "no imprint" sites by construction.

### 2.2 Exclusions

A site is out of the frame if it was used before in any earlier gold set, pilot or prompt study of the project. The match key is the canonical host, lower case, with a leading `www.` removed. Both variants (`x.de`, `www.x.de`) are excluded. The lists are given to `goldset/exclusions.py` as `NAME=FILE` pairs. It writes one normalised list per name and a manifest with sha256 values. The lists themselves are not part of this repository (except the old gold set, `evaluation/gold_standard_data.jsonl`).

Frame: F0 = U minus the union of the lists. N0 = |F0|. The frame builder reports how many hosts of each list it removes.

### 2.3 Top-up from the final release list

The final release list adds sites that were not in the frame source, and can drop some.

1. **Added sites.** F_A = sites in the final list and not in the frame source, minus the exclusion lists. N_A = |F_A|. Draw a simple random sample of n_A = round(1,869 x N_A / N0) sites from F_A. So the top-up has the mean sampling fraction of the gold set. Each item has pi = n_A / N_A. These items get no phase-1 screen and no oversample. They are labelled like all other items.
2. **Dropped sites.** A drawn F0 site that the final list removes leaves the set. It is not replaced.
3. **Weights stay exact.** F0 and F_A are two frame strata with known designs. Removing dropped sites is a domain restriction: it does not change any selection probability.

Result:
- Final list: 3,945,356 sites (sha256 prefix `93bd4d30`).
- 37,338 keys of the final list are not in the frame source. 27 of them are in the exclusion lists, so N_A = **37,311**.
- n_A = round(1,869 x 37,311 / 3,901,721) = round(17.87) = **18**.
- pi = 18 / 37,311 = 0.000482, so the weight is 2,072.8. The seed is 20261114.
- 27 frame-source keys are not in the final list. None of them is a gold item, so **0 items are dropped**.
- The 18 items are dealt to the folds with the fewest items. The fold sizes become 378, 378, 377, 377, 377 (1,887 items in all).

Estimator for the final population U' = (F0 ∩ U') ∪ F_A, with y_i the item's score and w_i = 1 / pi_i:

    total(y)  =  sum over drawn i in F0 ∩ U' of w_i y_i   +   sum over drawn i in F_A of (N_A / n_A) y_i

## 3. Input and capture

### 3.1 Two inputs from the same day

The release pipeline extracts from `ic fetch` text: the resiliparse `main_content` of the static HTML of three pages (main, kontakt, impressum). The crawl keeps no HTML, and sites change after the crawl.

For each item, on one day:
1. **Model input.** Run `ic fetch` (the release fetch code) from the crawl machine. Its output is the model input for all tasks, in the same form as in the release.
2. **Labeller input.** Run the gold capture (§3.2) on the same day. Labellers label the site from the capture.

Rules:
- An item where `ic fetch` finds no imprint stays in the set. It measures the fetch step. With no imprint text the address model is not called, and the prediction is "no address".
- The labeller labels the site, not the `ic fetch` output. A site that changed since the crawl is labelled as it is on the capture day.
- The capture runs from a different IP than the crawl machine where possible. Some hosters block the crawl machine. A block is a fetch failure, not a property of the site. `ic fetch` stays on the crawl machine, so that fetch failures match the release.
- If `ic fetch` and the capture run on different days for an item, the item gets the flag `input_day_mismatch`.
- If the capture failed or is incomplete, a later re-capture can replace it. The earlier capture is kept in the item directory (`capture_previous/`, `capture_previous2/`). An item whose capture still has a known problem gets a `capture_problem` note. The tool shows it as a banner.

### 3.2 Per-item archive

One directory per item, `$IC_GOLD_DATA/gold/<host>/` (default `datasets/goldset/gold/<host>/`), made by `goldset/capture.py` and completed by `goldset/merge_fetch.py`.

| Artifact | How | Why |
|---|---|---|
| `ic_fetch.jsonl` | `ic fetch` record of the item: main, kontakt, impressum with url, title, `main_content`, `content_language` | model input |
| `landing.static.html`, `imprint.static.html`, response headers | plain HTTP GET | static vs. rendered comparison |
| `landing.dom.html`, `imprint.dom.html` | Playwright Chromium, `networkidle` + 2 s, `page.content()` | labeller reference text |
| `landing.txt`, `imprint.txt` | `document.body.innerText` of the rendered page | check of verbatim address fields |
| `landing.png`, `imprint.png` | full-page screenshot, 1280 px wide, up to 20,000 px tall | labeller view; image-only addresses |
| `imprint.pdf` | the file, if the imprint is a PDF | PDF imprints |
| `meta.json` | UTC timestamps of the capture and of `ic fetch`, final URLs, redirect chains, HTTP status, user agent, viewport, browser version, cookie-banner action, capture IP group | provenance |

Rules:
- One capture per item, with a timestamp. The labeller labels from the screenshot and DOM text. The labeller opens the live site only when the capture lacks something, and records this (`used_live_site`, `comment`).
- If the capture has no rendered text, the tool falls back to the `ic fetch` text of the item.
- Cookie banners: the capture clicks a "reject" or "only necessary" button from a fixed list of labels. Otherwise it leaves the banner. `meta.json` records which.
- No WARC.

### 3.3 Descriptive tags

The detectors in `src/ic/gold/detectors.py` run on each capture: technology family, rendering need, imprint location, obfuscation, image-only candidate. These tags describe the set. They are not strata, and they do not change weights. Error analysis can use them.

## 4. Sampling design

### 4.1 Overview

| Phase | What | Size |
|---|---|---|
| 1 | Simple random sample S1 from F0, screened on stored crawl text | n1 = 20,000 |
| 2a | Random core: the first 600 sites of a seeded permutation of S1 | 600 |
| 2b | Coverage oversample: rarest stratum first, from S1 minus the core | 1,195 |
| 2c | Stratum top-up: one item for each priority stratum the draw would leave empty | 74 |
| Top-up | SRS from the sites added in the final release list (§2.3) | 18 |

Code: `src/ic/gold/sampling.py`, `goldset/frame.py`, `goldset/draw.py`, `goldset/topup.py`. Seeds are fixed: frame 20261112, phase 2 20261113, top-up 20261114. The permutation is a sha256-seeded order of the hosts.

### 4.2 Phase 1: screen

Input: the stored crawl record of each site in S1. No new fetches.

Per site:
- **Two models with fixed prompts**: gemma4-31b-it and qwen38-27b. Tasks: POI (retrieve k30), WZ (retrieve k30, 1,500 characters per field), address (main address, JSON schema). The prompts are not changed for the screen.
- **Text detectors** (`src/ic/gold/detectors.py`) on the imprint text: `find_addresses` and `address_flags` (P.O. box, several addresses, AT or CH postcode and country words, no postal address).
- **Free fields**: TLD, crawl source, `content_language`, text length.

Output per site: one record with both models' predictions, the detector flags and the free fields.

### 4.3 Strata

A site in S1 is a **member** of every stratum below that it meets. One site can be a member of many strata.

| Group | Strata | Membership rule |
|---|---|---|
| POI | the 8 top-level classes and the L2 classes of POI v3 | either model predicts the class |
| WZ | the 22 sections A-V and the groups of WZ 2025 | either model predicts the section or group |
| Address | `addr:at`, `addr:ch` | either model's main address, or a detector address, has an AT or CH postcode or country |
| Address | `addr:po_box` | detector or either model finds a P.O. box |
| Address | `addr:none` | imprint text present, and neither model nor detector finds a postal address |
| Address | `addr:multi` | detector finds 2 or more distinct postal addresses |
| Address | `lang:non_de` | `content_language` of landing page or imprint is not German |

**Union of two models.** A site is a member of a model-based stratum if either model predicts it. So no single model decides the oversample.

### 4.4 Phase 2: core and oversample

1. **Priority stratum.** Each site gets the rarest stratum it is a member of (fewest members in S1). A site in no stratum gets `other:none`, which is never oversampled.
2. **Core.** The first n0 = 600 sites of a seeded permutation of S1. The core is a simple random sample of F0 on its own.
3. **Oversample.** Rarest stratum first: draw at random from the not-yet-selected sites whose priority stratum is h. Stop when the marginal count of h in the sample (core and extras, all memberships) reaches T(h), or when the pool is empty.
4. **Target.** T = 25 for each POI top-level class, WZ section and address case; T = 5 for each POI L2 class and each WZ group. There is no item budget: the size follows from the target (1,795 items on the 19,998 screened sites), plus one item for each priority stratum the draw would leave empty (74 items; no stratum has weight 0): 1,869 items.
5. **Shortfall.** If a stratum has fewer than T members in S1, all of them are drawn (phase-2 probability 1). The quota table records this.

### 4.5 Inclusion probabilities and weights

Within priority stratum h, the m_h selected sites are a uniform random subset of the M_h sites of S1 in h. Conditional on the realised M_h:

    pi_i  =  (n1 / N0)  x  (m_h / M_h)          w_i  =  1 / pi_i

Each item stores `priority_stratum`, `strata` (all memberships), `pi_phase1`, `pi_phase2`, `inclusion_probability`, `design_weight`, `frame_stratum` (F0 or F_A), `in_core` and `fold`.

### 4.6 Estimators and reporting

| Figure | Estimator | 95% CI |
|---|---|---|
| Population figure (share, accuracy, P@L) | Hajek ratio: theta = sum(w_i y_i) / sum(w_i z_i), z_i = 1 if the item counts for the metric | Taylor linearisation, phase-2 strata as strata, with finite population correction 1 - m_h / M_h; strata with a single item are collapsed with a neighbouring stratum of the same schema for the variance |
| Model difference (population) | Hajek ratio of the paired item difference | same linearisation |
| Check on the core | plain share over the 600 core items (SRS) | Wilson |
| Per stratum | unweighted, by the **labelled** (true) stratum; n shown | Wilson; rates only for n >= 10, counts below |

Rules:
- Population figures are the headline numbers. Per-stratum figures are descriptive.
- The linearised variance treats the M_h as fixed. With n1 = 20,000 the phase-1 component is small for common strata. It is not small for rare strata.
- Per-stratum figures use the label's true stratum. They do not use the screen prediction.

### 4.7 Known biases

- **Strata come from model predictions.** True members of a rare class that both screen models missed enter only through the core, with a large weight. Weighted estimates stay unbiased (every frame site has pi > 0), but their variance is high.
- **Unweighted per-class scores favour the screen models.** In a rare class, most sample items are items that a screen model predicted as that class. So an unweighted recall for that class is biased upward for the screen models. Per-class model comparisons are reported weighted, or with the screen models marked.
- **Models and detectors decide strata only, never labels.** Labellers do not see strata or screen predictions. A mis-stratified item changes only its weight.
- **Stale screen input.** The screen uses crawl text that is weeks old. The label uses a fresh capture. A site that changed may sit in the wrong stratum. This affects weights, not labels.
- **Conditional probabilities.** pi is conditional on the realised M_h and on the screen outputs.

## 5. Labelling protocol

### 5.1 Label schema

Tool schema v3 (`src/ic/gold/annotate/schema.py`).

| Field | Values |
|---|---|
| `site_status` | live, unreachable, http_error, parked, redirect_other_domain, not_a_website |
| `imprint_present`, `imprint_url`, `imprint_location` | as in `docs/annotation_guideline.md` §2 |
| `addresses` + `main_address_index` | the main address with all fields, verbatim from the capture (town as written) |
| `no_address_reason` | site_dead, no_imprint, imprint_without_address |
| `flags` | multi_address, po_box, obfuscated, non_dach, ... |
| `topic_labels.poi`, `topic_labels.wz` | main node, 0-2 extra nodes, confidence, note; POI `online_only` |
| `used_live_site`, `capture_problem`, `comment`, `seconds_spent`, `prefilled_from` | provenance |

### 5.2 Labellers and workload

| Step | Items | Labels |
|---|---|---|
| Calibration: all three label the same 50 items, without talking; then discuss every difference; update the guideline | 50 | 150 |
| Primary labels: each item has one primary labeller; load split 2:1:1 | the rest | one per item |
| Second labels: an independent second labeller, other than the primary | about 375 | about 375 |

- Calibration items are gold items. Their gold label is the consensus after discussion.
- The double-labelled items are chosen so that every stratum with >= 10 items in the sample gets at least 10 double-labelled items where possible (set cover, `src/ic/gold/assignment.py`). The rest is spread over priority strata.
- Top-up items get a primary labeller only.
- Each labeller sees the calibration block first, then the rest in random order.
- Annotator names, access and the calibration date: to be set.

### 5.3 Model suggestions

- Addresses: every item opens with a model suggestion for the main address (accept, correct or delete). Fields not found verbatim in the capture text are marked.
- Topics (POI, WZ): not pre-filled. The labeller decides them from the capture.
- Site status and imprint URL come from the capture, not from a model.
- The suggestion model is not an evaluation candidate. It is recorded per item (`prefilled_from`). The suggestions are made by `goldset/prefill.py`.

### 5.4 Adjudication and agreement

- Two labels that differ are adjudicated. The adjudicated label is the gold label. Both raw labels stay in the files.
- Adjudicator: to be set.
- Agreement on the double-labelled items: site status and `imprint_present` (Cohen's kappa); main address (location match, and exact match per field); POI and WZ (share of equal path prefix per level; Krippendorff alpha on the top level).
- Address agreement is reported as "agreement with suggestions shown". Both labellers saw the same suggestion, so the two labels are independent of each other but not of the suggestion.
- Calibration agreement (before discussion) is reported too.

## 6. Use of the set in evaluation

- All items are test items. There is no development split.
- **Publish depth by 5-fold cross-fitting.** The items are split into 5 folds at random, stratified by priority stratum (strata with fewer than 5 items are pooled into one "rare" stratum per schema). For each fold, the depth cut-off (deepest level with P >= 0.8) is chosen on the other 4 folds and applied to this fold. The out-of-fold numbers are reported.
- **Model choice** is made on the full set and reported as such. With 3 to 5 candidates the selection effect is small.
- Scoring, candidates, statistics and the decision rule: `docs/model_eval_protocol.md`.

## 7. Related work

Web information extraction benchmarks:
- **SWDE** (Hao et al., SIGIR 2011, DOI 10.1145/2009916.2010020): about 124k detail pages from 80 hand-picked sites in 8 verticals. The target page is given. **Expanded SWDE** (Lockard et al., NAACL 2019, N19-1309) adds open relation labels.
- **WebSRC** (Chen et al., EMNLP 2021, 2021.emnlp-main.343): about 400k question-answer pairs over 6.4k pages, with HTML and screenshots.
- **Klarna Product Page Dataset** (Hotti et al., arXiv 2111.02168, TMLR 2024; Zenodo DOI 10.5281/zenodo.12605480): 51,701 product pages from 8,175 shops, with rendered DOM snapshot and screenshot.

Address extraction:
- **Schmidt, Manschitz, Rensing, Steinmetz** (i-KNOW 2013, DOI 10.1145/2494188.2494193): German postal addresses from unstructured web text with OpenStreetMap. Text only; no page discovery, no negatives.

What this gold set adds:
1. **A probability sample of a released dataset.** Every item has a known inclusion probability, so each metric has a population estimate with a CI for the release.
2. **Coverage of rare topic classes and address cases** in two topic schemas (POI, WZ 2025 to 5 levels), with the sampling bias stated.
3. **End-to-end input.** The models get the same-day output of the release fetch code, including fetch failures. The labels describe the site on the same day.
4. **A frozen multimodal capture per item** (static HTML, rendered DOM, screenshot, timestamps).
5. **A legally defined genre.** The imprint (§ 5 DDG in Germany, § 5 ECG and § 25 MedienG in Austria, Art. 3 para. 1 let. s UWG in Switzerland) defines the right answer: the provider's address.
6. **Three labellers with calibration, double labels and adjudication.** Address agreement is reported with suggestions shown.

## 8. Limitations

- **Stratifying with candidate models.** The screen models are also evaluation candidates. Unweighted rare-class scores favour them (§4.7).
- **Small strata.** At T = 25, a per-stratum Wilson CI is about ±15-20 pp. Rare WZ sections may have fewer than 25 sites in S1.
- **Fetch blocks.** `ic fetch` from the crawl machine can be blocked by some hosters. This is correct for the release, but it lowers model scores on blocked sites. The capture from another IP keeps the labels right.
- **Sites outside the final list.** The top-up covers only sites in the final release list.
