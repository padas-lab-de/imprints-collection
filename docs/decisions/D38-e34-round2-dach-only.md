# D38-e34-round2-dach-only

Issued 2026-11-04 ~14:25 UTC by the data-collection lead.

## Question
E34-new-seed-outlink-pilot round 2: the pilot misses the D33 bar overall, but its DACH part is far above it. Crawl only the DACH part of the round-2 frontier?

## Context (lead-verified)
- Frontier tmp/E34/round2/frontier_r2.txt: 247,928 new hosts linked from E26/E29/E30/E33/E34 pages (sha256 c2fae09d...), 0 overlap with known lists.
- Pilot 5,000 (seed 342), mispel, E35 fetcher, done 13:51 UTC:
  - all: 421 imprint_found = 8.4% (Wilson CI 7.7-9.2%) -> below D33's 10%.
  - DACH TLDs (de/at/ch/li), 756 hosts: 267 = 35.3% (CI 32.0-38.8%); de 41.4%, at 45.5%, ch 22.7%.
  - other TLDs, 4,244 hosts: 154 = 3.6% (CI 3.1-4.2%); com 3.5%.
  - found_by: link 408, probe 12, kontakt 1.
- Rest of the frontier: 242,928 = DACH 38,375 + other 204,553. Estimate at pilot rates: DACH ~13,500 imprint_found, other ~7,400.
- Precedent: E28 ran DACH and non-DACH pools as separate pilots under D33.
- No paid APIs involved.

## Options
- **A** Full crawl of the 38,375 DACH hosts only (mispel, E35 fetcher, Shopify skipped), next to E33. Non-DACH rest dropped (3.6%).
- **B** Full crawl of all 242,928 hosts: ~7,400 extra non-DACH finds at 3.6%, which also must pass the D16 DACH-address filter at merge, so most may not count.
- **C** No full crawl; record round 2 as below the D33 bar.

**Recommend A**: the DACH part has its own random sample of 756 hosts at 35.3%, well above 10%; the non-DACH part fails the rule on its own.

## Answer
(open)
