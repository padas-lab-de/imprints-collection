# D43-shopify-full-run

Issued 2026-11-06 (lead). Blocks: the crawl of the Shopify hosts that are not fetched yet.

**Question:** At what rate and on how many VMs do we crawl the about 97,300 Shopify hosts that are left?

**Context (E45-shopify-rate-step-test, lead-verified 2026-11-06):**
- Run A, mispel, 1 request per 10 s to the Shopify group v4:23.227.38: 16:52–18:30 UTC, all 100 hosts done.
  - 612 requests (589 to Shopify), **0 HTTP 429**. The Shopify requests were spaced about 9.9 s apart, so the limiter held.
  - 38 imprint_found (38%), 51 imprint_not_found, 10 host_not_found, 1 filtered. 6.1 requests per host. **About 62 hosts per hour.**
- Run B, apfel, 1 request per 60 s, at the same time: stopped at the 4 h cap (20:55 UTC). 37 hosts, 242 requests, **0 HTTP 429**. 16 imprint_found (43%). 6.7 requests per host. About 9 hosts per hour.
- E42 (earlier the same day, mispel, 1 per 60 s): 0 of 240 requests got 429.
- Total so far today: 0 of 1,071 Shopify requests got 429.
- The per-IP question stays open: with no 429 at any rate, the test cannot show whether Shopify limits per IP or per client.
- Hosts left: 97,489 (tmp/E42/shopify_all.txt) minus the hosts done in E42, A and B (36 + 100 + 37) = **97,316**.
- Measured throughput at 1 per 10 s: about 1,490 hosts per VM per day.
  - On 1 VM, the crawl takes about 65 days.
  - On 5 VMs (apfel, aspe, abelie, mispel, lorbeer; all run E41 or E43 now, and Shopify is skipped there), it takes about 13 days.
- Expected yield at 38–43% imprint_found: about 37,000–42,000 imprints. Not all are new sites after the D34 rule.

**Recommend A:** 1 request per 10 s held on two IPs with no 429. Five IPs at that rate add up to 1 request per 2 s to a platform that serves millions of shops. The stop rule is global, so any sign of throttling stops the whole crawl and does not just move it to another IP.
- **A** Full run at 1 per 10 s on each of the 5 VMs, with the list split into 5 parts. Global stop rule: if any VM has more than 5% of its last 200 Shopify requests get HTTP 429, stop **all** 5 runs and issue a new card. About 7,400 hosts per day.
- **B** Full run at 1 per 10 s on one VM (mispel), with the same stop rule. About 1,490 hosts per day.
- **C** Step test at 1 per 5 s on one VM (100 hosts, the same 5% stop rule), then a new card. This gives more speed per IP, if it holds.

**Answer (user, 2026-11-06):** "D43 C." Step test at 1 per 5 s on one VM (E46-shopify-rate-5s-test, mispel), then a new card.
