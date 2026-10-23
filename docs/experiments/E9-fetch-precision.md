# E9: Fetch precision fixes (re-run on the E4 random 20k)

Date: 2026-10-23. Branch `E9-fetch-precision` (from `lead-record` 8e35e07). Follows `E6-fetch-rule-fixes.md`, whose precision sample had 13 bad of 70 judged hosts.

## Changes

| # | Change | Where |
|---|---|---|
| 1 | Candidate order: link whose URL path/query matches an imprint term first, then anchor-only matches; within each group keyword priority, own host first, shortest URL. | `discover_links` |
| 2 | URL matching of `imprint`, `legal notice`, `rechtliche hinweise`, `rechtliches` works on URL segments: the term must be the segment, with only filler tokens (`en`, `de`, `privacy`, `and`, digits, `html`, ...) next to it. `imprint-methods`, `imprinted-pins` no longer match; `imprint`, `en/imprint.html`, `legal-notice-privacy`, `?page=imprint` do. Anchor text uses word boundaries. Anchor-only matches of these terms need a label of at most 30 characters (no product links). `impressum` stays a substring match except `impressumspflicht`. | `url_matches_term`, `IMPRINT_PATTERNS` |
| 3 | Imprint evidence (`ic.utils.imprint_utils.has_imprint_evidence`): a phrase such as Angaben gemäß, § 5 TMG/DDG, Inhaber, Geschäftsführer, Handelsregister, Registergericht, USt-ID, vertreten durch, Medieninhaber, represented by, commercial register, VAT ID, (French) SIRET, or a postcode plus town. Error and rate-limit pages and unfilled template placeholders ("Bitte geben Sie Ihren ... ein") are rejected. Required for F5 probes (plus the word impressum/imprint), for the F1 full-body fallback, and for every page found through a keyword other than `impressum` (`imprint`, `legal notice`, `rechtliches`, ...). Pages found via `impressum` with normal extraction are accepted as before. | `accept_imprint_text`, `find_imprint` |
| 4 | A privacy-policy URL (last path segment `privacy`/`datenschutz`, not naming the imprint), as candidate or after redirect, is not accepted for the weak keywords. | `is_privacy_url` |

Tuning was done offline on the E6 output (`scripts/E6/evidence_offline.py`, no network): the evidence check passes 96% of `link:impressum`, 84% of `link:imprint`, 78% of `link:legal notice`, 87% of full-body pages in E6. Postcode alone counts as evidence; a stricter two-signal variant lost 6 of 57 good E6 hosts and was dropped.

Tests: 80 passed (`tests/test_fetch_precision.py`, `tests/test_fetch_precision2.py`, plus the older ones; two older tests got imprint evidence in their fake pages). Command: `PYTHONPATH=<worktree>/src .venv/bin/python -m pytest`.

Scripts for E6 and E9 are committed under `scripts/E6/` (compare, loss analysis, judgement writer, offline evidence check) and `scripts/E9/` (`compare9.py`, `judge9.py`, `lost_vs_e6.py`, `show9.py`). They read and write under `/home/dinzinger/GitHub/imprints-collection/{datasets,results}`.

## Run

Same settings as E4/E6 (64 workers, UA `Mozilla/5.0`, seed list `datasets/E4/random20k_seed_hosts.txt`, one batch):

```
cd <worktree>   # datasets/ symlinked to datasets/E9/random20k
PYTHONPATH=$PWD/src python -c "from ic.ic import main; main()" fetch /home/dinzinger/GitHub/imprints-collection/datasets/E4/random20k_seed_hosts.txt
```

Output `datasets/E9/random20k/imprints_batch000000.jsonl.gz`, log `results/logs/E9-fetch-random20k.log` (39 min). A first E9 run before the last three tweaks (privacy final URL, 30-character anchor limit, placeholder pages) is in `datasets/E9/run1/` (10,273 found, 63.7%).

## Results

Imprint found / reachable (source: `results/E9/compare_output.txt`):

| Set | E4 | E6 | E9 |
|---|---|---|---|
| All | 9,606 / 16,217 = 59.2% | 10,327 / 16,093 = 64.2% | 10,246 / 16,129 = 63.5% |
| .de | 7,106 / 8,917 = 79.7% | 7,469 / 8,888 = 84.0% | 7,444 / 8,904 = 83.6% |

E9 versus E4: 791 hosts gained (444 .de), 151 lost. E9 versus E6: 92 gained, 173 lost, of which 33 hosts were unreachable in E9 (crawl noise of about plus or minus 100). The other lost E6 hosts by E6 route (`results/E9/lost_vs_e6.txt`): `link:imprint` 49, `link:impressum` 34, `probe:/impressum` 20, `link:legal notice` 13, `link:impressum+fullbody` 11, `link:rechtliche hinweise` 5, `link:rechtliches` 3, other 5. The cost of the precision rules is thus about 0.7 pp of yield against E6, mostly the `imprint` route.

Gains versus E4 by route: link `impressum` 252, link `imprint` 228 (+4 full-body), probe `/impressum` 143, `impressum` full-body 75, `legal notice` 37, probe `/imprint` 19, probe `/impressum.html` 14, `rechtliches` 10, `rechtliche hinweise` 4, other 5. Compared with E6 the `imprint` and `legal notice` routes find more because URLs like `/legal-notice` and `/imprint` now match by token (the old substring `legal notice` never matched a hyphenated URL).

### E6 precision-sample hosts

The 13 bad hosts of E6 (`results/E6/precision_sample.jsonl`):

| Host | E9 |
|---|---|
| `www.4pens.com`, `m81.studio`, `www.alpaka-oase-usedom.de`, `christoph-rumpelcom-production-q2th9b.laravel.cloud`, `www.agroservice-mertendorf.de`, `doublehh.com`, `www.ah-azl.de` | rejected (7) |
| `medien-wiki.de`, `www.buhoplast.de` | now the right page (`studi-wikis.de/impressum/`, `impressum.html`) (2) |
| `designtanke.de`, `sferallia.de`, `index.nachmittagsbetreuung-rattelsdorf.de`, `4fakultaet.de` | unchanged, still bad (4) |

Of the 57 good E6 hosts, 56 are still found (54 with the identical URL, 2 with an equivalent URL such as a different session id); the 57th (`2018.mdst.de`) was unreachable in E9.

### E5 recovery (43 targeted hosts)

| E5 fix | n | E6 | E9 |
|---|---|---|---|
| F1 | 10 | 9 | 8 |
| F2 | 11 | 9 | 9 |
| F3 | 7 | 7 | 6 |
| F4 | 4 | 4 | 4 |
| F5 | 9 | 9 | 9 |
| F6 | 1 | 1 | 1 |
| none | 1 | 0 | 0 |
| Total | 43 | 39 | 37 |

Lost versus E6: `mediathek.vrm.de` (full-body page of navigation text without evidence) and `mahara.europa-uni.de` (the "Rechtliches" page holds only that heading). Both are weak imprints; the other four misses are the same as in E6.

### New precision sample

50 hosts gained versus E4, `random.seed(20261023)` on the sorted list (`results/E9/sample.json`, judgements `results/E9/precision_sample.jsonl`): I read each URL and extracted text.

| | Correct |
|---|---|
| 50 newly gained (E4 vs E9) | **49 / 50 (98%)**, Wilson 95% CI about 89-100% |
| E6 (for comparison, different sample) | 40 / 50 (80%) |

Bad: `praxis-dr-brosi.de`, whose `rechtliches` link leads to an unrelated external page (ethics-committee guidelines of a medical chamber). Doubtful but counted correct: `drwzmobile.com` (external host dgx-mobility.de, text starts with a cookie banner), `medien-camp.com` and `dr-volker-graf.de` (full-body fallback pages with navigation), `www.casas-lomo-felipe.de` (terms of use and provider data in one page).

## Doubts

- The two samples differ (E6 and E9 each drew 50 random gained hosts), so 80% vs 98% is not paired; the E6 bad cases that remain in E9 (4 of 13) show the rules are not complete. One sample of 50 gives a wide interval.
- Precision of the hosts lost versus E6 (about 140) was not judged; many of the 49 `imprint` losses were probably the false positives that evidence now rejects, but some are short real imprints without a postcode or phrase. A quick sample of those would settle it.
- The evidence list is German-centred (plus a few English and French terms); imprints in other languages without postcode pass only if a listed phrase appears.
- Remaining bad types that rules cannot catch: a web designer's imprint (`nachmittagsbetreuung`), a registrar or parking page's legal notice (`sferallia.de`), a contact page labelled imprint (`4fakultaet.de`).
- Crawl noise of about plus or minus 100 hosts applies to all yield differences between runs.
