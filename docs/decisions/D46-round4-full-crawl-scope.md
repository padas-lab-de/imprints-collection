# D46-round4-full-crawl-scope

Issued 2026-11-08 (lead). Blocks: the full crawl of E34 round 4.

**Question:** The round-4 pilot is far below the D33 bar (more than 10% imprint_found). Do we crawl all of the round-4 rest, only its DACH-TLD part, or nothing more?

**Context (lead-verified 2026-11-08):**
- Round-4 frontier: 701,697 outlink hosts on all TLDs (from E34r3, E41, E43, E44 and the Shopify tests), minus all crawled, known and planned lists. Overlap 0 with E48, E41 L1–L4, the round-3 frontier and the Shopify lists (lead re-check). Pilot 5,000 (seed 344), rest 696,697 (sha c93a1525…).
- Pilot: mispel, tree e34r3, D39 B user agent, Shopify skipped, 2026-11-08 20:09–20:26 UTC (about 17,700 hosts per hour on one VM).
  - imprint_found 97 of 5,000 = **1.94%** (Wilson 95% 1.6–2.4%). host_not_found 25.0%. 27,650 requests.
  - New D34 sites (not in the E31 canonical set): 88 = 1.76%.
  - DACH TLDs (.de/.at/.ch/.li): 28 of 94 = about 30% imprint_found. All other TLDs: 69 of 4,906 = about 1.4%.
- Rest by TLD: com 349,568; net 36,116; io 34,294; DACH 12,192 (de 9,061, ch 1,748, at 1,327, li 56).
- Expected yield from the pilot rates (not measured):
  - full rest: about 13,500 imprint_found, about 12,300 new sites, about 3.85M requests;
  - DACH part only: about 3,600 imprint_found from 12,192 hosts;
  - the other 684,505 hosts: about 9,600 imprint_found.
- Precedent: E41 L3 (round-3 non-DACH outlinks, 565,218 hosts) was crawled under the parity rule at 1.6% yield. Round 2 at 8.4% was judged below the bar.
- No money cost (own VMs). E48 keeps running on all 5 VMs at its Shopify rate either way.

**Recommend A:** The yield is the same as E41 L3 (1.6%), which we crawled under your rule to treat all TLDs the same. It costs no money, and it adds about 12,000 new sites.
- **A** Crawl the full rest (696,697 hosts), split over apfel, aspe, abelie, mispel and lorbeer beside E48. About 12,300 new sites expected. It sends about 3.85M requests to mostly non-German hosts, which raises the chance of abuse reports.
- **B** Crawl only the DACH-TLD part (12,192 hosts, about 30% yield), on one VM. About 3,600 imprint_found expected. This selects hosts by TLD, which breaks the rule to treat all TLDs the same, here as a crawl filter.
- **C** Stop round 4 after the pilot. Keep the 88 new pilot sites and record the frontier. Outlink snowballing ends here.

**Answer (user, 2026-11-09):** "D46 C." Round 4 stops after the pilot; rest_r4.txt is not crawled. The 88 new pilot sites go into the next recount.
