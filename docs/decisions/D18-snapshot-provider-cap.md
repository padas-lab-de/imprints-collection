# D18-snapshot-provider-cap

Issued 2026-10-24, after E13-snapshot-dry-run (docs/experiments/E13-snapshot-dry-run.md).

### D18-snapshot-provider-cap · Full seed crawl at 4 or 8 parallel requests per provider network? — before the snapshot crawl starts · blocks the snapshot crawl
**Recommend A:** tested setting; Strato and IONOS hold about 16% of hosts, and a block there would remove them from the snapshot.
- **A** 4 per network (tested on 100k: Strato 0.4% blocked, yield as E9): measured rate gives about 310 h (12.9 days) for 6.56M seeds.
- **B** 8 per network: estimated 9-10 days; Strato gets up to twice the tested rate, untested, risk of 503 blocks.
- **C** Test 8 on one 25k batch first, then pick A or B from its block rate.

Answer: (pending)
