# D19-link-expansion-depth

Issued 2026-10-24, after E14-link-expansion-depth (docs/experiments/E14-link-expansion-depth.md). Refines D16 B.

### D19-link-expansion-depth · How deep does link expansion go? — before the expansion crawl · blocks the expansion plan
**Recommend B:** about 10-20% more fetches than depth 1 for about 20-30% more DACH imprints from expansion; all-TLD depth 2-3 yields 20 and 8 per 1,000 fetches.
- **A** Depth 1 across all TLDs (D16 B as is): 3.5-3.9M fetches, 302-332k DACH-address imprints.
- **B** Depth 1 across all TLDs, then depth 2 and 3 only on .de/.at/.ch hosts: 3.9-4.6M fetches, 363-439k. Misses DACH operators on .com/.eu at depth 2-3.
- **C** Depth 3 across all TLDs: 11.4-19.1M fetches, 407-512k.
Estimates extrapolate 300-400x from 10-15k-host rounds and likely overstate depth 2-3 fetches.

Answer (user, 2026-10-24): "D19: C. D18: C."
Outcome: C: depth 3 across all TLDs
