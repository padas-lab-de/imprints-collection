# E5: Why do 1,811 reachable .de hosts have no imprint?

Date: 2026-10-23. Analysis only; no files under `src/` were changed.

## Question and sample

Of 8,917 reachable .de hosts in `datasets/E4/random20k/imprints_batch000000.jsonl.gz`, 1,811 have no `impressum` record (79.7% found). Which of these are detection misses of `src/ic/cli/fetch.py` and which are not?

Sample: all .de hosts with a record but no `impressum` key, sorted alphabetically, then `random.seed(20261023); random.sample(list, 200)`. Sample list: `scratchpad/E5/sample.json`. Per-host labels: `results/E5/classifications.jsonl` (gitignored).

## Method

1. Re-fetch the landing page with `requests` (desktop Chrome UA, `Accept-Language: de-DE`, timeout 15 s, redirects followed, 4 parallel workers, 0.3 s pause between probes).
2. Replicate `discover_links()` offline with the same `resiliparse` parser (script `collect.py`) and replay the crawler's own fetch logic (UA `Mozilla/5.0`, `allow_redirects=False` manual follow, `content_length` from `extract_plain_text(main_content=True)`) in `replay.py`, to see which step of `process_host` drops the imprint.
3. Broad anchor scan (`impressum|imprint|legal notice|anbieterkennzeichnung|rechtliche hinweise|rechtliches|kontakt|...`, including `title`, `aria-label`, `<img alt>`), `<base href>` check, framework/parking/challenge keyword scan, `/impressum` and `/impressum.html` probes when no link exists, and a Kontakt-page check for hosts that looked genuinely imprint-free.
4. Hand review of every borderline host. One primary cause per host (priority: reproducible fetch.py defect first, then page state).
5. For hosts that now return 503/unreachable (20 hosts, all Strato IPs 81.169.145.x / 193.141.3.x, 503 persisted over ~10 min and retries) the crawl-time record (`main_content`, keys) and the earlier replay were used where possible; 7 stay "unverifiable".

What fetch.py actually does (relevant facts found while reading):
- `discover_links` keeps one entry per URL **path** (`discovered_links[parsed_url.path]`); a later link with the same path (e.g. `/`, `/index.php`, or the same page with a different query) overwrites the earlier one, including its anchor text.
- A link matches only if the substring `impressum` is in the **path** or in the anchor's own text (not query string, not `title`/`alt`, not "imprint"/"legal notice"). Other-host links are accepted (only social/shop hosts are filtered).
- Among matching links the shortest absolute URL wins; only that one URL is fetched, no fallback.
- `<base href>` is ignored; only HTTP 200 counts (non-redirect 3xx are followed); a fetched page is kept only if `content_length > 0`, where `content_length` comes from main-content extraction (`main_content=True`).
- Status "imprint_not_found" is thus: no matching link, fetch failed, or empty main content.

## Results (n = 200)

| Cause | n | % of 200 | 95% Wilson CI |
|---|---|---|---|
| Parked / for sale / maintenance / default or error page | 41 | 20.5 | 15.5-26.6 |
| Empty body, JS-only / SPA / loader (no static content or links) | 35 | 17.5 | 12.9-23.4 |
| **Missed by rules (usable imprint link/page in static HTML)** | 34 | 17.0 | 12.4-22.8 |
| - imprint page fetched but `content_length == 0` (main-content extraction empty) | 10 | 5.0 | 2.7-9.0 |
| - link has query string / shares path with other links (`?id=183`, `index.php?site=imprint`, `?page_id=21`) | 10 | 5.0 | 2.7-9.0 |
| - other label (Imprint, Legal Notice, Rechtliche Hinweise, Rechtliches) | 7 | 3.5 | 1.7-7.0 |
| - `<base href>` ignored (relative link resolved to 404) | 4 | 2.0 | 0.8-5.0 |
| - wrong candidate kept by path-keyed dict (staging host, WP draft-preview URL) | 2 | 1.0 | 0.3-3.6 |
| - anchor text only in `<img alt>` | 1 | 0.5 | 0.1-2.8 |
| Genuinely no imprint (real site, no link, /impressum 404, no legal data) | 23 | 11.5 | 7.8-16.7 |
| Redirect to unrelated site, or spam/hijacked content | 14 | 7.0 | 4.2-11.4 |
| Imprint link found but target failed | 12 | 6.0 | 3.5-10.2 |
| - other host (parent company, website builder), 403/404 | 5 | 2.5 | 1.1-5.7 |
| - 5xx or redirect loop on imprint URL | 3 | 1.5 | 0.5-4.3 |
| - transient (works now, failed/timed out at crawl) | 3 | 1.5 | 0.5-4.3 |
| - dead link (404) | 1 | 0.5 | 0.1-2.8 |
| Imprint content on the landing page itself (`#impressum`, modal, JS toggle, single page) | 10 | 5.0 | 2.7-9.0 |
| No link, but `/impressum` exists and is a real imprint | 9 | 4.5 | 2.4-8.3 |
| Web app / login / booking portal / auth wall | 8 | 4.0 | 2.0-7.7 |
| Unverifiable (host 503 now, real content at crawl time) | 7 | 3.5 | 1.7-7.0 |
| Legal-entity data only on the Kontakt page | 3 | 1.5 | 0.5-4.3 |
| Bot challenge / human verification | 3 | 1.5 | 0.5-4.3 |
| Other ("Impressum" menu item links to `/`) | 1 | 0.5 | 0.1-2.8 |

Reading: roughly 37% of the sample (parked, JS/empty, redirect/spam, app, challenge) are sites without a crawlable static imprint at all; about 11.5% (+ some of the 7 unverifiable) are genuine omissions; **about 21% (42/200, CI 15.9-27.2%) are plain detection misses fixable with static-HTML rules**, up to 29% (58/200, CI 23.2-35.6%) if content-on-landing, Kontakt-page imprints and retries are counted.

### Extrapolation (assumptions)

Assumptions: the 200 are a simple random sample of the 1,811 (yes); crawl conditions and site state at re-fetch resemble the crawl (violated for the 20 now-503 hosts, handled above); the 1,811 are representative of .de hosts in the full seed list (random20k is a random draw from `seed_hosts.txt.gz`; the file contains 3,428,132 .de of 6,560,119 hosts; random20k has 10,682 .de, 8,917 reachable = 83.5%).

- To the 1,811: static-HTML rule misses 42/200 = about 380 hosts (CI 288-493), which would lift the found rate from 79.7% to about 84.0% of reachable .de hosts (+4.3 pp); all misses incl. F7-F9 about 525 hosts (+5.9 pp).
- To all .de seeds: 3,428,132 x 83.5% reachable = about 2.86 M reachable; x 20.3% no-imprint = about 581 k; static-rule misses about 122 k hosts (CI 92-158 k), all misses about 168 k. This assumes the .de share and the reachable/no-imprint rates of the 20k sample hold for the full list; the 20k sample ordering/seed-list composition was not independently checked.
- Cluster warning: 4 of the 10 empty-main-content cases are the same Caritas CMS; the sample is not independent across hosts of a common CMS/hosting provider, so CIs are optimistic.

## Proposed rule changes (not applied), ranked by recovered hosts

Counts are hosts of the 200 for which the fix is the primary recovery (verified target returns 200 with imprint content; one fix per host to avoid double counting).

1. **F2: key links by full URL and match on path + query + anchor text, try candidates in turn (11 hosts, 5.5%, about 100 of 1,811).**
   In `discover_links`, replace `discovered_links[parsed_url.path]` by a list of `(abs_url, anchor_text)`; test the keyword against `path + "?" + query` and the anchor text; collect all matches, order by (own host first, shortest), and in `process_host` try them until one returns usable content. Fixes `?id=183`, `index.php?id=impressum`, `?page_id=21`, `index.php?site=imprint` (10) and the staging-host duplicate on berning-net.de (1). Dead links (chinesische-schule-stuttgart.de, 404) and the WP draft-preview link on car-art-work.de are not recoverable.
2. **F1: do not discard imprint pages with empty main-content (10 hosts, 5%, about 91).**
   Pages were fetched with 200 and clear imprint text (Caritas CMS x4, drg-evaluation.de, mediathek.vrm.de, maafischer-viereth.de, autoabo.schneider-mobility.de, 2 Strato hosts), but `extract_plain_text(main_content=True)` returned 0 chars because the short page is classified as boilerplate. In `process_host`, if `content_length == 0` re-run extraction with `main_content=False` (or keep the page when the visible body text is non-empty). No extra requests needed.
3. **F5: URL-probe fallback when no link matched (9 hosts, 4.5%, about 81).**
   If no matching link exists (or all candidates fail), try `/impressum`, `/impressum.html`, `/imprint` on the final host; accept only 200 responses whose text contains `impressum`, `angaben gemäß`, or `§ 5 TMG/DDG` and which differ from the landing page. Recovers onclick-button menus (chor-schoenwalde.de), JS-injected or unlinked footers (designbybine.de, dr-med-kropp.de, bridgeofhope.de, cappugino.de, awinnovationcenter.de, okami-restaurant.de, 3dreamsdesign.de, buchwissenschaft.uni-mainz.de). Cost: +1-3 requests for roughly the 20% of hosts without imprint; soft-404s need the text check.
4. **F3: extend keywords (7 hosts, 3.5%, about 63):** add `imprint`, `legal-notice`/`legal notice`, `rechtliche hinweise`, `rechtliches`, `anbieterkennzeichnung`, `impressum` in `title`/`aria-label`. Beware `legal` alone (privacy/terms false positives, e.g. vercel.com `/legal/terms`). contact2me.de ("Legal Notice", 371 chars) is the weakest of the 7.
5. **F4: honour `<base href>` (4 hosts, 2%, about 36):** `base = urljoin(final_url, tree.head.query_selector("base[href]").getattr("href"))` before `urljoin(base, href)`. Recovers 4cats.de, dr-rauwald.de, agtiere.de, dasekg.de.
6. **F9: retry once on timeout/5xx for imprint fetches (3 hosts, 1.5%, about 27):** thermag-gmbh.de (slow 1.3 MB page), fengshui-raumplanung.de (Strato 503), caravanskopp.de.
7. **F8: Kontakt page as imprint fallback (3 hosts, about 27):** the kontakt page is already fetched; if there is no imprint and the Kontakt page text has `Impressum`/`USt-IdNr`/`Umsatzsteuer-ID`, store it as imprint (dryandcool.de, bessernaehen.de, media-service-grade.de). Quality question: these are legally imprints but not labelled.
8. **F7: imprint on the landing page (10 hosts, 5%, about 91):** if a `#impressum`/`javascript:...('impressum')` anchor exists, or landing text matches `Angaben gemäß § 5`, `Handelsregister`/`USt-Id` plus the word Impressum, mark the landing page itself as imprint (ahcg.de, drhofmann-kinderarzt.de, bergstrassen-cup.de, lisazennerart.de, dr-spitznagel.de, cantinacatering.de). This is a semantic decision (the landing record then doubles as imprint) and would need a precision check on the found set.
9. **F6: `<img alt>`, `title`, `aria-label` text (1 host, about 9).**

Static-HTML rule changes F1+F2+F3+F4+F5+F6: 42/200 = 21% (CI 15.9-27.2%). With F7-F9: 58/200 = 29% (CI 23.2-35.6%).

Not addressable by fetch.py rule changes: imprint links to other hosts that return 403/404 to us (westenergie.de, dewezet.de, tilda.ws, buerger-geld.de; 5 hosts, bot blocking or dead), 5xx/redirect loops (podcaster.de, helicobacter-testen.de), JS-only sites (35, would need rendering; for the 3 chayns.de sites the imprint is a JS tapp), parked/placeholder sites (41), spam/hijacked or redirected sites (14).

## Examples per category

- Parked/placeholder: `chrisford.xxx-kaufen.de` (domain for sale), `vs-buckenhofen-burk.de` (Plesk default), `www.dawnmusic.de` (Strato "domain reserved").
- JS/empty: `drweber-quickborn.de` (empty `<div id="root">`), `hoch-m.de` ("Loading..."), `thermalhotel-kemper.de` (chayns app; imprint only in JS config).
- Rule miss, query string: `schuetzen-salzkotten.de` (`?id=183`, text "Impressum"), `terontec.de` (`index.php?site=imprint`), `windsurfingclub.de` (`?page_id=21`).
- Rule miss, label: `dr-nibler.de` ("IMPRINT" `/imprint/`), `www.campingplatz-porto-vecchio.de` ("Rechtliche Hinweise"), `mahara.europa-uni.de` ("Rechtliches" `legal.php`).
- Rule miss, base href: `dr-rauwald.de` (`<base href="https://dr-rauwald.de/">`, link `de/impressum.html` resolved to `/de/de/impressum.html`), `4cats.de`.
- Rule miss, empty main-content: `www.caritas-limburg.de`, `drg-evaluation.de`, `maafischer-viereth.de`.
- Imprint at guessable URL, no link: `designbybine.de`, `dr-med-kropp.de`, `chor-schoenwalde.de` (nav is `<button onclick="x5engine.utils.location('impressum.html')">`).
- Imprint on landing page: `www.ahcg.de` (`#impressum`), `dr-spitznagel.de` (`javascript:unhide('impressum')`), `www.bestattungen-griese.de` ("Impressum & Datenschutz" modal; the plain `/Impressum` link is a 404).
- Link target failed: `helios.westenergie.de` (parent `www.westenergie.de/de/impressum.html`, 403), `felixcare.de` (tilda.ws, 403), `3yo3c3.podcaster.de` (imprint 500).
- Contact page only: `www.bessernaehen.de`, `media-service-grade.de`, `dryandcool.de`.
- App/login: `cavok.odd.de`, `dragontalk.opendfki.de` (401), `termine.mmbbs.de`.
- Bot challenge: `natursteinarbeiten-berlin-brandenburg.de` (Cloudflare), `hessen.thw-jugend.de`, `www.buecherei-mindelheim.de` (human verification).
- Redirect/spam: `www.buessecker.de` (-> vulkanvegas.de), `gutachter-freese.de` (-> katatogelmacau.com), `wiedenroth.de` (-> vercel.com), `www.dasreiners.de` (casino spam).
- Genuinely none: `blog.never-afk.de`, `kevins-werkstatt.de`, `www.db.informatik.uni-bremen.de`, `laufpunkrock.de`.
- Unverifiable: `www.casa-del-caffe.de`, `miz-werther.de`, `tensioncontrol.de` (all Strato 503 now).
- Other: `www.bernd-mannhardt.de` ("Impressum" menu item points to `/`).

## Caveats

- Sites were re-fetched hours after the crawl; the 20 hosts on Strato IPs returned 503 for the whole session. 17 of them were classified from the crawl-time record, 7 stay unverifiable (cause could be any of the above).
- "Genuinely none" is a negative: only `/impressum`, `/impressum.html`, anchor scans and Kontakt pages were checked; imprints in PDFs, under other paths (`/rechtliches`, `/info`) or behind JS would be missed. The true genuine rate is thus an upper bound for hosts with static HTML and a lower bound overall.
- Classification of JS vs parked vs genuine is partly judgement; single-primary-cause labeling means fix counts are exclusive (a few hosts would be recovered by two fixes).
- Hosts sharing a CMS/provider (Caritas, podcaster.de, Strato) are correlated, widening the true uncertainty beyond the Wilson intervals.
- The replay used the repo's `HEADERS` UA "Mozilla/5.0"; the original crawl ran with 64 workers, which may cause extra timeouts that cannot be reproduced.

## Reproduction

Scripts in `/tmp/claude-1001/-home-dinzinger-GitHub-imprints-collection/4280400b-8791-4eb6-b5aa-38d0ba90cc90/scratchpad/E5/` (venv `v/` with `resiliparse requests charset-normalizer`): `sample.py` (sample), `collect.py` (re-fetch and evidence), `replay.py` (crawler replay), `kontakt_check.py`, `verify.py`, `labels.py` (manual labels), `classify.py` (table, JSONL).
