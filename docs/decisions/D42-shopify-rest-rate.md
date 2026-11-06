# D42-shopify-rest-rate

Issued 2026-11-06 (lead). Blocks: the crawl of all Shopify hosts that were skipped.

**Question:** How do we crawl the 97,489 Shopify hosts that are skipped or left out?

**Context (E42-shopify-repilot, lead-verified 2026-11-06 on mispel):**
- Pilot: 2026-11-06 11:03–15:05 UTC on mispel, D39 B User-Agent, 1 request per 60 s to group v4:23.227.38; stopped at the 4 h cap.
  - 36 of 100 hosts done; 240 requests, **0 throttled (HTTP 429)**.
  - 14 imprint_found (39%), 20 imprint_not_found, 2 host_not_found. Mean 6.7 requests per host.
- D32 A rule: under 50% got 429, so the rest may run at this rate.
- Shopify hosts not fetched yet, all sources, www-collapsed, not found elsewhere: **97,489** (tmp/E42/shopify_all.txt, sha c667920a…).
  - By source: recovery round 2 33,972; Common Crawl 8-crawl union 27,158; depth-2 rest 12,176; host-index/FineWeb-2/HPLT pools 8,613 + 4,646; Common Crawl single crawl 7,285; others 3,639.
- Measured throughput at 1 request per 60 s: about 9 hosts per hour per VM. At that rate, 97,489 hosts need about 450 VM-days.
- Not known: whether Shopify limits per IP or per account. We sent no 429 at 1 per 60 s, which may mean the earlier block has lifted.

**Recommend A:** 1 request per 10 s on one IP is still polite to a platform that serves millions of shops. A short step test shows whether a higher rate holds before any long run.
- **A** Step test: 100 new hosts at 1 request per 10 s on one VM; at the same time, 100 hosts at 1 per 60 s on a second VM (to test per-IP). Stop a run at once if 429s exceed 5% of requests. Then a card for the full run.
- **B** Start the full run now at 1 request per 60 s on the free VM (lorbeer), as D32 A allows.
- **C** Do not crawl Shopify hosts. Record them as "skipped, throttled platform".

**Answer (user, 2026-11-06):** "D42 A." Step test (E45-shopify-rate-step-test): 1 per 10 s on mispel, 1 per 60 s on apfel.
