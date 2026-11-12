# E53 facts (read-only fact-finding agent, 2026-11-12; lead-reviewed)

## Frame
- Release population now (r4 + E40 r2 parking filter): /home/dinzinger/GitHub/imprints-collection-e35/datasets/E40/r2/canonical_sites_after_filter.txt, 3,908,045 sites, one canonical host per line. Package copy: /home/dinzinger/imprints-release-20261109/filter/E40r2/.
- Before filter: .../e35/datasets/E31/r4/E31_out/canonical_sites.txt, 4,020,137. Filter flags: .../E40/r2/flagged_sites.tsv (dropped 112,092).
- host -> source -> status: .../e35/datasets/E31/r4/E31_in/<vm>_<source>_<dir>.tsv (99 files + manifest.tsv); source list counts/r4/sources.tsv. No single site -> files table; build by join (first source wins).
- Crawl output per host: /home/dinzinger/imprints-release-20261109/crawls/<source>/<vm>/<dir>/imprints_batch*.jsonl.gz (+ fetch_status_batch*.tsv). Record: {host, main, kontakt, impressum}, each with url, title, description, keywords, main_content (extracted text), content_language, ... Only extracted text, NO raw HTML.
- Not final: r5 pending (E48 Shopify + E34r4 pilot 88). E48 watch.log: GLOBAL STOP 2026-11-11 00:40Z at about 84% (about 16.1-16.4k of 19,344 per VM; imprint_found about 6.8-7.0k per VM). The record line says RUNNING (other lead's module; asked them 2026-11-12). No new crawls planned (D47).

## Input form
- Release run: `ic fetch` text (resiliparse main_content of STATIC HTML), pages main / kontakt / impressum.
- Old gold captures (scripts/gold/e17_capture.py): landing/imprint .static.html, .dom.html, .txt (innerText), .png, meta.json. E49 inputs = rendered DOM text; E51 = static crawl text.

## Already used hosts (exclude from the new draw)
- Old gold pre-E12: evaluation/gold_standard_data.jsonl (1,000). E8 pilot (1,000) and E12 screened 10,000: aspe only (datasets/E8/hosts.txt, datasets/E12/). E12 gold sample 1,000: datasets/gold/assignment.jsonl / prefill.jsonl.
- E49 300 (inside E12 gold), E51 500 (results/E51/{dev2,heldout2}_hosts.txt), E50 = E49 + E51.

## Stratifiers
- Free for the whole frame: TLD and hostname patterns, crawl source, provider (/24), found_by, candidate_rank, fallback_extraction, content_language, content_length, landing/imprint title etc.
- Not available without new fetches: CMS/tech, age, rendering need, operator type, address presence, topic. No large-scale POI/WZ/address predictions exist.

## Tooling
- src/ic/gold/sampling.py (two-phase core + rarest-first oversample, HT weights) reusable with new membership fields; assignment.py / e18_assign.py (3 labellers, 50 calibration, ~200 double); e17_capture.py; annotate tool (schema v2 with POI/WZ topic labels); e21_prefill.py (qwen-agentworld, addresses + operator + 11-class topic).
- Labels: only datasets/gold/labels/L1.jsonl, 4 calibration items from 2026-10-26 (tool test).

## Doubts found
- docs/gold_set_design.md is v0.2: 11-class topics, D15 text vs D24 B, geocode threshold 250 m vs D12 100 m.
- decisions.md says 952 captures on aspe; lorbeer has 990.
