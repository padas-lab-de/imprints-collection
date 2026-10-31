# D28-e19-round2-more-ips · Spread E19 round 2 over more VMs?

Issued 2026-10-31 by the data-collection lead. Blocks: E19 round 2 throughput.

## Context
Round 2 (227,711 hosts, E16 batches 50-262) started 2026-10-31 07:00 UTC on akazie and aralie only (2 shards, D22 A second IP). Measured at 07:09 UTC: first minutes ~1 host/s per VM, after 9 min 1.6-2.2 s per host per VM (tqdm). Round 1 slowed further in its tail. The rate per VM is bound by the polite per-network limits (PCONC 2, PDELAY 2 s), so more IPs give more throughput. Idle crawl VMs now: aspe, lorbeer, mispel (each has its own IP). Rule: a host must not be retried from the VM that crawled it in E16 (aspe 0-106, lorbeer 107-156, apfel 157-213, mispel 214-262).

## Options
**Recommend A:** same move as D25 B for round 1; more IPs raise throughput, and the polite limits per IP stay the same.
- **A** Stop the two round-2 fetches, reshard the remaining hosts over 5 VMs (akazie, aralie, aspe, lorbeer, mispel), each VM getting only hosts it did not crawl in E16. Done rows are kept (ic fetch resumes by host).
- **B** Keep the 2 shards; add VMs only for later rounds.

## Answer
(open)
