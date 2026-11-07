# D45-shopify-full-run-choice

Issued 2026-11-07 (lead). Blocks: the crawl of the Shopify hosts that are not fetched yet.

**Question:** At what rate and on how many VMs do we crawl the 97,116 Shopify hosts that are left?

**Context (lead-verified 2026-11-07):**
- E47-shopify-rate-2s-test (D44 C): mispel, 1 request per 2 s to Shopify group v4:23.227.38, 08:43–09:03 UTC.
  - All 100 hosts done; 582 requests (all to Shopify), about 2.0 s apart on average.
  - **2 throttle responses (0.3%)**, the first in any Shopify test. The fetcher counts HTTP 429 and 503 as throttled (`src/ic/cli/fetch.py:67`), and the logs do not show which of the two it was. Both came on one host, account.efixelle.de (2 tries, 10 requests), the last host to finish, after request 540 (09:01Z, about 18 minutes into the run). The stop rule (5%) did not fire.
  - 39 imprint_found (39%), 53 imprint_not_found, 5 host_not_found, 3 filtered. 5.8 requests per host. **About 304 hosts per hour, or about 7,300 per day.**
- Rate ladder, all on Shopify group v4:23.227.38:

  | Rate | Test | Requests | Throttled (429/503) | Hosts per day |
  |---|---|---|---|---|
  | 1 per 60 s | E42 + E45 B | 482 | 0 | about 220 |
  | 1 per 10 s | E45 A | 589 | 0 | about 1,490 |
  | 1 per 5 s | E46 | 564 | 0 | about 3,070 |
  | 1 per 2 s | E47 | 582 | 2 | about 7,300 |

- Reading: one test cannot tell a Shopify rate limit that is starting from a single shop that had a fault. Both responses on one host point a little to the second, but 1 per 2 s is the only rate where any throttle response came.
- Hosts left: 97,116 (97,216 minus the 100 done in E47).
- The full run uses a moving-window stop rule: if more than 5% of the last 200 Shopify requests get 429 or 503, the run stops and I bring a new card.

**Recommend A:** 1 per 5 s gave no throttle response in 564 requests; 1 per 2 s is the only rate that gave any. A long run of 97,116 hosts should keep a margin below that rate.
- **A** Full run at 1 per 5 s on one VM (mispel), with the window stop rule. About 3,070 hosts per day.
- **B** Full run at 1 per 2 s on one VM (mispel), with the window stop rule. About 7,300 hosts per day. If the 2 responses were a rate limit, they may grow over a long run; the window rule then stops it.
- **C** Full run at 1 per 5 s on each of 5 VMs (apfel, aspe, abelie, mispel, lorbeer), with the list split into 5 parts. Global stop: a stop on one VM stops all 5. About 15,300 hosts per day. Shopify then gets 1 request per second from us in total, which is above the rate where throttle responses started from one IP.

**Answer:** (open)
