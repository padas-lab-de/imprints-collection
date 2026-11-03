# D31-e19-shopify-tail · How to handle the Shopify tail in E19 round 2?

Issued 2026-11-03 by the data-collection lead. Blocks: the rest of E19 round 2 (all five fetches).

## Context
- Since 2026-11-02 10:25 UTC the five round-2 fetches (aralie, aspe, lorbeer round2b; abelie, apfel round2c) have finished only ~200-300 hosts each in ~20 h (before: ~1,000 hosts/h in total per VM pair). The aspe log shows 7 hosts/min averaged over the run, but the last rows come at ~1 host/min.
- The last 300 rows on aspe are all provider group `v4:23.227.38` (Shopify), and 288 of 300 on abelie. Shopify answers HTTP 429, and each 429 pauses the group for 60 s (PCOOL), so these hosts go one at a time and most end as host_not_found (`https:http429;http:http429`).
- 39,133 of the 227,711 round-2 hosts (17%) had this provider in E16 (`round2/recovery_hosts_all_causes.tsv`). Only ~2% of the finished hosts are Shopify (aspe 461 of 21,092), so ~36k of the ~84k hosts left are Shopify (estimate).
- `ic fetch` starts batch 1 only after batch 0 is done, so the ~48k non-Shopify hosts left (mostly batch 1) wait behind the Shopify tail.
- Shopify yield in round 2 so far: aspe 22 imprint_found of 461 (4.8%), abelie 68 of 357 (19%). At ~11%, ~4k imprints are at stake in the Shopify hosts.
- Measured rate: ~1 Shopify host/min per VM, i.e. ~300/h on 5 VMs. Timing concern: at that rate the Shopify hosts alone take about 5 days.

## Options
**Recommend A:** the ~48k other hosts finish at the normal rate, and Shopify gets a pass tuned to its limit instead of blocking everything.
- **A** Stop the five fetches (finished hosts are kept). Split the hosts left by their E16 provider: non-Shopify (~48k) over the 7 VMs with the D30 code, never on the host's E16 origin VM; Shopify (~36k) in a separate list. Then pilot the Shopify list (500 hosts, 1 request at a time per VM, 10 s apart) to find a rate without 429, and run the rest at that rate on the VMs that are free.
- **B** Let the fetches run as they are. No work, but the batch-1 hosts wait several days behind the Shopify tail.
- **C** As A, but drop the Shopify hosts from E19 (~4k imprints lost, estimate).

## Answer
"D31 A." (user, 2026-11-03). Done 2026-11-03 08:20 UTC: 47,251 non-Shopify hosts on 7 VMs (round2d), 500-host Shopify pilot on mispel; 36,577 Shopify hosts left in total.
