# D25-e19-round1-reshard (issued 2026-10-28, data-collection lead)

**Question:** How do we finish E19-crawl-recovery-pass round 1, which runs far slower than planned on apfel alone? Decide by 2026-10-29 07:00 UTC, when E16 is due to free all four crawl VMs. It blocks the E19 round-1 result and round 2 (batches 50+).

**Recommend B:** E16 frees four IPs soon. Throttling is per provider network per client IP, so four IPs give about four times the polite request budget on the slow networks, with no host dropped.

- **A** Keep the current run: one process on apfel's IP (pid 133338/133348, workers 16, provider concurrency 2, delay 2.0 s). Nothing to do. Measured: batch 0 is at 22,888/25,000 after 2,646 min (~44 h) and now runs at <=9 hosts/min. Batches 1-2 (30,887 hosts) have not started.
- **B** When E16 is done: stop the E19 process on apfel (the status log keeps its progress). Compute the hosts with no final status yet, split them by host hash into four disjoint lists, and run `scripts/E19/run.sh` on aspe, apfel, lorbeer and mispel with the same rate settings, one OUT dir per VM. Then merge the four status sets into one round-1 report. Cost: a small shard and merge script (prepared now), plus the user's approval to stop pid 133338 (auto mode does not let the lead stop running workloads).
- **C** Drop the three slow networks from round 1: 23.227.38 (Shopify) and 172.66.3 and 162.159.143 (Cloudflare), ~13.7k of 55.8k hosts. Leave them as "not recovered", or give them a separate, slower round later. Round 1 then finishes faster on apfel alone, but those hosts get no answer now (Shopify shops often have an Impressum).

Context (measured 2026-10-28 ~06:50 UTC on apfel):
- Batch 0 counts: imprint_found 4,460, host_not_found 15,860, deferred 8,749, imprint_not_found 2,521.
- Limiter: 87,065 requests, of them 20,158 throttled. Parked queue: 2,105 hosts on v4:23.227.38.
- Top waits: Cloudflare 172.66.3 and 162.159.143, and Shopify 23.227.38.
- Provider networks of all round-1 hosts (from E16 first-pass rows on aspe): 23.227.38 6,755; 162.159.143 3,522; 172.66.3 3,467; 81.169.145 2,278; 37.27.55 1,553.

**Answer:** (open)
