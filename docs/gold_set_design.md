# Gold set design: a diversity-stratified gold set for German imprints

Status: proposal v0.1 (2026-10-23), from experiment E8-gold-strata-pilot. Decisions it depends on: D12 (town copied as written, location scored by geocoding), D14 A (labels from the live rendered site; HTML, rendered DOM and screenshot archived), D15 C (one human labels every item from scratch; a second human independently labels about 20%; no model pre-labels). Points that need the user are under "Open choices".

The new set replaces the old 1,000-item gold set. The old set has exactly one address per item, 999 of them in Germany, and no negatives (lead record, gold audit). So it cannot measure no-address answers, AT/CH sites, multiple addresses or how pages are produced.

## Summary

- **Design**: a probability sample of hosts from the crawl frame, in two parts. (1) A random core of 600 hosts gives unbiased population figures. (2) About 700 hosts are added by oversampling rare strata from a 10,000-host screening sample and from frames defined by hostname. Every item has a known inclusion probability, so results can be weighted back to the population. Total: about 1,300 items, each labelled from scratch by one human, plus a second human on about 20% (D15 C).
- **Strata**: age, technology, rendering need, imprint modality, operator type, TLD/country, topic, imprint location, negatives and hard cases. Each has an automatic, unit-tested detector. The pilot measured each detector's prevalence and checked its precision by hand.
- **Pilot E8** (1,000 random hosts, seed 20261023, from `datasets/E4/random20k_seed_hosts.txt`): 69% are live, and 61% of the live hosts have an imprint the detectors reach. Among live .de/.at/.ch hosts, 12% have no imprint. Among live hosts on other TLDs, 75% have none. WordPress is 32% of live sites and site builders 11%. Sites that need JavaScript for the imprint are 1.2% of live sites. Imprints whose address exists only as an image are 2 of 422 (0.5%, CI 0.1-1.7%). PDF imprints: 0 of 694.
- **Screenshot-required is an edge case.** The pilot shows it exists but is rare: 2 in 1,000 hosts. The design gives it a small quota (20 items, found by screening) and is otherwise not built around it. Screenshots are archived for every item anyway, because they are cheap and are what the labeller sees (D14 A).

## 1. Diversity dimensions and their detectors

Every dimension has an automatic detector in `src/ic/gold/detectors.py`, unit-tested in `tests/test_gold_detectors.py` on inline HTML with no network. The pilot driver `scripts/gold/e8_pilot.py` collects the inputs (static fetch, headless render, Wayback CDX, innkube LLM) and writes one record per host to `results/E8/pilot_features.jsonl`. "Source" means where a detector gets its evidence from.

| Dimension | Values (strata) | Detector and source | Pilot precision (20 hand-checked) |
|---|---|---|---|
| Age | `<2010`, `2010-2017`, `2018-2022`, `>=2023`, `no_capture` | `age_bin`: year of the host's first capture in the Wayback Machine. Source: CDX API `web.archive.org/cdx/search/cdx?url=<host>&limit=1&fl=timestamp`, at most 1 request/s, with backoff on 429. Second signal: the latest copyright year on the landing page (`copyright_years`). | not checkable by hand (the CDX answer is the ground truth for "first capture"); see caveat below |
| Technology / CMS | `wordpress`; `site_builder` (Wix, Jimdo, IONOS MyWebsite, Strato, Squarespace, Weebly, Webflow, Duda, one.com, GoDaddy); `blog_platform` (Blogger); `cms_other` (TYPO3, Joomla, Contao, Drupal, and minor CMSs that only show a generator tag); `shop_system` (WooCommerce, Shopify, Shopware, OXID, PrestaShop); `custom_php`; `static_html` (including old desktop editors such as FrontPage and Dreamweaver); `static_generator` (Hugo, Jekyll); `spa_framework` (React, Next.js, Angular, Vue, Nuxt, Gatsby); `custom_other` (ASP.NET, Java); `unknown` | `detect_tech`: Wappalyzer-style signatures (generator meta tag, asset paths, cookies, response headers, `.php` links). It runs on the static HTML and falls back to the rendered DOM. Source: static fetch + headless render. | 20/20 |
| Server language | `php`, `asp.net`, `java`, unknown | `detect_tech` (headers, session cookies, link extensions) | covered by the tech check |
| Rendering need | `static_ok` (imprint and address found in static HTML), `js_required` (imprint or address found only after rendering), `js_content` (rendered text much longer, but the imprint is in static HTML too), `static_blocked` (static fetch failed with 403/429/TLS error, browser succeeded), `none` (no imprint found in either) | `rendering_need`: compares static and rendered text, and whether the imprint and an address are found in each. Source: static fetch vs. Playwright Chromium (`networkidle`). | `js_required` 7/7 checked are real (e.g. imprint link only in a JS menu config, Angular/Next.js shells); `static_blocked` 13/13 are blocked fetches, not JS |
| Imprint modality | `text`, `image_only`, `pdf` | `screenshot_candidate`: the imprint text has no address and the page has an image whose name or alt text suggests an address. `image_only_addresses`: a vision model (gemma4-31b-it on innkube) lists every address on the tiled full-page screenshot; an address counts as image-only when both its postcode and its street are missing from the DOM text. `pdf_imprint`: the imprint link points to a PDF. | image-only: 4 flagged in the final run, 2 of them genuine (the rest are OCR slips or invented addresses), so every candidate needs a look; PDF: none in the pilot |
| Operator type | `corporate`, `association`, `public_body`, `sole_trader`, `private_person` | (a) `operator_type_rules`: legal-form and keyword tokens (GmbH, AG, e.V., Stiftung, Gemeinde, Inhaber, ...). (b) LLM (gemma4-31b-it) on the imprint text. Source: rendered imprint text. | of 20 sampled, 13 decidable from the text: rules 6/13, LLM 12/13. Use the LLM. |
| TLD / country | `de`, `at`, `ch`, `com`, `org`, `net`, `eu`, `other`; address country DE / AT / CH / other | `tld_class` (host name); `address_flags` (postcode pattern and country words in the found addresses) | TLD is exact; address country follows the address finder |
| Topic | the 11 top-level classes (D5) | LLM (gemma4-31b-it) on landing + imprint text | not checked here (E7 evaluates topic models on the old gold set) |
| Imprint location | `separate_page`, `landing_page`, `modal_or_fragment`, `other_domain`, `unlinked_probe` (no link, but `/impressum` exists), `none` | `find_imprint_links` (link text and URL patterns, scored) + `imprint_location`. Source: static and rendered landing page. | `none` 11/12 (one Shopify imprint missed); `other_domain` 8/12, all 4 errors were links to registrar placeholders or imprint generators, which are now excluded (re-run: 9 left) |
| Negatives | `site_dead` (unreachable, http_error, parked, default page), `no_imprint`, `imprint_without_address` | `site_status` (HTTP status, error, parking and default-page phrases, redirect to another domain) + `imprint_location` + address finders (rules and LLM) | site_status 20/20 |
| Hard cases | `multi_address`, `po_box`, `obfuscated` (e-mail or address hidden by JS, entities or images), `non_dach` | `find_addresses` (German, Austrian and Swiss street + postcode + town patterns) + `address_flags` (distinct addresses keyed by postcode, house number and street prefix); `obfuscation_signals` | multi_address 18/20 (both errors were spelling variants of one address; fixed and unit-tested); po_box 7/7 contain a P.O. box, but in only 2/7 is it the operator's (the others belong to an ombudsman or a district) |

Notes on the detectors:
- **Age is the age of the domain, not of the current site.** A domain first archived in 2004 counts as `<2010`, even after a 2024 redesign. That is the right notion for "old vs. new web presence". The current site's age is shown by the technology strata (e.g. desktop editors, frames, old WordPress versions) and by the copyright year. `no_capture` (3.2%) includes 14 hosts whose CDX answer could not be parsed. These should be re-queried before sampling.
- **Detectors decide strata only.** Under D15 C no detector or model output is shown to the labellers. Detector errors therefore affect only which stratum an item is drawn from, never its label. The label also records the true stratum (modality, location, operator type), so a mis-detected item ends up in the right stratum for analysis. Only its design weight is computed from the detector's value. Section 2 says how weights handle this.
- **Hostname-defined strata** (TLD, `*.blogspot.*`, `*.wordpress.com`, `*.jimdo*`, `*.wixsite.com`) are known for the whole 6.56M frame without fetching anything, so they can be oversampled directly with exact inclusion probabilities.
- **Crawl artefacts.** In the pilot, 132 hosts (13%) answered HTTP 4xx/5xx. 80 of the 132 sample hosts hosted at Strato (81.169.145.x) returned 503 to the crawl VM. 58 of the 87 hosts with a 503 had an imprint in E4. This looks like an IP-level block or rate limit, possibly triggered by the parallel E6 crawl from the same VM. Wix answered 429 and Jimdo 403 to the static client but served the headless browser. A retry at 4 workers did not lift the Strato block. These are properties of the crawler, not of the sites. The gold capture should run from a different IP or more slowly, and `static_blocked` is kept as a tag, not as a sampling stratum.

## 2. Sampling frame and quotas

### Frame

The frame is `seed_hosts.txt.gz` (6,560,119 hosts), the same list the dataset is built from, so that gold-set results speak for the dataset. Hostname counts in the frame give exact oversampling frames for some strata: `.de` 3,428,132; `.at` 232,476; `.ch` 216,947; `*.jimdo*` 10,649; `*.wordpress.com` 8,450; `*.wixsite.com` 5,038; `*.blogspot.*` 937.

### Pilot prevalences (E8, 1,000 random hosts, Wilson 95% CIs)

| Stratum | Base | n | % | 95% CI |
|---|---|---|---|---|
| live | all 1,000 | 694 | 69.4 | 66.5-72.2 |
| http_error (mostly a Strato 503 block, see notes) | all | 132 | 13.2 | 11.2-15.4 |
| unreachable | all | 82 | 8.2 | 6.7-10.1 |
| redirect to another domain | all | 77 | 7.7 | 6.2-9.5 |
| parked / default / placeholder / challenge page | all | 15 | 1.5 | 0.9-2.5 |
| age <2010 | live 694 | 279 | 40.2 | 36.6-43.9 |
| age 2010-2017 | live | 179 | 25.8 | 22.7-29.2 |
| age 2018-2022 | live | 134 | 19.3 | 16.5-22.4 |
| age >=2023 | live | 80 | 11.5 | 9.4-14.1 |
| age: no capture | live | 22 | 3.2 | 2.1-4.8 |
| WordPress | live | 219 | 31.6 | 28.2-35.1 |
| site builder (Wix 24, IONOS 11, Strato 10, Squarespace 9, Jimdo 7, other 13) | live | 74 | 10.7 | 8.6-13.2 |
| other CMS (TYPO3 21, Joomla 25, Contao 9, Drupal 6, minor 36) | live | 97 | 14.0 | 11.6-16.8 |
| static HTML (incl. 9 desktop editor) | live | 54 | 7.8 | 6.0-10.0 |
| custom PHP | live | 54 | 7.8 | 6.0-10.0 |
| shop system | live | 38 | 5.5 | 4.0-7.4 |
| SPA framework | live | 23 | 3.3 | 2.2-4.9 |
| custom other (ASP.NET, Java) | live | 22 | 3.2 | 2.1-4.8 |
| Blogger | live | 2 | 0.3 | 0.1-1.0 |
| static site generator | live | 2 | 0.3 | 0.1-1.0 |
| tech unknown | live | 109 | 15.7 | 13.2-18.6 |
| server language PHP | live | 197 | 28.4 | 25.2-31.9 |
| TLD .de | live | 351 | 50.6 | 46.9-54.3 |
| TLD .at | live | 21 | 3.0 | 2.0-4.6 |
| TLD .ch | live | 25 | 3.6 | 2.5-5.3 |
| TLD other (.com, .org, .net, .eu, other) | live | 297 | 42.8 | 39.2-46.5 |
| rendering: static_ok | live | 368 | 53.0 | 49.3-56.7 |
| rendering: js_required | live | 8 | 1.2 | 0.6-2.3 |
| rendering: js_content | live | 22 | 3.2 | 2.1-4.8 |
| rendering: static_blocked | live | 8 | 1.2 | 0.6-2.3 |
| imprint: separate page | live | 404 | 58.2 | 54.5-61.8 |
| imprint: other domain | live | 9 | 1.3 | 0.7-2.4 |
| imprint: no link, `/impressum` exists | live | 8 | 1.2 | 0.6-2.3 |
| imprint: on the landing page | live | 1 | 0.1 | 0.0-0.8 |
| no imprint found | live | 272 | 39.2 | 35.6-42.9 |
| no imprint, .de/.at/.ch | live .de/.at/.ch 397 | 48 | 12.1 | 9.2-15.7 |
| no imprint, other TLDs | live other 297 | 224 | 75.4 | 70.2-80.0 |
| imprint without address | live | 5 | 0.7 | 0.3-1.7 |
| imprint is a PDF | live | 0 | 0.0 | 0.0-0.6 |
| address only in an image (verified) | live with imprint 422 | 2 | 0.5 | 0.1-1.7 |
| multiple addresses (rules) | with imprint | 123 | 29.1 | 25.0-33.7 |
| multiple addresses (LLM) | with imprint | 127 | 30.1 | 25.9-34.6 |
| P.O. box anywhere on the imprint | with imprint | 7 | 1.7 | 0.8-3.4 |
| obfuscation signal | with imprint | 141 | 33.4 | 29.1-38.0 |
| address country AT or CH | with imprint | 49 | 11.6 | 8.9-15.0 |
| operator: corporate (LLM) | with imprint | 158 | 37.4 | 33.0-42.2 |
| operator: sole trader (LLM) | with imprint | 166 | 39.3 | 34.8-44.1 |
| operator: association (LLM) | with imprint | 61 | 14.5 | 11.4-18.1 |
| operator: public body (LLM) | with imprint | 24 | 5.7 | 3.9-8.3 |
| operator: private person (LLM) | with imprint | 12 | 2.8 | 1.6-4.9 |
| topic Business and Professional Services (LLM) | live | 223 | 32.1 | 28.8-35.7 |
| topic Event / Dining / Landmarks / Nightlife (LLM) | live | 9 / 17 / 2 / 1 | 1.3 / 2.4 / 0.3 / 0.1 | — |

Full tables, including every technology and topic: `results/E8/pilot_prevalence.md`.

### Design: random core + priority-stratified oversample, with design weights

Joint quotas (age × technology × operator × country × ...) would need thousands of cells, far more than a gold set of about 1,300 can fill. So quotas are **marginal**: every value of every primary dimension gets a minimum count. Joint cells are reported only descriptively.

1. **Random core**: 600 hosts by simple random sampling from the frame. Expected composition (pilot shares): about 415 live, about 255 with an imprint. This part alone gives population figures. For example, end-to-end address accuracy near 80% on the 255 hosts with an imprint has a CI of about ±5 pp.
2. **Screening sample**: 10,000 further random hosts (for example the rest of `datasets/E4/random20k_seed_hosts.txt`). All detectors run on them: static fetch, render, Wayback, and the LLM on the text. Vision runs only on imprint screenshots. All of this is free on innkube. 10,000 is the size needed to find the rarest quota strata. Image-only addresses run at about 0.2% of all hosts, which gives about 20 in 10,000; JS-required imprints at about 0.8%, which gives about 80.
3. **Oversample**: each screened host gets one *priority stratum*, the rarest stratum it belongs to, in a fixed order (image-only > imprint without address > operator P.O. box > JS-required > other-domain imprint > private person > public body > SPA > Blogger > desktop editor/static > ... > common). From each priority stratum h, n_h hosts are drawn at random. The n_h are chosen so that every marginal minimum below is met, counting core items too. Strata defined by hostname (`.at`, `.ch`, `*.blogspot.*`, `*.jimdo*`, `*.wixsite.com`) are drawn from the full frame instead, as separate frames.
4. **Weights**: an item drawn from priority stratum h of the screening sample has inclusion probability π = (10,000 / 6,560,119) × n_h / |S_h|, where S_h is that stratum's share of the screening sample. A core item has π = 600 / 6,560,119. An item from a hostname frame F has π = n_F / |F|. An item that could have been drawn in several ways gets π = 1 − ∏(1 − π_k) over all of them. Weighted (Horvitz-Thompson / Hájek) estimates give population figures. Unweighted figures per stratum are reported next to them, using the *true* stratum from the label (detector errors only change weights, not the analysis cell). As a check, the weighted sample marginals should match the core sample's marginals (raking would force this, but is not needed for unbiasedness).

### Minimum n per stratum and CI widths

Half-width of a Wilson 95% CI for a per-stratum accuracy:

| n | p = 0.5 | p = 0.8 |
|---|---|---|
| 30 | ±16.8 pp | ±13.9 pp |
| 50 | ±13.4 pp | ±10.9 pp |
| 100 | ±9.6 pp | ±7.8 pp |
| 200 | ±6.9 pp | ±5.5 pp |

Rule: **100** for strata the paper compares head-to-head (age bins, main technology families, DE/AT/CH), **50** for secondary strata, **30** for rare hard cases, and **20** for the image-only edge case. With 20 the CI is ±20 pp: enough to show whether a text pipeline fails on these items (it must, by definition) and whether a vision fallback recovers them, but not enough for fine comparisons.

### Quota table (proposal)

| Stratum | Pilot prevalence | Expected in core (600) | Minimum in set | Top-up | Found via |
|---|---|---|---|---|---|
| age >=2023 | 11.5% of live | 48 | 100 | +52 | screening |
| age 2018-2022 | 19.3% of live | 80 | 100 | +20 | screening |
| age 2010-2017, <2010 | 26%, 40% | 107, 167 | 100 | 0 | core |
| WordPress | 31.6% | 131 | 100 | 0 | core |
| site builder | 10.7% | 44 | 100 | +56 | `*.jimdo*`, `*.wixsite.com` frames + screening |
| other CMS (TYPO3, Joomla, Contao, ...) | 14.0% | 58 | 100 | +42 | screening |
| static HTML / desktop editor | 7.8% | 32 | 100 | +68 | screening |
| custom PHP | 7.8% | 32 | 50 | +18 | screening |
| shop system | 5.5% | 23 | 50 | +27 | screening |
| SPA framework | 3.3% | 14 | 50 | +36 | screening |
| Blogger | 0.3% | 1 | 50 | +49 | `*.blogspot.*` frame (937 hosts) |
| `.at` | 3.0% of live | 13 | 100 | +87 | `.at` frame |
| `.ch` | 3.6% of live | 15 | 100 | +85 | `.ch` frame |
| operator association | 14.5% of imprints | 37 | 60 | +23 | screening |
| operator public body | 5.7% | 15 | 60 | +45 | screening |
| operator private person | 2.8% | 7 | 50 | +43 | screening |
| JS-required imprint | 1.2% of live | 5 | 50 | +45 | screening |
| imprint on another domain | 1.3% of live | 5 | 30 | +25 | screening |
| imprint without address | 0.7% of live | 3 | 30 | +27 | screening |
| operator address is a P.O. box | ~0.5% of imprints (2/7 of the P.O. box hits) | 1 | 30 | +29 | screening + hand check |
| address only in an image | 0.5% of imprints | 1 | 20 | +19 | screening (rule + vision) + hand check |
| imprint is a PDF | 0 / 694 | 0 | none | 0 | label if met |
| topic Event, Dining and Drinking, Landmarks and Outdoors, Nightlife Spot | 0.1-2.4% each | 1-10 | 30 each | about +100 | screening (LLM topic) |
| negatives: no imprint | 39% of live | about 160 | (enough) | 0 | core |
| multiple addresses | 29% of imprints | about 75 | (enough) | 0 | core |

The top-ups add up to about 1,000 nominal. Since one item fills several quotas at once (an `.at` site is also some age, technology and operator type), drawing greedily from the screening and hostname frames should need about **700** items. **Total: about 1,300** (600 core + about 700 oversample).

Labelling effort (D15 C): about 3 minutes per item (all addresses with roles, operator type, topic, from the frozen screenshot). That is about 65 h for annotator A, 13 h for annotator B on 20%, plus about 5 h of calibration. If that is too much, drop the topic minimums and the static/custom-PHP 100s to 50 (total about 1,100).

Screenshot-required: the pilot found it exists (2 of 1,000 hosts: an imprint whose whole address block is one PNG, and a site whose German address is an image next to a Thai address in text). It gets the small quota of 20 above and nothing more. The archive takes screenshots of every item anyway (D14 A), so the vision-pipeline comparison in section 5 runs on all items, not only on these 20.

## 3. Per-item archive

D14 A: the gold label describes the live site as a human sees it in a browser at labelling time. To make that reproducible, everything the labeller saw is frozen first, and the label references the frozen copy.

For each item, captured in one session just before labelling (one directory per host, `datasets/gold/<host>/`):

| Artifact | How | Why |
|---|---|---|
| `landing.static.html`, `imprint.static.html` + response headers | plain HTTP GET (the same client as `ic fetch`) | input of the current pipeline; static vs. render comparison |
| `landing.dom.html`, `imprint.dom.html` | Playwright Chromium, `networkidle` + 2 s, `page.content()` | input of a rendering pipeline; the reference text the labeller sees |
| `landing.txt`, `imprint.txt` | `document.body.innerText` of the rendered page | text the label's verbatim fields are checked against |
| `landing.png`, `imprint.png` | full-page screenshot, 1280 px wide, up to 20,000 px tall | input of a vision pipeline; evidence for image-only addresses |
| `imprint.pdf` | the file itself, if the imprint is a PDF | PDF modality |
| `*.warc.gz` | Playwright requests recorded through `warcio` (a recording proxy such as `pywb`'s `wayback --record` or `warcprox` is the simpler route) | full replay; optional (see Open choices) |
| `meta.json` | UTC timestamps of each capture, final URLs, redirect chains, HTTP status, user agent, viewport, browser version, consent-banner action taken | provenance |

Rules:
- One capture per item, timestamped; the labeller labels from the frozen screenshot and DOM, opening the live site only to resolve something the capture lacks (and records that in `comment`).
- Cookie banners: click a "reject"/"only necessary" button if one matches a fixed list of labels; otherwise leave the banner. Record which.
- Release (D13 B): HTML, DOM text and screenshots are released with the gold set. WARCs are kept internally unless the user decides otherwise.

The pilot already stores static HTML, rendered DOM, rendered text and full-page JPEG screenshots for 1,000 hosts under `datasets/E8/{static,render}/<host>/` (no WARC).

## 4. Label schema, protocol and guideline v0.2

### Label schema (one JSON line per item)

```json
{
  "host": "example.de",
  "capture_id": "2026-11-05T10:12:03Z",
  "site_status": "live | unreachable | http_error | parked | redirect_other_domain | not_a_website",
  "imprint_present": true,
  "imprint_url": "https://example.de/impressum",
  "imprint_location": "separate_page | landing_page | modal | other_domain | pdf | none",
  "addresses": [
    {"role": "operator | operator_other_site | representative | editor | agency | host | other",
     "street": "Hauptstr.", "number": "12a", "postcode": "94032", "town": "Passau",
     "country": "Deutschland", "po_box": false,
     "modality": "text | image | pdf | js_only",
     "evidence": "verbatim text span (or 'image' for pixels)"}
  ],
  "main_address_index": 0,
  "no_address_reason": null,
  "operator_type": "corporate | association | public_body | sole_trader | private_person | unclear",
  "topic": "one of the 11 classes",
  "topic_ambiguous": false,
  "flags": ["multi_address", "po_box", "obfuscated", "non_dach"],
  "annotator": "A1",
  "seconds_spent": 140,
  "comment": ""
}
```

Changes from v0.1: all addresses on the imprint are listed with a role, not only the main one, so that multi-address errors (agency or hoster picked instead of operator) are visible; `modality` replaces `not_in_text` (D14 A: an address in an image is a gold address, tagged `image`); `no_address_reason` makes negatives explicit (`no_imprint`, `imprint_without_address`, `site_dead`); `operator_type` is a new label (it is also a stratum).

### Protocol (D15 C)

1. Freeze: capture the archive (section 3) for all items in one batch, then label within 30 days.
2. Annotator A labels every item from scratch, with no model output in view (no pre-labels; the stratum detectors are hidden too, so that they do not prime the label).
3. Annotator B independently labels a random 20% of items, drawn stratified by the sampling strata so that every stratum has at least 10 double-labelled items.
4. Agreement on the double-labelled items: per-field exact match for street, number, postcode, town (as written); location agreement by geocoding (D12; within 250 m on street level, same municipality on town level); Cohen's kappa for topic, operator type, imprint_present, no_address. Report per stratum where n >= 30.
5. Adjudication: A and B resolve all disagreements on double-labelled items; a third person decides if they cannot agree. Systematic disagreements lead to guideline v0.3 and a re-check of the affected field on A's single-labelled items (by A, with a filter, not a full relabel).
6. Calibration round first: both label the same 50 items (not part of the 20%), discuss, fix the guideline, then start.
7. Tool: a small local web form that shows the screenshot and DOM text side by side, with verbatim-span selection for address fields (copy, never type). Log time per item.

### Outline of guideline v0.2

1. What one item is: a host, its frozen capture (screenshot + DOM text), and the live site only as a fallback.
2. Site status and imprint presence (decision tree: is it a website? is there an imprint? where is it?).
3. Addresses: list every postal address on the imprint with its role; mark the main one (the § 5 DDG provider; headquarters if several); copy verbatim, town as written (D12); P.O. box; non-DACH; address split over lines; address in an image (`modality=image`); address that only appears after interaction (modal, accordion) counts.
4. Negatives: no imprint; imprint without an address (only e-mail/phone, or "address on request"); the operator's address on another site linked from the imprint (`role=operator_other_site`).
5. Operator type: five classes with tie-breakers (GmbH & Co. KG = corporate; e.K. and freelancers = sole trader; Verein, Stiftung, Partei, Kirchengemeinde = association; Gemeinde, Schule, Hochschule, Behörde = public body; a person with no business purpose = private person).
6. Topic: the 11 classes and tie-breakers from v0.1, judged on the homepage (D11).
7. Flags and comments; what to do when the capture is broken.
8. Worked examples: one per stratum, from the pilot (e.g. image-only address, multi-address with hoster, P.O. box, AT/CH, JS-rendered imprint).

## 5. Evaluation plan

The gold set evaluates the whole pipeline end to end, per host: starting from a host name, does the pipeline find the imprint, return the right main address (or correctly say "none"), and the right topic?

Metrics, all reported overall (weighted back to the population, section 2) and per stratum (unweighted, with 95% CIs):
- Imprint found: recall and precision against `imprint_present`.
- Address: on hosts with a gold address, exact match per field and full-address exact match; location match via geocoding (D12): within 250 m, same municipality. On negatives: the rate of hallucinated addresses (any address returned when the gold has none). Main-address choice on multi-address items.
- Topic: macro-F1 on the 11 classes (D5).
- Operator type: macro-F1 (new).

Comparisons:
1. Model comparison: the same pipeline with gemma4-31b-it, qwen38-27b and the other innkube models (and a paid API model within the spend limits), per stratum.
2. Pipeline variants: (a) static HTML text (the current `ic fetch` pipeline), (b) rendered DOM text (headless browser), (c) screenshot + vision model, (d) b with c only as fallback when b finds no address. The frozen archive makes these runs reproducible on identical input. The pilot predicts where the variants differ: (b) matters for the JS-required and blocked strata, (c) only for the image-only stratum, which is rare (section 2).
3. Error analysis by stratum: which strata drive the errors (e.g. multi-address, old sites, site builders).

## 6. Related work and what makes this gold set stand out

Web information extraction benchmarks:
- **SWDE** (Hao, Cai, Pang, Zhang: "From one tree to a forest: a unified solution for structured web data extraction", SIGIR 2011, DOI 10.1145/2009916.2010020): about 124k detail pages from 80 sites in 8 verticals (e.g. book, camera, university), with attribute values labelled per vertical. Sites were picked by hand, many pages per site; the task assumes the page is already found. **Expanded SWDE** (Lockard et al.: "OpenCeres: When Open Information Extraction Meets the Semi-Structured Web", NAACL 2019, N19-1309) adds open relation labels to a subset.
- **WebSRC** (Chen et al.: "WebSRC: A Dataset for Web-Based Structural Reading Comprehension", EMNLP 2021, 2021.emnlp-main.343): about 400k question-answer pairs over 6.4k pages, each with HTML and a screenshot.
- **Klarna Product Page Dataset** (Hotti et al.: "The Klarna Product Page Dataset: Web Element Nomination with Graph Neural Networks and Large Language Models", arXiv 2111.02168, TMLR 2024; data: Zenodo DOI 10.5281/zenodo.12605480): 51,701 product pages from 8,175 shops, each with a rendered DOM snapshot (MHTML) and a screenshot; the task is to nominate the element holding e.g. the price.

Address extraction:
- **Schmidt, Manschitz, Rensing, Steinmetz**: "Extraction of Address Data from Unstructured Text using Free Knowledge Resources", i-KNOW 2013, ACM, 7:1-7:8, DOI 10.1145/2494188.2494193. Extracts German postal addresses from unstructured web text using free knowledge resources such as OpenStreetMap; closest prior task to ours, but on text, with no page discovery, no negatives and no rendering or image cases.
- **Ahmadi, Bernhard, Abdelmaksoud, Zecchini, Rabl, Abedjan**: "Clean Me If You Can: A Large Collection of Real-World Addresses for Data Cleaning Benchmarking", arXiv 2606.31983 (2026). Real-world address records for data cleaning, not extraction from web pages.

Measuring how the web is built:
- **HTTP Archive Web Almanac** (2024 methodology): technology detection with a fork of Wappalyzer on millions of crawled pages. Our technology detector follows the same signature approach (generator meta tag, asset paths, cookies, headers), with a small hand-written rule set.

What makes this gold set stand out:
1. **Probability sample of a real crawl frame, not hand-picked sites.** Items are drawn from the 6.56M-host seed list with known inclusion probabilities, so every metric can be reported both per stratum and weighted back to the population. SWDE, WebSRC and Klarna pick sites by hand or by vertical; none supports population estimates.
2. **Strata for how the page was produced**: site age (Wayback), technology (WordPress, site builders, Blogger, hand-written HTML, desktop editors, SPA frameworks), rendering need (static vs. JS) and modality (text, image, PDF), each with an automatic, tested detector and measured detector precision. Existing benchmarks describe sites by topic vertical only.
3. **End-to-end task including negatives**: from a host name to "the operator's address, or none". About 40% of live German sites have no imprint the pipeline can reach, and some imprints have no address. Benchmarks above assume the target page exists and the answer is on it.
4. **Multimodal frozen archive per item** (static HTML, rendered DOM, full-page screenshot, timestamps), so the same items compare a static, a rendering and a vision pipeline on identical input (as WebSRC and Klarna do for QA and element nomination, but here for a whole-site task).
5. **A legally defined genre**: the imprint (§ 5 DDG in Germany, § 5 ECG and § 25 MedienG in Austria, Art. 3 para. 1 let. s UWG in Switzerland) gives a precise, checkable definition of the right answer (the provider's address), which makes labels less subjective than generic "contact address" tasks.
6. **Independent double annotation (D15 C) with agreement per stratum**, labelled from scratch without model pre-labels, so model comparisons are not biased toward the pre-labelling model.

## 7. Open choices (need the user)

These are design choices the pilot cannot settle. Each has a recommendation.

1. **Total size.** About 1,300 items (600 core + about 700 oversample), about 80 annotator hours in total. A leaner variant is about 1,100 items (topic minimums dropped, static/custom-PHP minimums at 50). *Recommendation:* 1,300. It is the smallest set that gives ±10 pp per primary stratum and still has a random core large enough for population figures.
2. **Frame: everything vs. German-language/DACH only.** 75% of live hosts on non-DACH TLDs have no imprint the detectors reach (mostly foreign sites in the seed list), against 12% on .de/.at/.ch. *Recommendation:* keep the full frame (the dataset is built from it, and these hosts are real negatives the pipeline must reject), but cap the "no imprint" negatives in the oversample at what the core brings (about 160).
3. **Operator-type detector for stratification.** Rules were right on 6/13 decidable spot-checks, the LLM (gemma4-31b-it on innkube, free) on 12/13. *Recommendation:* use the LLM for stratification only. It never reaches the labellers (D15 C).
4. **WARC capture.** Static HTML, rendered DOM, screenshots and HAR-like metadata are archived for every item (D14 A). A full WARC (e.g. via `warcio` around the static fetch) adds re-playability but also third-party content of uncertain licence. *Recommendation:* capture WARC for internal reproducibility, but do not publish it. Publish HTML, DOM text and screenshots where licensing allows, with URLs and timestamps otherwise.
5. **Image-only (screenshot-required) quota.** The pilot measured 2 of 422 imprints (0.5%, CI 0.1-1.7). *Recommendation:* a small quota of 20, found by screening, so the paper can show the failure mode and the vision fallback. Option: 0, reporting only the natural occurrences in the core (about 1).
6. **Capture infrastructure.** Strato-hosted sites (about 8% of the sample) answered 503 to the crawl VM during the pilot, Wix 429 and Jimdo 403 to the static client. *Recommendation:* run the gold capture from a different IP (e.g. a FAITH Slurm node) at low per-host-provider concurrency, and re-try blocked hosts before they count as negatives.

## 8. Open doubts

- **Crawl blocks bias the pilot prevalences.** The Strato 503 block makes 13% of hosts look dead. Many of them had an imprint in E4. Live-site shares are therefore biased low, and per-provider strata (Strato site builder) are undercounted.
- **Vision is a weak detector.** gemma4-31b-it reads addresses off screenshots with OCR digit slips and occasionally invents addresses. 2 of 4 image-only flags were genuine. Every image-only candidate needs a human look before it is drawn.
- **Age measures the domain, not the current site.** A redesign does not change the bin. The copyright year is recorded as a second signal. 14 hosts had unparsable CDX answers.
- **Detectors are heuristic.** Spot-checks are 20 per detector (fewer for rare ones). Precision estimates have wide CIs. Recall was not measured, except indirectly against E4 for imprint discovery.
- **Topic and operator type** from the LLM were checked only by the spot-check above (topic not at all here; E7 covers topic models on the old set).
- **Imprint discovery misses.** `none` was wrong for 1 of 12 checked (a Shopify imprint under `/policies/legal-notice`), so the "no imprint" stratum contains some positives. The labellers decide from the live site, so labels are not affected.
