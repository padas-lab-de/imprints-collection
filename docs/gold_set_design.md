# Gold set design: a diversity-stratified gold set for German imprints

Status: v0.2 (2026-10-24). v0.1 came from E8-gold-strata-pilot; v0.2 rewrites §2 and §7 for 1,000 items after the E12 screening of 10,000 hosts and records the drawn sample. Decisions it depends on: D12 (town copied as written, location scored by geocoding), D14 A (labels from the live rendered site; HTML, rendered DOM and screenshot archived), D15 C (one human labels every item from scratch; a second human independently labels about 20%; no model pre-labels; superseded by D24 B: every item starts from a model suggestion), D17 B (1,000 items, no head-to-head comparison of site groups). Points that need the user are under "Open choices".

The new set replaces the old 1,000-item gold set. The old set has exactly one address per item, 999 of them in Germany, and no negatives (lead record, gold audit). So it cannot measure no-address answers, AT/CH sites, multiple addresses or how pages are produced.

## Summary

- **Design (D17 B)**: 1,000 hosts, a two-phase probability sample. Phase 1: a simple random sample of 10,000 hosts from the frame, screened with the detectors (E12). Phase 2: (1) a **random core** of 700 hosts, an SRS on its own, for population figures; (2) a **coverage oversample** of 300 hosts so that every diversity stratum has about 30 items where the population allows. Every item has a known inclusion probability and a Horvitz-Thompson design weight. There are no per-stratum precision targets, because the paper does not compare site groups head to head.
- **Strata**: age, technology, rendering need, operator type, TLD (.at, .ch), imprint location, rare topics, and hard cases (imprint without an address, P.O. box, multiple addresses, obfuscation, image-only). Each has an automatic, unit-tested detector (E8).
- **Screening E12** (10,000 hosts, seed 20261024, full seed list minus the E8 and old gold hosts): 71.4% are live, and 57.7% of the live hosts have an imprint the detectors reach. Among live .de/.at/.ch hosts, 16.3% have no imprint. WordPress is 32% of live sites and site builders 11%. 1.2% of live sites need JavaScript for the imprint. Hand-confirmed image-only addresses: 15 of 4,129 imprints (0.36%, CI 0.22-0.60%). PDF imprints: 3 of 7,137.
- **Drawn sample**: `datasets/E12/gold_sample.jsonl`, 1,000 items (700 core + 300 oversample), with 799 live and 420 negatives from the core (219 with no imprint, 201 not live). Quotas, inclusion probabilities and achieved counts are in §2.
- **Screenshot-required is an edge case.** It gets every confirmed case (15, cap 20) and is otherwise not built around. Screenshots are archived for every item anyway (D14 A).

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

The frame is `seed_hosts.txt.gz` (6,560,119 hosts), the same list the dataset is built from, so that gold-set results speak for the dataset. E12 excludes the 2,400 hosts of the E8 pilot and of the old gold set (www variants included), so the frame is **6,557,719** hosts. It is the full frame, not DACH-only (§7.2): non-DACH hosts are real negatives the pipeline must reject. "No imprint" negatives come only from the random core (§7.2).

### Screening (E12, 10,000 random hosts)

Script `scripts/gold/e12_screen.py`, run by `scripts/gold/e12_run.sh` (2026-10-23 to 2026-10-24). Stages as in E8:
- static fetch;
- render (headless Chromium);
- Wayback CDX (at most 1 request/s);
- LLM text features (gemma4-31b-it on innkube, free);
- vision, run only on image-only candidates (707 hosts).

Rate limits:
- **at most 1 concurrent request per provider (IPv4 /24)**, with a gap between hosts of the same /24;
- one retry of all 403/429/503 hosts (1,381) after a pause.

Outputs: `results/E12/screening_features.jsonl` (one record per host) and `results/E12/screening_prevalence.md` (Wilson CIs, with Newcombe CIs for the difference from E8).

| Count | n | % | 95% CI |
|---|---|---|---|
| screened | 10,000 | | |
| DNS resolves | 9,430 | 94.3 | |
| live | 7,137 | 71.4 | 70.5-72.2 |
| http_error (Strato 503 block: 578) | 1,257 | 12.6 | 11.9-13.2 |
| unreachable | 745 | 7.5 | 7.0-8.0 |
| redirect to another domain | 690 | 6.9 | 6.4-7.4 |
| parked / placeholder / challenge / default | 171 | 1.7 | |
| live with an imprint the detectors reach | 4,117 | 57.7 of live | 56.5-58.8 |
| + hand-confirmed image-only imprints the detectors missed | 12 | | |
| no imprint, live .de/.at/.ch | 662 | 16.3 of 4,050 | 15.2-17.5 |
| no imprint, live other TLDs | 2,358 | 76.4 | 74.9-77.8 |
| JS-required imprint | 83 | 1.2 of live | 0.9-1.4 |
| imprint on another domain | 87 | 1.2 of live | 1.0-1.5 |
| P.O. box | 95 | 2.3 of imprints | 1.9-2.8 |
| address only in an image (hand-confirmed) | 15 | 0.36 of 4,129 | 0.22-0.60 |

The retry recovered 317 of the 1,381 blocked hosts. The Strato block did not lift (§8). Most shares agree with E8 within the CIs. Differences whose CI excludes 0 (out of about 300 comparisons, so a few are expected by chance):
- **No imprint on live .de/.at/.ch: 16.3% vs 12.1%.**
- **Age bins:**
  - <2010: 42.9% vs 38.7% of all hosts.
  - >=2023: 10.1% vs 12.3%.
  - no Wayback capture: 1.6% vs 3.2%. The slower CDX rate gave fewer errors.
- **Topics:**
  - Health and Medicine: 12.1% vs 16.6% of imprints.
  - Business and Professional Services: 36.9% vs 32.0%.
- **Minor:** ASP.NET (2.3% vs 3.6% of live) and default pages (0.2% vs 0.8%).
- **Vision:** `image_only_address` differs by design, because vision ran on candidates only.

### Design: random core + priority-stratified oversample, with design weights

Code: `src/ic/gold/sampling.py` (tests in `tests/test_gold_sampling.py`), driver `scripts/gold/e12_sample.py draw` (seed 20261025).

1. **Memberships.** Each screened host belongs to a set of coverage strata (list below). A host that is not live belongs only to `neg:site_not_live`. A live host without a detected imprint belongs only to `neg:no_imprint`, unless it is a hand-confirmed image-only imprint. Coverage strata:
   - age bin;
   - technology family: WordPress, custom PHP, site builder, SPA, shop, static HTML, other CMS, custom other, Blogger; plus "PHP anywhere";
   - JS-required;
   - LLM operator type, used for stratification only and never shown to labellers;
   - `.at`, `.ch`;
   - imprint on another domain;
   - imprint without a text address, or image-only (hand-confirmed);
   - P.O. box;
   - multiple addresses (rules, or LLM >= 2);
   - obfuscation;
   - rare topics (Event, Dining and Drinking, Landmarks and Outdoors, Nightlife Spot).
2. **Priority stratum.** Each host's priority stratum is its rarest coverage stratum, with image-only always first. Negatives keep their negative stratum.
3. **Core.** The core is the first n0 hosts of a seeded permutation of the 10,000, so it is an SRS of the frame.
4. **Oversample.** Rarest stratum first, hosts are drawn at random from the not-yet-selected hosts whose priority stratum is h. Drawing stops when stratum h's marginal count in the sample (core and extras, counting every membership) reaches the target T, or when the pool is empty. Image-only is capped at 20. Negatives are never oversampled.
5. **Choice of n0 and T.** Take the largest T in 20-30 for which some n0 in 600-700 gives n0 + oversample <= 1,000. Then take the largest such n0. Leftover budget goes to further passes at T+1, T+2, ... (rarest first). Result: **T = 30, n0 = 700**, 233 extras in the first pass and 67 in later passes up to 37.
6. **Weights.** Within priority stratum h, the m_h selected hosts are a uniform random subset of the M_h screened hosts. So, conditional on the realized stratum sizes, the inclusion probability is **pi = (10,000 / 6,557,719) x m_h / M_h**, and the design weight is 1/pi (Horvitz-Thompson; Hajek for ratios). Each item stores `pi_phase2`, `inclusion_probability` and `design_weight`. Weights range from 656 (pi2 = 1) to 16,582. They add up to 6,555,096. The missing 2,623 belong to 4 screened hosts whose priority strata got no item (M_h <= 2, m_h = 0); their share is negligible. Report results per stratum by the label's *true* stratum, unweighted, next to the weighted population figures.

### Quota table (final, E12 draw)

"Screened" counts every membership among the 10,000 hosts. "Target" is the common T, or the cap. "In sample" is the marginal count among the 1,000 items. "m_h / M_h" counts hosts whose *priority* stratum is h. pi phase 2 = m_h / M_h.

| Stratum | Screened (of 10,000) | % (of screened w/ imprint; negatives: of all) | Expected in core | Target | In sample | of which core | Priority-stratum items (m_h / M_h) | pi phase 2 |
|---|---|---|---|---|---|---|---|---|
| modality:image_only | 15 | 0.4 | 1.1 | 20 | 15 | 2 | 15 / 15 | 1.0000 |
| topic:Nightlife Spot | 3 | 0.1 | 0.2 | 30 | 3 | 0 | 3 / 3 | 1.0000 |
| tech:blogger | 8 | 0.2 | 0.6 | 30 | 8 | 0 | 8 / 8 | 1.0000 |
| topic:Landmarks and Outdoors | 13 | 0.3 | 0.9 | 30 | 13 | 2 | 13 / 13 | 1.0000 |
| hard:imprint_without_address | 42 | 1.0 | 2.9 | 30 | 37 | 4 | 37 / 42 | 0.8810 |
| topic:Event | 52 | 1.3 | 3.6 | 30 | 37 | 4 | 37 / 52 | 0.7115 |
| tech:custom_other | 63 | 1.5 | 4.4 | 30 | 37 | 2 | 36 / 62 | 0.5806 |
| op:private_person | 74 | 1.8 | 5.2 | 30 | 37 | 8 | 27 / 63 | 0.4286 |
| render:js_required | 81 | 2.0 | 5.7 | 30 | 37 | 10 | 29 / 71 | 0.4085 |
| loc:other_domain | 87 | 2.1 | 6.1 | 30 | 37 | 7 | 28 / 69 | 0.4058 |
| hard:po_box | 95 | 2.3 | 6.7 | 30 | 37 | 7 | 35 / 87 | 0.4023 |
| topic:Dining and Drinking | 144 | 3.5 | 10.1 | 30 | 37 | 12 | 34 / 137 | 0.2482 |
| tech:spa | 168 | 4.1 | 11.8 | 30 | 37 | 14 | 16 / 125 | 0.1280 |
| tld:ch | 201 | 4.9 | 14.1 | 30 | 37 | 15 | 23 / 169 | 0.1361 |
| tech:static_html | 218 | 5.3 | 15.3 | 30 | 38 | 12 | 19 / 181 | 0.1050 |
| tech:shop | 224 | 5.4 | 15.7 | 30 | 36 | 14 | 28 / 198 | 0.1414 |
| op:public_body | 227 | 5.5 | 15.9 | 30 | 39 | 12 | 14 / 163 | 0.0859 |
| tld:at | 262 | 6.3 | 18.3 | 30 | 41 | 21 | 16 / 189 | 0.0847 |
| tech:custom_php | 325 | 7.9 | 22.8 | 30 | 47 | 19 | 12 / 216 | 0.0556 |
| age:>=2023 | 529 | 12.8 | 37.0 | 30 | 85 | 37 | 27 / 296 | 0.0912 |
| tech:site_builder | 537 | 13.0 | 37.6 | 30 | 57 | 37 | 20 / 345 | 0.0580 |
| op:association | 573 | 13.9 | 40.1 | 30 | 90 | 40 | 19 / 295 | 0.0644 |
| tech:cms_other | 757 | 18.3 | 53.0 | 30 | 91 | 56 | 31 / 359 | 0.0864 |
| age:2018-2022 | 958 | 23.2 | 67.1 | 30 | 129 | 65 | 15 / 294 | 0.0510 |
| tech:php_any | 983 | 23.8 | 68.8 | 30 | 115 | 57 | 7 / 177 | 0.0395 |
| age:2010-2017 | 1304 | 31.6 | 91.3 | 30 | 188 | 95 | 15 / 253 | 0.0593 |
| age:<2010 | 1321 | 32.0 | 92.5 | 30 | 171 | 81 | 16 / 243 | 0.0658 |
| hard:multi_address | 1428 | 34.6 | 100.0 | 30 | 181 | 91 | 0 / 2 | 0.0000 |
| hard:obfuscation | 1441 | 34.9 | 100.9 | 30 | 186 | 102 | 0 / 1 | 0.0000 |
| tech:wordpress | 1529 | 37.0 | 107.0 | 30 | 175 | 100 | 0 / 0 | 0.0000 |
| op:sole_trader | 1608 | 38.9 | 112.6 | 30 | 174 | 108 | 0 / 0 | 0.0000 |
| op:corporate | 1622 | 39.3 | 113.5 | 30 | 228 | 112 | 0 / 1 | 0.0000 |
| neg:no_imprint | 3008 | 30.1 | 210.6 | core only | 219 | 219 | 219 / 3008 | 0.0728 |
| neg:site_not_live | 2863 | 28.6 | 200.4 | core only | 201 | 201 | 201 / 2863 | 0.0702 |

Items per priority stratum: neg:no_imprint 219, neg:site_not_live 201, topic:Event 37, hard:imprint_without_address 37, tech:custom_other 36, hard:po_box 35, topic:Dining and Drinking 34, tech:cms_other 31, render:js_required 29, tech:shop 28, loc:other_domain 28, age:>=2023 27, op:private_person 27, tld:ch 23, tech:site_builder 20, op:association 19, tech:static_html 19, tech:spa 16, age:<2010 16, tld:at 16, age:2010-2017 15, modality:image_only 15, age:2018-2022 15, op:public_body 14, topic:Landmarks and Outdoors 13, tech:custom_php 12, tech:blogger 8, tech:php_any 7, topic:Nightlife Spot 3.

Shortfalls (the whole screened pool is used, pi2 = 1):
- Nightlife Spot: 3 items.
- Blogger: 8 items.
- Landmarks and Outdoors: 13 items.
- Image-only: 15 items (cap 20).

Every other stratum reached at least 36. Common strata exceed T through the core alone.

Labelling effort (D15 C): about 3 minutes per item. That gives about 50 h for annotator A, 10 h for annotator B on 20%, plus about 5 h of calibration.

Screenshot-required: 15 hand-confirmed cases, all in the sample. The rule: the address is visible on the screenshot, sits in an `<img>`, and is missing from the extracted text. The list and the reasons for rejecting the other 18 vision flags are in `datasets/E12/image_only_confirmed.txt`. 12 of the 15 were missed by the imprint detector entirely: with no address text, the page did not look like an imprint. They enter as image-only, not as "no imprint".

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

## 4. Label schema, protocol and guideline

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
5. Adjudication: A and B resolve all disagreements on double-labelled items; a third person decides if they cannot agree. Systematic disagreements lead to a guideline update and a re-check of the affected field on A's single-labelled items (by A, with a filter, not a full relabel).
6. Calibration round first: both label the same 50 items (not part of the 20%), discuss, fix the guideline, then start.
7. Tool: a small local web form that shows the screenshot and DOM text side by side, with verbatim-span selection for address fields (copy, never type). Log time per item.

### Outline of the guideline

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

Settled by D17 B (1,000 items, no head-to-head comparisons) and applied in E12. The defaults below were taken as assumed choices. Each can still be overruled.

1. **Total size.** 1,000 items: 700 random core + 300 coverage oversample, about 30 per stratum where the population allows (§2). *Applied.*
2. **Frame: everything vs. German-language/DACH only.** Full seed-list frame. "No imprint" negatives come only from the core (219 items), and non-live hosts likewise (201 items). *Applied (assumed).* Option: drop the 201 non-live core items and replace them with live core items. This would save labelling time, but the core would then no longer be an SRS of the frame (it would become an SRS of live hosts).
3. **Operator-type detector for stratification.** The LLM (gemma4-31b-it on innkube), for stratification only. Never shown to labellers (D15 C). *Applied (assumed).*
4. **WARC capture.** Capture WARC for internal reproducibility, but do not publish it. *Assumed.*
5. **Image-only quota.** Cap 20; screening found 15, and all are in the sample. *Applied.*
6. **Capture infrastructure.** The E12 screening still ran from the crawl VM, with at most 1 request per /24 and one retry. Strato kept answering 503 (578 hosts, 5.8% of the screening sample, 39 items of the `neg:site_not_live` core). *Recommendation:* capture the 1,000 gold items from a different IP (e.g. a FAITH Slurm node), and re-try blocked hosts there before they count as negatives.

## 8. Open doubts

- **Crawl blocks bias the pilot prevalences.** The Strato 503 block makes 13% of hosts look dead. Many of them had an imprint in E4. Live-site shares are therefore biased low, and per-provider strata (Strato site builder) are undercounted.
- **Vision is a weak detector.** gemma4-31b-it reads addresses off screenshots with OCR digit slips and occasionally invents addresses. 2 of 4 image-only flags were genuine. Every image-only candidate needs a human look before it is drawn.
- **Age measures the domain, not the current site.** A redesign does not change the bin. The copyright year is recorded as a second signal. 14 hosts had unparsable CDX answers.
- **Detectors are heuristic.** Spot-checks are 20 per detector (fewer for rare ones). Precision estimates have wide CIs. Recall was not measured, except indirectly against E4 for imprint discovery.
- **Topic and operator type** from the LLM were checked only by the spot-check above (topic not at all here; E7 covers topic models on the old set).
- **Imprint discovery misses.** `none` was wrong for 1 of 12 checked (a Shopify imprint under `/policies/legal-notice`), so the "no imprint" stratum contains some positives. The labellers decide from the live site, so labels are not affected.
- **E12: Strato block persists.** 578 of 642 Strato-hosted hosts (/24 81.169.145.0) answered 503 even at 1 concurrent request and after the retry. They are in `neg:site_not_live`. Live and imprint shares stay biased low by about 5 pp, and Strato-hosted site builders are undercounted.
- **E12: inclusion probabilities are conditional** on the realized screening stratum sizes and on detector outputs. A detector error changes only an item's weight, not its labelled stratum.
- **E12: the image-only search is bounded by the vision candidate rule** (707 candidates). Image-only cases outside that rule are missed. Iframe-embedded imprints (4 seen) and pages whose rendered text is missing from the extraction (3 seen) are hard cases with no stratum of their own.
- **E12: some flagged differences vs E8 are likely chance.** There were about 300 comparisons at 95%. The higher no-imprint share on .de/.at/.ch (16.3% vs 12.1%) is the one that matters for the design and is unexplained (E8's E4 merge only adds fields, it does not change the detector). It changes only the core's expected negatives.
- **E12: T and n0 were chosen from the screening data** (largest T, then largest n0, that fit 1,000). This is a deterministic rule fixed before the draw, so weights stay valid.

