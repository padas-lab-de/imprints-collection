# E14: Link expansion depth (rounds 2 and 3)

Date: 2026-10-23/24. Branch `E14-link-expansion-depth` (from `lead-record` 693ddfa). Follows D16 B (all TLDs, keep imprints with a DACH address). Question: should link expansion go beyond one round, up to depth 3?

## Method

- Round 0 = 20k random seeds (E9 output), round 1 = E10 (11,969 new hosts). Round 2 candidates = hosts in E10's `discovered_external_hosts.txt` with the E10 rules (clean-hosts filter, not in seed list incl. `www.` variant, platform filter, `www.` collapse) plus: not fetched in an earlier round. 15,197 candidates (<= 20k), all fetched. Round 3 candidates from round 2's discovered file: 31,456, random sample of 10,000 (`random.seed(20261023)`).
- Current fetcher, 8 workers (E10: 64), batches of 2,500, one run each (`scripts/E14/run_fetch.sh`; ~2.6 hosts/s round 2, ~2.5 round 3). Logs `results/logs/E14-fetch-round{2,3}.log`. No 503 problem was looked for explicitly; reachable share does not collapse (69% and 80%).
- "DACH address" = the strict flag of `scripts/E10/analyze_lib.py`, unchanged. Analysis `scripts/E14/analyze.py` (output `results/E14/analysis.txt`), estimate `scripts/E14/estimate.py` (`results/E14/estimate.txt`), per-parent frontier sample `scripts/E14/frontier_sample.py`. Data in `datasets/E14/`, untracked.

## Per-round results

| Round | Fetched | Reachable | Imprint found / reachable | Strict DACH imprints | DACH / 1,000 fetched (95% CI) | .de/.at/.ch hosts fetched | their DACH / 1,000 | other-TLD hosts | their DACH / 1,000 | DACH by .de / .at / .ch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (seeds) | 20,000 | 16,129 (80.6%) | 63.5% | 8,644 | 432 (425-439) | 11,999 | 603 | 8,001 | 177 | 6,511 / 409 / 311 |
| 1 | 11,969 | 9,182 (76.7%) | 13.4% | 1,020 | 85 (80-90) | 1,619 | 413 | 10,350 | 34 | 526 / 85 / 58 |
| 2 | 15,197 | 10,548 (69.4%) | 4.0% | 303 | 20 (18-22) | 1,031 | 181 | 14,166 | 8 | 121 / 26 / 40 |
| 3 (10k of 31,456) | 10,000 | 7,965 (79.7%) | 1.7% | 80 | 8 (6-10) | 379 | 121 (92-158) | 9,621 | 4 | 26 / 11 / 9 |

The .de/.at/.ch share of the DACH-address imprints in rounds 2 and 3 is 62% and 58% (round 1: 66%).

### Frontier (new candidates per fetched host)

Candidates from a round's landing pages, after seed-list, earlier-round, platform and `www.` filters.

| From round | Fetched | Link lines | Unique hosts | In seed list | Already fetched earlier | New candidates | per fetched host | .de/.at/.ch share |
|---|---|---|---|---|---|---|---|---|
| 0 | 20,000 | 41,853 | 34,771 | 22,762 | 0 | 11,860 | 0.59 | 13.6% |
| 1 | 11,969 | 92,092 | 29,795 | 10,957 | 3,440 | 15,197 | 1.27 | 6.8% |
| 2 | 15,197 | 99,453 | 50,963 | 12,623 | 6,547 | 31,456 | 2.07 | 3.9% |
| 3 | 10,000 | 202,355 | 46,149 | 8,764 | 6,048 | 31,116 | 3.11 | 3.3% |

The frontier does not shrink; it grows per fetched host, because deeper hosts are more often service, directory and tool sites that link many external hosts, and the share of those that is .de/.at/.ch falls from 13.6% to 3.3%. Hosts already in the seed list shrink only from 65% to 19% of unique links. Singletons: 96%, 93%, 86%, 72% of candidates (round 3 is the sample of 10k parents, so the singleton drop is partly a sampling effect of fewer parents sharing links).

Per-parent sample (landing page re-fetched for 500 random reachable hosts of round 1 and of round 2; new candidates per parent are non-unique, so larger than the 1.27 and 2.07 above): .de/.at/.ch parents give 1.38 (round 1) and 1.47 (round 2) new hosts per parent, of which 1.18 and 1.14 are themselves .de/.at/.ch; other-TLD parents give 2.5 and 3.0 new hosts per parent and almost no .de/.at/.ch children (0.01-0.02). So a .de/.at/.ch-only expansion is self-sustaining and almost never leaves it, while a non-DACH TLD parent seldom leads back to DACH ccTLDs.

### Novelty (rough operator key: same postcode + street + house number)

Key found for 61-72% of the strict-DACH imprints. Duplicates of operators seen in earlier rounds:

| Round | DACH imprints | with key | key already seen in earlier rounds | new (no key or unseen) | new per 1,000 fetched |
|---|---|---|---|---|---|
| 1 | 1,020 | 627 | 298 (47.5%) | 722 | 60 |
| 2 | 303 | 219 | 85 (38.8%) | 218 | 14 |
| 3 | 80 | 56 | 22 (39.3%) | 58 | 6 |

Round 0 itself has 212 repeated keys among 5,356 (4%), so seed-list duplication is small; 39-48% of the expansion imprints belong to an operator that already has an imprint in an earlier round (other host, same address: subdomains, shops, multi-domain firms). This is a rough upper bound on duplication where the key exists (the same address can host several firms) and counts unkeyed imprints as new.

## Full-run estimate from 6,560,119 seeds (D16 B)

Same method as E10: new hosts per fetched host scaled linearly (upper) or by a Heaps fit on the round's own rarefaction curve (E10 exponent 0.98 for round 0; here 0.955 for round 1, 0.906 for round 2); yield per fetched host as measured per round. Round 3 yield is based on 80 imprints (CI 6-10 per 1,000). The depth-1 numbers reproduce E10 (3.5-3.9M fetches, 300-330k DACH imprints). Cumulative = all depths up to k.

All TLDs fetched at every depth:

| Depth | Fetches at this depth (Heaps - linear) | DACH imprints at this depth | Cumulative fetches | Cumulative DACH imprints | Cumulative per 1,000 fetched |
|---|---|---|---|---|---|
| 1 | 3.5M - 3.9M | 302k - 332k | 3.5M - 3.9M | 302k - 332k | 85 |
| 2 | 3.5M - 4.9M | 70k - 98k | 7.0M - 8.8M | 371k - 430k | 49-53 |
| 3 | 4.4M - 10.2M | 35k - 82k | 11.4M - 19.1M | 407k - 512k | 27-36 |

Depth 1 all TLDs, depths 2-3 only .de/.at/.ch (depth-3 frontier from .de/.at/.ch parents: 0.63-1.14 children per fetched parent, from the sample above with a 0.55 unique factor for the low end; yields 181 and 121 DACH per 1,000):

| Depth | Fetches at this depth (Heaps - linear) | DACH imprints at this depth | Cumulative fetches | Cumulative DACH imprints |
|---|---|---|---|---|
| 1 | 3.5M - 3.9M | 302k - 332k | 3.5M - 3.9M | 302k - 332k |
| 2 | 0.24M - 0.34M | 43k - 61k | 3.8M - 4.2M | 345k - 393k |
| 3 | 0.15M - 0.38M | 18k - 46k | 3.9M - 4.6M | 363k - 439k |

Unit yield of the added fetches: depth 2 all TLDs 20 per 1,000 fetched (14 counting only new operators), depth 3 all TLDs 8 (6 new). Depth 2 ccTLD-only: 181 per 1,000 (cc hosts fetched in round 2), depth 3 ccTLD-only: 121 (CI 92-158). For comparison the seed list gives 432 and round 1 85 (60 new operators) per 1,000.

Context: the seed snapshot has about 2.8M DACH-address imprints (E10), so depth 1 adds 11-12%, depth 2 (all TLDs) another 2.5-3.5%, depth 3 another 1.3-2.9%; ccTLD-only depth 2-3 add 2.2-3.8% together for 0.4-0.7M extra fetches.

## Reading

- Depth 2 and 3 are expensive for what they give: marginal yield falls 85 -> 20 -> 8 per 1,000 fetches (4x and 2.5x per round) while the frontier grows (0.6 -> 1.3 -> 2.1 -> 3.1 new hosts per fetched host). The all-TLD full run to depth 3 would need 11-19M fetches (17-28 days at the E10 speed of 7.8 hosts/s, 2-3 months at the 8-worker speed here) for 100-130k extra DACH imprints beyond depth 1.
- The .de/.at/.ch-only variant at depth 2-3 keeps 120-180 DACH per 1,000 fetches (a third of the seed list yield, twice round 1) and needs only 0.4-0.7M extra fetches for 60-110k imprints. This is the useful part of depth 2-3; its yield also falls with depth (181 -> 121) and 39-48% of expansion imprints are likely operator duplicates.
- Caveat for comparison with E10's filter (a): depth 1 under D16 B fetches all TLDs; the variant here is a hybrid.

## Open doubts

- Extrapolation: three Heaps fits on 12-15k-host rounds extrapolated 300-400x; the linear and Heaps columns are an upper and a plausible-lower bound, not a confidence interval. At full scale many more round-2 candidates will already be round-1 hosts or duplicates of each other (the pilot excludes only 12k round-1 hosts of ~3.7M), so both columns overstate depth 2-3 fetch counts; the yield per fetch is less affected.
- Round 3 is a 10k sample of 31,456 candidates; sampling is uniform, but yields rest on 80 imprints (379 cc hosts). Frontier growth in round 3 (3.1 per host, 202k link lines) is driven by a few link-heavy hosts; not inspected.
- Round-3 frontier per fetched host and the cc-only depth-3 frontier (0.63-1.14) come from the non-unique per-parent sample (500 parents each, 49-74 cc parents) with a guessed unique factor.
- Novelty key is rough (regex street + postcode + number); 28-39% of imprints have no key.
- Round 2 reachable share is 69% (round 1: 77%); lower concurrency (8 vs 64 workers) should not reduce it, but no repeat run was made, so crawl noise is unmeasured.
- Strict DACH flag precision was checked in E10 for round 1 only; deeper rounds have more non-German-language hosts and its precision there is unchecked. "DACH address" is operator location, not German-language content.
- ccTLD-only variant assumes cc hosts are identified by TLD only (.de/.at/.ch); DACH operators on .com/.eu/.it etc. are lost at depth 2-3 (that is 38-42% of DACH imprints in rounds 2-3).
