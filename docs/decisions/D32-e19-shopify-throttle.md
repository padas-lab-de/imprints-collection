# D32-e19-shopify-throttle · What to do with the 36,577 Shopify hosts of E19 round 2?

Issued 2026-11-03 by the data-collection lead. Blocks: the Shopify part of D31-e19-shopify-tail A.

## Context
- D31 A started a pilot on mispel at 08:20 UTC: 500 Shopify hosts (`v4:23.227.38`), 1 request at a time, 10 s apart.
- After 21 min: 1 host done (host_not_found, http429), 22 deferred. Every request gets HTTP 429. With the 60 s cooldown after each 429, the pilot sends ~1 request/min, and that is also refused. A slower rate without 429 is not visible.
- The throttle looks like a block of our crawl IPs, maybe because of the round-2 traffic on 11-02/03. Earlier in round 2, Shopify hosts gave imprints (aspe 22/461, abelie 68/357).
- Not an option: sending a browser user agent or other changes to get past the 429. That would bypass Shopify's limit.
- Expected loss if dropped: ~4k imprints (~11% of 36,577, estimate), ~0.1% of the dataset.
- round2d (47,251 non-Shopify hosts on 7 VMs) runs normally and is not affected.

## Options
**Recommend A:** Shopify answers no request now; a short quiet period is the only polite way to find out whether the block is temporary, and it costs nothing.
- **A** Stop the pilot now. Send no requests to Shopify for 72 h (to 2026-11-06 ~10:00 UTC). Then pilot 100 hosts at 1 request per 60 s from one VM. If < 50% of requests get 429: run the rest at that rate on the free VMs. Else: drop the Shopify hosts from E19 (record them as throttled).
- **B** Drop the Shopify hosts from E19 now (record them as throttled). ~4k imprints lost (estimate).
- **C** Let the pilot run as it is (~1 request/min, all 429 so far) and decide on its numbers in 24 h.

## Answer
(open)
