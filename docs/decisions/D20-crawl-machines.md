# D20-crawl-machines

Issued 2026-10-24. User asked whether fetching can be distributed over several machines (timing and disk).

### D20-crawl-machines · Where do the seed crawl and the depth-3 expansion run? — before the expansion rounds · blocks the expansion crawl plan
**Recommend A:** the crawl subnet exists so that abuse reports reach the right place; each VM with its own public IP adds its own Strato/IONOS budget and its own disk.
- **A** Add VMs in the crawling subnet, each with its own public IP: batch ranges are split over machines with the existing run.sh FIRST LAST, each stores its own output; outputs gathered (or only imprint text kept) before processing.
- **B** FAITH Slurm compute nodes: not documented whether nodes have outbound internet or may crawl; needs confirmation from FAITH admins first.
- **C** This VM only: seed crawl about 7-13 days, depth-3 expansion 11-19M fetches after it; needs about 80 GB against 66 GB free.

Answer: (pending)
