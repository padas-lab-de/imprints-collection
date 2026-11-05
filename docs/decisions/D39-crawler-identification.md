# D39-crawler-identification · How do the crawls identify themselves after the mispel abuse report?

Issued 2026-11-05. Blocks: the next crawl starts (E34 round 3, D32 Shopify re-pilot, later rounds).

## Context (lead-verified)
- Abuse report for mispel (132.231.12.31): 2026-11-04T16:11:57Z, "HTTP vulnerability scanning / path probing", target mail.christian-riemann.de (188.40.61.153); AbuseIPDB: 7 reports in 30 days.
- Cause: E33 full, batch 35 on mispel, host templers.de (resolves to 188.40.61.153, the same server), end_time 16:11:58 UTC, 7 requests, imprint_not_found. Row: e35 tree datasets/E33/full/fetch_status_batch000035.tsv.
- The 7 requests: landing page, then (no imprint link) the E32 probe paths /impressum, /impressum.html, /imprint, /impressum.php, /impressum.htm. A row of 404s for guessed paths in one second is what scanner detectors (fail2ban/CrowdSec style) flag.
- Fetcher (E35 b54aaa1, src/ic/cli/fetch.py): User-Agent is the bare "Mozilla/5.0" (no bot name, no contact); no robots.txt handling.
- christian-riemann.de itself was crawled once, E25 pilot, 2026-11-03 17:13:57 UTC (5 requests), not on 11-04.
- mispel is shared: user dang runs a ray job there since 2026-10-26; the other 6 AbuseIPDB reports can come from either.

## Options
- **A** (recommended) For all new crawls: User-Agent with bot name + contact URL; read robots.txt and skip disallowed hosts/paths; probe at most /impressum and /imprint, and stop probing after the first 404. Running E37 (last batches) and E30 finish unchanged. Yield drops a little (probe found 3.0% of E33 finds; robots.txt opt-outs unknown).
- **B** Only the User-Agent with contact URL; probes and robots.txt unchanged.
- **C** As A, and stop the running crawls now; restart them with the new fetcher.

## Answer
User 2026-11-05 ~12:20 UTC: "D39 B. Use this as URL: https://www.fim.uni-passau.de/data-science". UA: `Mozilla/5.0 (compatible; ImprintsCollectionBot/1.0; +https://www.fim.uni-passau.de/data-science)` (bot name assumed by lead), branch D39-crawler-user-agent from E35-fetch-recall-patch; for new crawls only, running E30/E37 unchanged.
