# D16-link-expansion-scope (2026-10-23) — open
Context: E10-link-expansion-pilot (docs/experiments/E10-link-expansion-pilot.md). New hosts linked from the 20k seeds: 11,969 fetched, 13.4% of reachable have an imprint (seed list 63.5%), 83% of those with a DACH address. Only 13.5% of new hosts are .de/.at/.ch, but they give 413 DACH imprints per 1,000 fetched (seed list 432); other TLDs give 34 per 1,000. Full one-hop round estimate: 15k-300k DACH imprints (middle 60-110k with ccTLD filter), i.e. roughly +2-4% on ~2.8M from the seed list. Doubt: the E9 fetcher discovers 1.7x more external hosts than E4; unexplained.
Question: how far do we take link expansion for the snapshot?
Recommend A.
- A One round, .de/.at/.ch hosts only (est. ~0.5M fetches, seed-list yield per host); report as a separate source in Data Records. Cheap, clean provenance.
- B One round, all TLDs, keep imprints with a DACH address. ~34% more DACH imprints than A at ~7x the fetches (est. 3.6-3.9M).
- C Skip link expansion; growth comes from the better fetcher only (+4 pp on .de).

Answer (user, 2026-10-23): "D17: We don’t need to compare site groups. Hence I go with B. Could we make it 1,000 instead of 1,100? D16: B. Do we for sure only do one round? How about finding new websites also to a depth of 3?" + "Go 1+2"
Outcome: B: all TLDs, keep DACH-address imprints; depth up to 3 asked -> E14-link-expansion-depth pilot (user)
