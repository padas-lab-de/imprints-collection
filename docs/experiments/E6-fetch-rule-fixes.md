# E6: Fetch rule fixes F1-F6, F9 (re-run on the E4 random 20k)

Date: 2026-10-23. Branch `E6-fetch-rule-fixes` (from `lead-record`). Follows `docs/experiments/E5-imprint-not-found-causes.md` (in the main checkout, untracked).

## What changed (`src/ic/cli/fetch.py`)

| Fix | Change |
|---|---|
| F2 | `discover_links` keeps every link as (url, anchor text) instead of one entry per URL path; keywords are matched on path + query and on the anchor label. Imprint candidates are ordered by keyword priority, then own host first, then shortest URL; `find_imprint` tries up to 5 in turn until one gives a usable page. |
| F1 | If main-content extraction of an imprint page gives 0 characters, it is re-extracted with `main_content=False` and kept if the body text is non-empty (`fallback_extraction: true`). |
| F3 | Imprint keywords `impressum`, `imprint`, `legal notice`, `rechtliche hinweise`, `rechtliches`, `anbieterkennzeichnung` (in this priority order). |
| F4 | `<base href>` is honoured when resolving relative links (`get_base_href`). |
| F5 | With no imprint link tried, probe `/impressum`, `/impressum.html`, `/imprint` on the final host; accept only HTTP 200 with text matching `impressum`, `angaben gemäß` or `§ 5 TMG/DDG` (case-insensitive) and different from the landing page text. |
| F6 | Anchor label also uses `<img alt>`, `title`, `aria-label`. |
| F9 | `try_fetch(..., retry=True)` retries once (after 1 s) on timeout or HTTP 5xx; used for the landing page and imprint pages. |
| found_by | The imprint record gets `found_by` (`link` or `probe`), `found_keyword` (matched term or probed path), `candidate_rank`, `fallback_extraction`. |

Not implemented on purpose: F7 (landing page as imprint), F8 (Kontakt page as imprint).

Three further changes came from the first precision sample and are part of the measured run (commit `986d3cc`):

- URL fragments are dropped from link targets; a candidate pointing to the landing page itself (e.g. `#impressum`, `/`) is skipped, and so is a fetched page whose text equals the landing page text. Without this, 6 of the E5 "on landing page" hosts and many `#...` links counted the landing page as imprint (an accidental F7).
- `try_fetch` returns nothing for binary content (charset detection fails). Before, a PDF was decoded to the string `"None"` and counted as an imprint (old E4 data has 13 such hosts that are now lost on purpose).

Other commits: `stats.py` and `merge.py` count an address only if one field is non-empty (`ic.utils.address_utils.has_address`, test `tests/test_address_utils.py`).

## Tests

`PYTHONPATH=<worktree>/src .venv/bin/python -m pytest` : 58 passed. New: `tests/test_fetch_links.py` (query-string links, shared paths, base href, img alt/title/aria-label, other labels, priority and ordering, candidate fallback, probe accept/reject, full-body fallback), `tests/test_fetch_select.py` (fragments, landing self link, landing text, binary), `tests/test_address_utils.py`.

## Run

Same settings as E4: 64 workers (the `NUM_WORKERS` default), UA `Mozilla/5.0`, timeout 10 s, host shuffle seed 42, one batch. The E4 command is not recorded in `results/logs/E4-fetch-random20k.log`; the defaults reproduce its header (`Total hosts: 20000 across 1 batches`).

```
cd <worktree>            # datasets/ symlinked to /home/dinzinger/GitHub/imprints-collection/datasets/E6/random20k
PYTHONPATH=$PWD/src python -c "from ic.ic import main; main()" fetch /home/dinzinger/GitHub/imprints-collection/datasets/E4/random20k_seed_hosts.txt
```

Output `datasets/E6/random20k/imprints_batch000000.jsonl.gz`, log `results/logs/E6-fetch-random20k.log` (40 min against 29 min for E4: extra candidates, probes, retries). A first run before the landing-page fix is kept in `datasets/E6/run1/` (log `E6-fetch-random20k-run1.log`; 10,446 imprints, .de 84.8%).

Analysis scripts (not in git): `/tmp/claude-1001/-home-dinzinger-GitHub-imprints-collection/4280400b-8791-4eb6-b5aa-38d0ba90cc90/scratchpad/E6/` (`compare.py`, `lossdebug.py`, `losscat.py`, `judge.py`).

## Results (old = E4, new = E6)

Imprint found / reachable (reachable = host has a record):

| Set | E4 | E6 | Delta |
|---|---|---|---|
| All | 9,606 / 16,217 = 59.2% | 10,327 / 16,093 = 64.2% | +721 (+5.0 pp) |
| .de | 7,106 / 8,917 = 79.7% | 7,469 / 8,888 = 84.0% | +363 (+4.3 pp) |
| Crawl status | found 9,606 / not found 6,611 / host_not_found 3,579 | found 10,327 / not found 5,766 / host_not_found 3,705 | |

Reachable differs by 124 hosts: 225 hosts have a record only in E4, 101 only in E6 (run-to-run noise of the crawl). On the 15,992 hosts reachable in both runs: 9,528 -> 10,282 imprints.

### Gains, losses, changes (per host)

- Gained (imprint now, none in E4): **873** (469 .de). 828 were reachable before without imprint, 45 were not reachable in E4.
- Lost (imprint in E4, none now): **152**.
- Imprint URL changed (both found): **128**, of which 58 differ beyond scheme/www/fragment/trailing slash; 22 of these changed host (mostly from an external site to the own host, or from a staging host to the live host).

Gains by `found_by` rule (873 gained hosts):

| Rule | Hosts | Fix it exercises |
|---|---|---|
| link, `impressum` | 265 | F2 (query/shared path, candidate list), F4, F6, F9, plus crawl noise (see losses) |
| link, `impressum`, full-body fallback | 90 | F1 |
| link, `imprint` | 267 (+5 with full-body) | F3 |
| link, `legal notice` | 40 (+1 full-body) | F3 |
| link, `rechtliches` | 11 | F3 |
| link, `rechtliche hinweise` | 7 | F3 |
| probe `/impressum` | 163 (+1 full-body) | F5 |
| probe `/impressum.html` | 16 | F5 |
| probe `/imprint` | 7 | F5 |
| link, `anbieterkennzeichnung` | 0 | F3 |

By fix family: F3 331, F5 187, F1 97 (90 + 5 + 1 + 1), rest (F2/F4/F6/F9/noise) 265 minus overlaps. Only 6 gained hosts needed a candidate other than the first (`candidate_rank > 0`), so candidate fallback matters little on this sample. F2/F4/F6/F9 cannot be told apart in the `link:impressum` bucket; the E5 per-host check below separates them. F9 cannot be isolated at all.

### Losses (152 hosts), explained

Each lost host was re-checked live with the new code (`lossdebug.py`) and old text compared with the old landing page.

| Category | Hosts | Verdict |
|---|---|---|
| Old "imprint" text identical to the landing text (shell / SPA / single page) | 34 | intended: no separate imprint page |
| Old imprint was the landing page itself (`#impressum`, `/` link) | 9 | intended |
| Old imprint was a PDF/binary decoded as `"None"` | 13 | intended (all 13 were garbage) |
| Host unreachable in the E6 run and still unreachable when re-checked | 48 | site down or blocking; crawl noise |
| Host unreachable in the E6 run, imprint found when re-checked | 29 | transient |
| Host reachable, no imprint in the E6 run, found when re-checked | 8 | transient (timeouts under 64 workers) |
| Other (down, 403 or changed when re-checked) | 11 | noise or site change |

So 56 losses are deliberate removals of false positives of the old rule, 96 are crawl noise or site state. Noise is symmetric: 225 vs 101 hosts reachable in only one run, so part of the gains (probably around 100) is noise too.

### E5 recovery (43 hosts of E5 category `rule_miss` or `no_link_but_url_exists`)

E5 reports 42 (fixes F1-F6); the file `results/E5/classifications.jsonl` has 43 because the wrong-candidate host `www.car-art-work.de` has no fix label.

| E5 fix label | Hosts | Found in E6 | Not found |
|---|---|---|---|
| F1 empty main content | 10 | 9 (all via full-body fallback) | `autoabo.schneider-mobility.de` (in the first E6 run found, in the final run dropped because its page text equals the landing page text, an SPA shell) |
| F2 query string / shared path / wrong candidate | 11 | 9 | `schuetzen-salzkotten.de` (landing page has no imprint link now), `www.bsv-heinsberg.de` (unreachable in the E6 run) |
| F3 other labels | 7 | 7 | |
| F4 base href | 4 | 4 | |
| F5 probe | 9 | 9 (all `probe:/impressum`) | |
| F6 img alt | 1 | 1 | |
| none (wrong candidate) | 1 | 0 | `www.car-art-work.de`: the only link is the WordPress draft preview URL (403) |
| Total | 43 | 39 (91%) | |

Other E5 categories now found (not targeted): link_target_failed 3, unverifiable_503 3, js_or_empty 2, genuinely_none 1, app_or_login 1, on_landing_page 1.

## Precision

Random sample, seed 20261023 (`random.seed(20261023)`; first `random.sample(gained, 50)`, then `random.sample(changed_substantive, 20)` from the 58 substantive URL changes; cosmetic changes such as a dropped `#datenschutz` fragment are excluded). I read the extracted imprint text and URL of each and judged whether it is the legal-notice page of that site. File with judgement and reason: `results/E6/precision_sample.jsonl` (fields `judgement`, `reason`, `note`).

| Sample | Correct | Bad |
|---|---|---|
| 50 newly gained | **40 / 50 (80%)** | 10 |
| 20 changed URL | **17 / 20 (85%)** | 3 |

Bad cases, gained: `designtanke.de` (full-body fallback gave only nav and footer), `sferallia.de` (parked domain, registrar's legal notice), `www.4pens.com` (product page "imprint methods"), `m81.studio` (portfolio page behind `/legal`), `www.alpaka-oase-usedom.de` (unfilled template placeholders), `index.nachmittagsbetreuung-rattelsdorf.de` (the web designer's imprint), `4fakultaet.de` (contact/team page), `christoph-rumpelcom-production-q2th9b.laravel.cloud` (course teaser), `www.agroservice-mertendorf.de` (hosting provider's privacy policy via `rechtliches`), `doublehh.com` (product page "custom imprinted hitchpin").

Bad cases, changed: `medien-wiki.de` (wiki article "Impressumspflicht" now beats the correct external imprint through own-host-first), `www.ah-azl.de` (unrelated external dealer site, 96 characters), `www.buhoplast.de` (`links.html` with nav label "Links & Partner Impressum" beats `impressum.html` by shortest URL).

Doubtful but counted correct: `madata.bib.uni-mannheim.de` (Anubis endpoint serves the site's imprint), `helvar.com` (legal-notices hub), `2018.mdst.de` (another organisation's imprint, linked as Impressum), `www.3it-berlin.de` (host institute's notice).

By route, the 10 bad gained cases: 5 matched the keyword `imprint` (`www.4pens.com`, `m81.studio`, `4fakultaet.de`, laravel.cloud, `doublehh.com`), 1 `legal notice`, 1 `rechtliches`, 1 probe, 1 `impressum` with full-body fallback, 1 `impressum` link to the web designer. The `imprint` keyword is the least precise new term (many English-language sites, substring matches in product URLs).

## Doubts and suggested follow-ups

- A sample of 50 gives a wide interval (80%, Wilson 95% CI about 67-89%); the old E4 imprints were not precision-checked, so the net effect on precision is unknown. The old rule also kept landing pages and PDFs (56 of the 152 losses).
- Ranking suggestion (not applied, would need another 40 min run): sort candidates whose URL itself matches a keyword before anchor-only matches (fixes `buhoplast.de`), and prefer same-organisation hosts over other-host links less aggressively (`medien-wiki.de`). Substring `imprint` in URLs matches product pages (`imprint-methods`, `imprinted`); a word-boundary match would remove these.
- F5 probes accept any 200 whose text contains the word `impressum`; one probe hit a WAF rate-limit page that quotes the probed paths (seen in the first sample: `akademie-erfolgsgestaltung.de`). A stricter pattern (Angaben gemäß / § 5 / Registergericht plus an address) would avoid it.
- Run-to-run noise is about +-100 hosts on the found count (hosts down in one run), so compare yields with that margin.
- `autoabo.schneider-mobility.de`-type cases (imprint page text equals the landing shell) are dropped by the same-text rule; for SPAs the imprint is not in static HTML.
