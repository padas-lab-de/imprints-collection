# D35-next-imprint-sources

Issued 2026-11-03 ~21:00 UTC by the data-collection lead. User asked: "What could we run to find more imprints?"

## Options (multi-pick; each source gets a 5k pilot and the D33 >10% rule)
- **A** Outlink frontier of the new seeds: hosts discovered while crawling E26/E29/E30 (link expansion depth 1, D16/D19 rules: DACH address required for link-expansion imprints). Prior: E22 depth 1 of frontier A 9.9% overall, .de 54.4%; depth 2 0.96%.
- **B** More dumps of the sources that passed: FineWeb-2 DACH last seen before 2023 (~2.57M not known), FineWeb-2 German hosts not in E23/cc43 (4.74M, mostly other TLDs), the other 25 Common Crawl host-index crawls (only 2025-18 used, P1 27.8%), full HPLT Internet-Archive part (sample 2.8% gave 212k pool, P3 21.5%).
- **C** Recall audit of imprint_not_found (largest non-found group, e.g. 43% of E27 P1): sample 300 DACH hosts, test extra probe paths (/impressum/, /impressum.php, /de/impressum, /rechtliches, /legal-notice, /kontakt) and footer/JS cases; if the miss rate is high, a re-check run over all imprint_not_found DACH hosts.
- **D** Shopify re-pilot after 2026-11-06 11:02 UTC (already D32; all skipped_provider hosts).

## Recommendation
A + B + C, D as planned. C first (small, tells whether millions of existing rows hide imprints), B pilots on lorbeer, A when E26 frees VMs.

## Answer
User 2026-11-03 ~21:05 UTC: "D35 A B C". -> C = E32-imprint-recall-audit, B = E33-more-dump-pilots, A = E34-new-seed-outlink-pilot; D stays D32. Each pilot under the D33 >10% rule.
