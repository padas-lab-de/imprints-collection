# D40-e41-list-order

Issued 2026-11-06 (lead). Blocks: when the higher-yield non-DACH lists start.

**Question:** In E41-non-dach-parity-crawls, in which order do the four lists run?

**Context (measured 2026-11-06 08:30 UTC):**
- The four lists are disjoint, www-collapsed and contain no de/at/ch/li host. Total 4,195,520 hosts.
  - L4: E16 not-found seed hosts, 1,439,316.
  - L3: outlink round 3, 565,218.
  - L1: FineWeb-2, 1,722,700.
  - L2: HPLT IA-only, 468,286.
- 4 VMs (apfel, aspe, abelie, mispel) run L4, then L3, L1 and L2, one fetch at a time per VM. Speed is about 260 rows per minute per VM.
- L4 yield after about 28 min: 0.4–0.7% imprint_found. The L1 pilot was 8.1%. L3 and L2 have no non-DACH pilot. Their DACH versions gave 35.1% (round 3, DACH) and 21.2% (HPLT, DACH).
- Lead's ordering mistake: L4 first puts the weakest list first.

**Recommend A:** the yield is about 10x higher on L1 than on L4, so the same requests find more imprints first. All four lists still run in full.
- **A** Stop the L4 fetches now (rows done so far are kept; the driver restarts on the rest later). Run L3, L1, L2, then the rest of L4.
- **B** Keep the order: L4, L3, L1, L2.

**Answer:** (open)
