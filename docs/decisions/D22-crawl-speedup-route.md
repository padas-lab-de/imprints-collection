# D22-crawl-speedup-route (issued 2026-10-24)

Question (user): accelerate the crawl without losing websites/imprints - fast round, then a slow round from another VM/IP for the misses?

Measured on E16 batches 0-7 (200k hosts):
- Batch time ~57 min per 25k = 64 workers x 7.2 s mean per host; the last ~3% of hosts take ~18% of batch time (tail).
- Provider limiter is not the brake: IONOS 217.160.0/24 ~2.7 req/s, Strato 81.169.145/24 ~2.0 req/s vs cap 4; 1.4% hosts throttled.
- host_not_found 37.7k (18.8%): HTTP error on both schemes 6.7k, DNS 11.2k, 403 8.3k, SSL 3.9k, 429/503 3.2k, timeout 3.0k, refused/conn 0.8k. Retryable from another IP (403/429/503/timeout/conn/refused): ~7.5k = 3.8%.
- VM load ~25 on 16 cores; clamd (325%) is the Owler service's.

**Recommend A.**
- **A** Speed from parallelism, keep polite limits: move batch ranges to the A5 VMs (each own IP + CPU), plus E19-crawl-recovery-pass: after the main pass, retry the retryable failures (and the 48 Strato gold hosts) from a second IP at low rate. Completeness up, no extra block risk.
- **B** Fast first round with looser limits (cap 16, min_delay 0.1 s), then the same slow recovery round. Little gain (limiter is not the brake), higher risk: Strato/IONOS block the whole IP or file abuse reports, and blocked hosts then all fall to the slow round.

Answer: (open)
