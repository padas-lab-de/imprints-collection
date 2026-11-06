# D41-hplt-rest-dialect-full-crawl

Issued 2026-11-06 (lead). Blocks: the full crawl of the two remaining seed pools.

**Question:** Crawl the rest of the E43 HPLT pool and the E44 FineWeb-2 dialect pool, although both pilots are below the 10% rule of D33?

**Context (lead-verified 2026-11-06 from the status files):**
- E43-hplt-rest-pilot: HPLT IA-only hosts from the 3,209 shards not used before. The pool has 1,255,808 hosts on all TLDs (32.2% DACH TLDs).
  - Pilot: 5,000 hosts; 442 found (8.84%); 174 new D34 sites (3.48%).
  - 73% host_not_found (old IA hosts).
  - Found rate by TLD: 18.2% on DACH TLDs, 4.4% on others.
  - The rest has about 1.25M hosts; about 44k new sites at the pilot rate.
- E44-fw2-dialect-pilot: the pool has 10,687 hosts; the pilot is 5,000.
  - 116 found (2.32%); 80 new sites (1.6%).
  - The rest has 5,687 hosts; about 90 new sites.
- lorbeer is free (no other crawl there); the pilots ran at about 280 hosts per minute with 32 workers. The 4 other VMs are busy with E41.
- The user does not want a DACH / non-DACH split, so a DACH-only option is not offered.

**Recommend A:** about 44k new sites is more than any outlink round gave (round 2: 11,891). The cost is only VM time on a free machine, with the D39 B User-Agent and no Shopify requests.
- **A** Crawl both rests in full on lorbeer now (E44 rest first, then E43). Add both to the next recount.
- **B** Crawl the E43 rest only; leave E44 (about 90 sites).
- **C** Crawl neither (D33 10% rule). Record both as "piloted, below rule".

**Answer (user, 2026-11-06):** "D41 A." Crawl both rests on lorbeer: E44 first, then E43.
