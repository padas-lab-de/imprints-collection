# D44-shopify-full-run-rate

Issued 2026-11-07 (lead). Blocks: the crawl of the Shopify hosts that are not fetched yet.

**Question:** At what rate and on how many VMs do we crawl the 97,216 Shopify hosts that are left?

**Context (lead-verified 2026-11-07):**
- E46-shopify-rate-5s-test (D43 C): mispel, 1 request per 5 s to Shopify group v4:23.227.38, 2026-11-06 23:41 – 2026-11-07 00:28 UTC.
  - All 100 hosts done; 564 requests (all to Shopify), **0 HTTP 429**. The requests were 5.0 s apart on average, so the limiter held.
  - 50 imprint_found (50%), 36 imprint_not_found, 14 host_not_found. 5.6 requests per host. **About 128 hosts per hour, or about 3,070 per day.**
- Earlier on 2026-11-06: E45 got 0 of 589 Shopify requests 429 at 1 per 10 s, and 0 of 242 at 1 per 60 s. E42 got 0 of 240 at 1 per 60 s.
- In total, 0 of 1,635 Shopify requests got 429. A per-IP limit is still not shown.
- imprint_found across the 3 tests: 38%, 43%, 50%.
- Hosts left: 97,216 (tmp/E42/shopify_all.txt minus the 336 hosts done in E42, E45 and E46).
- In a long run, the stop rule works on a moving window: if more than 5% of the last 200 Shopify requests get 429, stop, and I bring a new card.

**Recommend A:** it runs at exactly the rate and on the one IP that the tests measured, so nothing in it is untested. Shopify sees the same polite single client as in E46.
- **A** Full run at 1 per 5 s on one VM (mispel), with the window stop rule. About 3,070 hosts per day.
- **B** Full run at 1 per 5 s on each of 5 VMs (apfel, aspe, abelie, mispel, lorbeer), with the list split into 5 parts. Global stop rule: a stop on one VM stops all 5. About 15,300 hosts per day. The total rate (1 per s) is 5 times what we tested from one client.
- **C** One more step test at 1 per 2 s on one VM (100 hosts, the same rule), then a new card.

**Answer:** (open)
