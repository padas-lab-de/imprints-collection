# Collection history: German Imprints Dataset

State: 2026-11-08. Compact history of the whole data collection for the new snapshot.
It is ordered by what we collected (seeds, link rounds, re-crawls), not by experiment number.
Source of truth: [decisions.md](decisions.md) and [status.md](status.md). The appendix maps IDs to sections.
Terms: "found" = host with status `imprint_found` (an imprint page was fetched; it is not yet a checked address).
"New" = new D34 sites, counted in order, first source wins (see section 1 and 7). All "new sites" values are from recount r4 (2026-11-08, `release_count.tsv`, branch E31-recount-r4); they sum to 4,020,137.

## 1. Count now

| Count | Value | Date | Rule |
|---|---|---|---|
| Sites after D34 dedup | **4,020,137** | 2026-11-08 (recount r4, lead-verified) | One site per `www.x` / `x` pair. |
| Sites after parking filter | **3,992,804** | 2026-11-08 | Drop sale, parking and host-default pages. |

- D34 rule: `www.x` and `x` count as one site. Keep the redirect target if it is a crawled host, else the non-www form.
- Parking filter (E40): drop a site when all its found hosts are domain-sale (19,898), parking (6,276) or host-default pages (1,159). Keep under-construction pages (16,862). That drops 27,333 sites.
- Other views of the same data (2026-11-08): 4,844,209 www-collapsed only; 5,275,955 exact hosts.
- Recount r4: branch E31-recount-r4, sha 181589e, made off E31-recount-r3, not merged. Output on lorbeer: e35 `datasets/E31/r4`. sha256 of the D34 site list: e4645f32…; of the filtered list: 85e12846….
- r4 adds 155,287 new sites from the sources E41L1-L4, E43, E44 and E45-E47. 4,113 r3 sites fold into new r4 sites (their redirect target is now crawled). The old sources fall from 3,865,119 to 3,864,850. Check: 3,864,850 + 155,287 = 4,020,137.
- Not in r4: E48 (Shopify full crawl of 96,722 hosts, running), the E34 round 4 pilot, and E42 (100-host Shopify pilot, no data copy).
- Both counts are sites with a found imprint page. The D16 address filter and the LLM extraction are not applied yet. Not every found page has an address (section 6).
- The releases and the paper report only these current counts.

## 2. Seed sources

Seeds are host lists that we crawl for an imprint. "Crawled" = hosts with a status row. Yield = found / crawled.
A pilot is a random 5k (or 20k) sample. Rule D33 (user, 2026-11-03): crawl the rest of a source if the pilot yield is above 10%.

| Source | Hosts crawled | Found | New sites (D34) | Status |
|---|---|---|---|---|
| Original seed list (6.56M hosts) | 6,560,119 | 3,256,728 (49.6%, exact hosts, 2026-10-29) | 2,631,463 | Done 2026-10-29 |
| Common Crawl, one crawl (CC-MAIN-2026-43, German hosts, .de/.at/.ch) | 20,000 pilot + 598,841 | 9,918 (49.6%) + 295,355 (49.3%) | 9,775 + 290,897 | Done 2026-11-04 |
| Common Crawl, 8-crawl union (E23), DACH pool | pilot 5,000 + part of 1,365,261 | pilot 1,901 (38.0%) | see next row | Done 2026-11-05 |
| Common Crawl, 8-crawl union, other-TLD pool | pilot 5,000 + part of 1,365,261 | pilot 918 (18.4%) | see next row | Done 2026-11-05 |
| Both Common Crawl pools together (full crawl) | 1,365,261 | 297,043 (21.8%) | 276,785 (pilots: 2,631) | Done 2026-11-05 |
| Common Crawl host index 2025-18 (DACH) | 5,000 pilot; rest inside the 962,942 below | pilot 1,391 (27.8%) | 3 pilots together: 2,591 | Done |
| Common Crawl host index 2024-46 to 2025-13 (DACH) | 447,400 (full crawl) | 79,560 (17.8%) | inside the 186,395 below | Done 2026-11-05 |
| FineWeb-2 DACH, last seen 2023+ (pilot 29.2%) | 5,000 pilot; rest inside the 962,942 below | pilot 1,459 | inside next row | Done |
| HPLT Internet-Archive-only DACH, 2.8% shard sample (pilot 21.5%) | 5,000 pilot; rest inside the 962,942 below | pilot 1,077 | inside next row | Done |
| Pools of the three rows above, full crawl | 962,942 | 252,474 (26.2%) | 184,254 | Done 2026-11-04 |
| FineWeb-2 DACH, last seen before 2023 | 1,470,805 | 269,399 (18.3%) | inside the 186,395 below | Done 2026-11-05 |
| HPLT Internet-Archive-only DACH, full | 511,763 | 108,276 (21.2%) | inside the 186,395 below | Done 2026-11-05 |
| The three rows above together (one crawl) | 2,429,968 | 457,235 (18.8%) | 186,395 (pilots: 1,624) | Done 2026-11-05 |
| FineWeb-2 hosts not crawled before, other-TLD parity crawl (E41L1) | 1,722,700 | 135,853 (7.9%) | 79,177 (after filter: 78,578) | Done |
| HPLT Internet-Archive-only hosts not crawled before, other-TLD parity crawl (E41L2) | 468,286 | 38,867 (8.3%) | 18,679 (after filter: 18,535) | Done |
| HPLT rest (E43): pilot 5,000 + full 1,250,808 | 1,255,808 | 116,279 (9.3%) | 45,449 (after filter: 43,967) | Done |
| FineWeb-2 dialect configs (E44): pilot + full | 10,687 | 242 (2.3%) | 159 (after filter: 158) | Done |

Not run, partly run (same sources). The other-TLD parts of FineWeb-2 and HPLT ran as E41L1 and E41L2 (user override of the 10% rule, 2026-11-06; FineWeb-2 pilot 8.1%: net 12.7%, eu 11.3%, com 9.4%). The dialect configs ran as E44 (29,436 hosts were not known; DACH 7,366).

| Source | Status | Reason or note |
|---|---|---|
| FineWeb-2 DACH, remaining part of 3,007,940 not-known hosts (2026-11-03) | Not traced | The docs do not say how much of the rest overlaps other pools. |
| Other 25 Common Crawl host-index crawls | Not run | Only 2025-18 and 2024-46 to 2025-13 used. |
| Common Crawl 8-crawl union: hosts seen in one crawl only (603k), hosts with one German page (20%) | Crawled with the pools, no separate cut | Noise is high; pilots passed 10% on all page-count buckets, so no page threshold. |

Looked at, not used:

| Source | Why not |
|---|---|
| CulturaX | Gated. No host list. |
| OSCAR | Gated. |
| German Commons | No URL column. |
| FineWeb2-HQ | Subset of FineWeb-2. |
| Common Crawl web graph (8.85M .de host vertices) | Includes uncrawled and spam hosts, no language flag. Weak alone. |

Notes:
- Original seed list: sources named in the paper are Open Web Index, Common Crawl and Curlie. The repo states no counts per source.
- Pools were built minus all known hosts (seeds, link frontiers), after clean-hosts and platform filters, www-collapsed.
- The Shopify provider group was skipped in all pilots and full crawls (section 4). The Shopify hosts themselves are tested in E45-E48 (section 4.3).
- For the sources added in r4, the "New sites" cell also gives the count after the parking filter. The E41 crawls use the new User-Agent.
- Pools had *.blogspot.de and *.blog.de removed (HPLT pool: 604 filtered in the pilot).
- A pilot yield counts found hosts of all hosts. Shares of reachable hosts are higher (for example 53.3% for the first pilot).
- Raw found rate overstates the dump sources: the 2,429,968-host crawl folds 60.2% of its found hosts into redirect targets (original list 8.0%, 8-crawl union 6.3%). Compare sources on new D34 sites.

## 3. Link rounds

Link rounds follow outlinks of pages we fetched. A frontier = new hosts linked from crawled pages, minus known hosts, platforms and www duplicates.
Rule (D16 B, D19 C, user): all TLDs, depth up to 3. Link-expansion finds count only with a DACH postal address (D16), checked at merge.

### 3.1 Outlinks of the original seeds

| Round | Frontier | Crawled | Found | New sites | Left out |
|---|---|---|---|---|---|
| Depth 1, frontier A (snapshot 2026-10-29 02:01 UTC) | 2,275,329 | 2,275,329 | 224,811 (9.9%) | 156,638 | Built from 252 of 263 seed batches. |
| Depth 1, frontier B (rest of the seed batches) | 59,046 | 59,046 | 5,085 (8.6%) | 3,272 | None known. |
| Depth 2, priority TLDs (de, at, ch, eu, info, shop) | 86,098 | 86,098 | 19,988 (23.2%) | 14,841 | None. |
| Depth 2, rest (com 630k, nl 177k, ...) | 1,715,061 | 1,715,061 (done 2026-11-04 06:04 UTC) | 16,342 (1.0%) | 11,987 | Shopify group skipped (1,318 at 22% done). |
| Depth 2 of frontier B | built on paper only | not run | none | none | No record that it ran. |
| Depth 3 | not built | not run | none | none | D19 C plans it; nothing in the docs. |

- Yield falls with depth: German Impressum on the same TLDs 45.6% (depth 1) and 21.5% (depth 2 priority).
- Depth 1 on other TLDs gave 2.36% German Impressum (com 3.35%). Depth 2 drifts away from DACH.
- DACH TLDs are 12.5% of depth-1 hosts and give 73.4% of German Impressum pages.
- Order of depth 2 (D26 B): priority TLDs first, then the rest. The user chose the full rest list (D29 C, 2026-11-03).

### 3.2 Outlinks of the new-source pages

Frontier = hosts linked from pages of the new sources (section 2), minus all known and crawled hosts.

| Round | Frontier | Crawled | Found | New sites | Left out |
|---|---|---|---|---|---|
| Round 1 (2026-11-03/04) | 49,142 | 49,142 (5,000 pilot + 44,142) | 5,797 (11.8%) | 3,893 | None. |
| Round 2 (2026-11-04) | 247,928 | 247,928 (pilot 5,000 + 242,928) | 21,071 (pilot 421 + full 20,650; 8.5%) | 11,880 | None. 6,992 non-DACH finds need a DACH address at merge. |
| Round 3, DACH TLDs (2026-11-05) | 33,257 | 33,257 (pilot 5,000 + 28,257) | 11,721 (1,807 + 9,914; 35.1% on the full part) | 6,101 (after filter: 5,959) | Other TLDs: next row. |
| Round 3, other TLDs (E41L3; all but .de/.at/.ch/.li; done 2026-11-08) | 572,749 (dropped by the round-3 TLD filter; 565,218 left after later exclusions) | 565,218 | 9,057 (1.6%) | 5,451 (after filter: 5,426) | None known. |
| Round 4 (2026-11-08, all TLDs, pilot only) | 701,697 | 5,000 (pilot) | 97 (1.94%) | 88 | Below the D33 bar (10%). D46 C (user, 2026-11-09): stop after the pilot; the rest is not crawled. Outlink rounds end here. Not in recount r4. |

- Round 2 by TLD group: DACH 13,658 / 38,375 = 35.6%; generic 5,618 / 145,446 = 3.9%; other ccTLDs 1,374 / 59,107 = 2.3%.
- The pilot of round 2 was below the 10% rule (8.4%). The user chose the full crawl including generic TLDs (D38 B).
- Round 3 is the first crawl with the new User-Agent (section 5).
- The hand count for round 3 was 9,753 new sites. Recount r4 gives 6,101.
- Round 4 frontier = outlinks of E34 round 3, E41, E43, E44 and the Shopify tests, on all TLDs. The pilot found 97 of 5,000 hosts; 88 are new D34 sites.

## 4. Re-crawls and recovery

### 4.1 Retry passes for failures

Failures of the first pass were retried from a second IP at a low rate. Causes: throttle (429/503), timeout, connection refused. 403 hosts were left out.

| Pass | Hosts | Found | Note |
|---|---|---|---|
| Pilot (1,000 retryable hosts, 2026-10-26) | 1,000 | 148 (14.8%) | By cause: throttle 54.1%, timeout 10.3%, conn 8.8%, 403 0.6% (3/525). |
| Round 1 (seed batches 0-49 + 48 Strato hosts, done 2026-10-31) | 55,887 | 10,697 (19.1%); 8,740 new sites | Throttle 7,233 / 29,287 (24.7%); timeout 2,341 / 19,248 (12.2%); conn_refused 1,083 / 7,304 (14.8%). |
| Round 2 (seed batches 50-262, done 2026-11-03) | 191,134 of 227,711 | 44,087 (23.1% of listed); 37,375 new sites | Throttle 29,885 / 114,193 (38.5%); timeout 10,644 / 85,594 (12.4%); conn_refused 3,558 / 27,924 (12.7%). All found hosts are net new. |
| 403 pilot (2,000 hosts, 2026-11-01) | 1,861 fetched | 14 (0.75%) | Far below 10%. No round 3 for 403 hosts. |

- Not retried: 36,577 Shopify hosts (round 2, see 4.3); 403 hosts (270,624 in seed batches 0-262; 220,074 in batches 50-262).
- Round 2 ran in stages. It started on 2 VMs (2026-10-31), moved to 5 VMs after slow progress (D28), moved again after two out-of-memory incidents (D30, section 8), and finished its non-Shopify part on 7 VMs (2026-11-03 13:16 UTC).
- Rule: a host is never retried from the VM that crawled it first.
- Round 2 stalled from 2026-11-02 to 2026-11-03: Shopify answered 429 to every request and held back the batches behind it (D31).

### 4.2 Re-check of imprint_not_found hosts with the improved fetcher

| Step | Hosts | Found | Note |
|---|---|---|---|
| Recall audit (300 DACH hosts: 150 single-crawl Common Crawl, 150 seed list) | 300 | 20 real imprints (6.7%) | The patch alone would add 4.0% (CI 2.3-6.9%). |
| Pilot with the patched fetcher (2026-11-04) | 5,000 | 294 (5.9%) | link 174, probe 63, kontakt 57. New sites: 261. |
| Full re-check of DACH not-found hosts (done 2026-11-05) | 479,573 | 29,855 (6.2%) | link 16,704, probe 6,003, kontakt 7,148 (24%). New sites: 23,447. |
| Re-check of E16 not-found hosts on all TLDs (E41L4) | 1,439,316 | 7,312 (0.5%) | New sites: 6,234 (after filter: 6,037). |

- The population was 484,573 seed-list .de/.at/.ch hosts with status imprint_not_found, minus hosts found elsewhere and the audit sample.

### 4.3 Shopify hosts

All Shopify shops share one provider group (`v4:23.227.38`).

| Date (UTC) | Event |
|---|---|
| 2026-10-28 | Slow round 1 partly caused by Shopify and two Cloudflare networks. |
| 2026-11-02 to 11-03 | Round 2 stalls: every request gets HTTP 429, about 1 host per minute. 39,133 round-2 hosts were Shopify (17%). |
| 2026-11-03 08:20 | D31 A: stop the 5 fetches. Non-Shopify hosts (47,251) go to 7 VMs; they finish with 11,481 found (24.3%) by 13:16. A 500-host Shopify pilot starts on mispel. |
| 2026-11-03 11:02 | D32 A: the pilot stops after 3 hosts in 2 h 42 min (2 found). Every request got 429 even at about 1 per minute. Quiet period of 72 h starts. |
| 2026-11-03 onward | All new crawls skip the group (new `--skip-provider-group`, status `skipped_provider`, no request sent). |
| 2026-11-06 11:02 | Re-pilot starts (E42): 100 hosts from the unfetched Shopify list, 1 request per 60 s, one VM (not the host's first VM). It has no data copy and is not counted. |
| 2026-11-08 | Rate tests E45, E46, E47 are in recount r4 (table below). E48, the full Shopify crawl of 96,722 hosts, is running and not counted yet. |

Rate tests in recount r4:

| Test | Hosts | Found | New sites (D34) |
|---|---|---|---|
| E45 | 137 | 54 (39.4%) | 52 |
| E46 | 100 | 50 (50.0%) | 49 |
| E47 | 100 | 39 (39.0%) | 37 |
| Together | 337 | 143 | 138 (after filter: 138) |

- Decision rule for the re-pilot (E42): if fewer than 50% of requests get 429, run the other 36,477 hosts at that rate on free VMs. Otherwise drop Shopify from the recovery and record the hosts as throttled.
- The pilot also counts all Shopify hosts skipped in all sources (E42 goal). That count is not in the docs yet.
- Stake: about 4k imprints in the 36,577 round-2 hosts (estimate at about 11%). Earlier round-2 yield was 22 / 461 (aspe) and 68 / 357 (abelie).
- We do not use a browser User-Agent or any trick to get past the 429. The user's rule is to stay polite.

## 5. Fetcher changes and their effect

All numbers are on random samples of seed hosts unless marked.

| Change | Measured effect | Date |
|---|---|---|
| Baseline fetcher | Imprint found 59.2% of reachable (.de 79.7%), 20k sample. | 2026-10-23 |
| Static-rule fixes F1-F6, F9 (links keyed by full URL, pages with empty main text kept, /impressum probe, ...) | 64.2% of reachable (.de 84.0%). Precision of gains 40/50 = 80%. | 2026-10-23 |
| Corrected rules (current fetcher until the recall patch) | 63.5% of reachable (.de 83.6%). Precision of gains 49/50. | 2026-10-23 |
| Fix for lost external hosts (links were keyed by URL path) | Counts of external hosts are right: 34,771 unique on the 20k sample. | 2026-10-23 |
| Provider limiter (per /24 or /48 network) | 100k dry run: found per reachable 62.5%; Strato blocked 24 of 6,433 hosts. | 2026-10-24 |
| 8 requests per provider network (was 4) | Strato blocked 0.7% (0.44%), IONOS 0.24% (0.53%); found 49.8% (50.2%); 59 min per 25k batch (74). | 2026-10-24 |
| Memory-leak fix (stop endless bodies, stream reads) | RSS 1,901 MB to 1,061 MB over 3 x 1,000 hosts. | 2026-10-25 |
| Body-size cap 10 MB (D30) | 16 bodies capped in 17 h; RSS stayed 0.36-1.0 GB. | 2026-11-01 |
| Skip-provider flag (Shopify) | No requests to the group; 1,318 hosts skipped at 22% of depth-2 rest. | 2026-11-03 |
| Recall patch (E35; /impressum.php, /impressum.htm, probes after failed link candidates, accept a Kontakt page with imprint word + address, no Kontakt redirect to landing page) | New found: 5.9% of old not-found hosts (pilot) and 6.2% (full). Cost: worst case 15 requests per host (was 10). | 2026-11-04 |
| New User-Agent with bot name and contact URL (D39 B) | Used only from round 3 of the outlinks (2026-11-05). No yield measurement. | 2026-11-05 |

- Fetcher by source: seed list, link depths 1-2, all pilots and full crawls up to the 962,942-host crawl and the 1,365,261-host crawl use the older fetcher (with cap and skip flag). The 2,429,968-host crawl, round 2 of the outlinks, the re-check and the pilots of section 4.2 use the recall patch. Round 3 uses the patch plus the new User-Agent. The paper must state the fetcher per source (D36).
- Left out on purpose: counting a landing page as an imprint (F7) and a Kontakt page as an imprint (F8) in the first round of fixes. The Kontakt rule came back in the recall patch (D36 B).
- Probes, robots.txt and the number of path guesses stay unchanged after the abuse report (D39 B, user decision). A stricter option A was not chosen.

## 6. Quality checks

| Check | Result | Date |
|---|---|---|
| Imprint precision of fetcher gains | 49/50 correct (CI about 89-100%). | 2026-10-23 |
| Why 200 .de hosts have no imprint (E5 sample) | Parked 20.5%, JS-only/empty 17.5%, missed by rules 17.0%, truly none 11.5%, others. Static fixes recover 21% of them. | 2026-10-23 |
| Recall audit (300 DACH not-found hosts) | 6.7% have a real imprint (CI 4.4-10.1%); 4.7% are missed by the code of that day (6 of the 20 were crawl-time errors). | 2026-11-04 |
| Kontakt precision, pilot labels | 38 true, 5 false, 7 unclear of 50 Kontakt finds (10% false, CI 4.3-21.4%). | 2026-11-04 |
| Kontakt precision, audit (agent labels, lead recount) | 87.0% (87/100, full re-check), 88.0% (44/50, 2,429,968-host crawl). Control: link finds 84.0% (42/50). Intervals overlap, so no evidence Kontakt is worse. | 2026-11-05 |
| Parking filter precision | Sale + park flags 58/60 = 96.7% (CI 88.6-99.1); host-default 20/20; under-construction only 9/30 = 30%. Unflagged found sites: 0/60 parked. | 2026-11-05 |

- In the Kontakt audit, "real imprint" means operator named, street and number, postcode and city. One rater (agent), pages cut at 4,000 characters.
- Result: a found host means a page was found. It is not yet an imprint with a DACH address. About 10 of the Kontakt "yes" records are contact blocks. Some pages list other parties' addresses before the imprint.
- Decision: no Kontakt filter before the merge. All routes go to the LLM extraction unchanged. Wrong finds without a DACH address fall out at the D16 filter; spam pages with an address do not.
- The parking filter reads only the home page. Misses show new phrases for a later pass ("domain names for sale", "Website folgt", and others).

## 7. Dedup and count rules

| Rule or variant | Result | Status |
|---|---|---|
| D34: www-collapse, keep redirect target if crawled, else non-www | 4,020,137 sites (2026-11-08) | Adopted (user, 2026-11-03). |
| Order of sources: first source wins | New sites per source depend on the order. | Adopted. |
| Exact host count | 5,275,955 | Not used as headline. |
| www-collapse only, no redirect fold | 4,844,209 | Not used as headline. |
| Variant: fold only into redirect targets that are themselves found | 4,073,897 (on the 4,020,137 base) | Rejected. At the 2026-11-05 count, 45,541 of the 57,655 hosts it kept apart went to the parking target ts.domainname.de. |
| Parking filter: drop sale + park + host-default | 3,992,804 (sale 19,898, park 6,276, host 1,159) | Adopted as the assumed release count; branch not merged. |
| Parking filter variant: also drop under-construction pages | not applied | Rejected: only 30% precision. |

- History of the count: 3,069,472 D34 sites on a partial snapshot (2026-11-04 01:30 UTC); 3,859,210 at the final count (2026-11-05, all crawls finished); 3,865,119 at recount r3 (2026-11-06, with round 3 of the outlinks); 4,020,137 at recount r4 (2026-11-08, with the E41, E43, E44 and Shopify-test crawls).
- Why exact hosts overcount: 423,017 sites were found under both `www.x` and `x` in the seed crawl alone.
- Pilots stay in the count. The test dirs of the dry runs, the recovery pilots and the 403 pilot stay out.
- The count is not final for the paper: the D16 address filter and the LLM extraction come first (section 9).

## 8. Operations

### 8.1 VMs

| VM | Role |
|---|---|
| lorbeer | Lead VM. Crawled seed batches 107-156, hosts the merged data and the counts. |
| aspe, apfel, mispel | Crawl VMs from the start (seed batches 0-106, 157-213, 214-262). |
| abelie, akazie, aralie | Added 2026-10-29 (own /24, IPs 193.175.2.84-86). Shared with another user's jobs: little memory on akazie and aralie. |

- Seven VMs, each with its own public IP in the crawling subnet (D20 A). Throttling is per provider network and client IP, so more IPs gave more polite budget (D25 B, D28 A).
- Single copies on aspe only (as of 2026-11-05): seed-crawl data, E12 and E19 data, gold captures, the Photon geocoder.

### 8.2 Timeline

| Dates (UTC) | Phase |
|---|---|
| 2026-10-23/24 | Pilots and dry runs (20k, 100k). 8 requests per network chosen. |
| 2026-10-24 to 10-29 | Seed crawl: 263 batches of 25k on 4 VMs. |
| 2026-10-28 to 10-31 | Recovery round 1. |
| 2026-10-29 to 11-01 | Depth 1 (A, B) and depth 2 priority. |
| 2026-10-31 to 11-03 | Recovery round 2. |
| 2026-11-03 to 11-05 | Depth-2 rest, new-source pilots and full crawls, recall patch, re-check, outlink rounds 1-3. |
| 2026-11-06 to 11-08 | Other-TLD parity crawls (E41), HPLT rest (E43), dialect configs (E44), Shopify tests (E42, E45-E47), recount r4. |
| 2026-11-08 | E34 round 4: frontier built, pilot of 5,000 done. E48 (Shopify full crawl) running. |

### 8.3 Incidents

| Date | Incident | Handling |
|---|---|---|
| 2026-10-25 | Seed crawl process grew by about 2.5 GB per batch (25.5 GB at batch 19, swap full). | Restart with 3 batches per process. Root cause fixed the same day (abandoned request threads). |
| 2026-10-31 | akazie fetch killed (likely out of memory); the script logged a false exit 0. | Script fixed, restart loop added. |
| 2026-11-01 | akazie dead after 5 restarts; mispel killed twice, fetch at 25.6 GB. | D30 A: stop mispel, 10 MB body cap, reshard 68,782 hosts to abelie and apfel. |
| 2026-11-02/03 | Shopify 429 stall. | D31, D32 (section 4.3). |
| 2026-11-04 16:11 UTC | Abuse report for mispel (132.231.12.31): path probing on templers.de (188.40.61.153). Traced to 7 requests: landing page and 5 probe paths. | D39 B: new User-Agent with bot name and contact URL (https://www.fim.uni-passau.de/data-science). The reply (A14) said this was not a vulnerability scan and named the new User-Agent. Sent; the user marked the matter clarified on 2026-11-06. |
| 2026-11-05 ~14:12 UTC | lorbeer and mispel rebooted (user); no crawl of ours ran. apfel and aspe unreachable (network issue, no restart). | Both back at 16:55 UTC with data intact (checked). Copies of the unique results made to lorbeer; the count waited for this. |
| ongoing | lorbeer disk 94-95% full (19 GB free on 2026-11-04). | Not solved in the docs. |

### 8.4 Spend

- No paid runs for the data collection. The cost ledger (docs/cost_ledger.csv) does not exist yet. All crawling and the Common Crawl, DuckDB and Hugging Face reads use our VMs and free data.
- Limits stay: $20 per experiment run, $30 per UTC day.

## 9. Running now, not run, open

### 9.1 Running

| Job | What | Note |
|---|---|---|
| E48 Shopify full crawl | 96,722 hosts | Not in recount r4. Counts follow when it ends. |

The 2026-11-06 parity crawls (E41L1-L4) are done and in recount r4 (sections 2, 3.2, 4.2).

### 9.2 Not run (by decision or by threshold)

- 403 hosts (270,624): pilot 0.75%.
- 36,577 Shopify hosts of recovery round 2: now part of the Shopify work (E48 runs 96,722 hosts).
- E34 round 4: closed after the pilot (D46 C, 2026-11-09); the rest of 696,697 hosts is not crawled.
- Depth 3 of the seed outlinks and depth 2 of frontier B.
- The other 25 host-index crawls.
- A Kontakt filter before the merge.
- A stricter fetcher (robots.txt, fewer probes): option A of D39, not chosen.

### 9.3 Open

- LLM extraction of the snapshot waits for the gold-set model comparison. The user wants one model for addresses and topics.
- D16 address filter at merge: link-expansion finds need a DACH postal address. This affects the 6,992 non-DACH finds of outlink round 2 and similar finds elsewhere.
- Merge of the branches: counts (E31 final, r3 and r4), parking filter (E40), recall patch (E35) and User-Agent (D39) are not merged to the main branch.
- Per-pool split of the 1,365,261-host crawl (DACH pool vs other-TLD pool) is still to do.
- Open user proposals: the docs list only the gold-set proposals (time per item; the 11 hosts whose main address the filter removed) and D21. See Doubts.

## 10. Other module: gold set and extraction models

Owned by the other lead (since 2026-10-26). This is a pointer only, from the docs.

- Gold set design: new diversity-stratified set of 1,000 items (700 random core + 300 oversample; D14 to D17). Labels come from the live rendered site. Three labellers; one primary label per item, about 20% second labels, 50 calibration items for all three.
- Captures: 941 of 1,000 hosts captured (646 landing + imprint, 295 landing only), 59 failed.
- Labelling tool and model suggestions (E21, all items, D24 B) are ready on lorbeer. Labelling has not started. It waits on D21 (judgement calls in the guideline), the names of the three labellers, the access route and a calibration date.
- Baseline on the old gold set (innkube, 1,000 items): Qwen3.8-27B address exact 0.904 / normalized 0.953, topic accuracy 0.736; Gemma4-31B 0.885 / 0.945 and 0.752.
- Location-based match (D12): street level 0.982 (Qwen), 0.972 (Gemma); town level 0.992 / 0.986.
- Homepage as topic input scores about 2.5 points below imprint text.
- Target: Scientific Data, Data Descriptor (D10).
- For details read status.md, gold_set_design.md and the annotation docs.

## 11. Doubts

Conflicts between docs (later doc wins in the text above):
1. Round 1 recovery found: 10,697 (19.1%, In flight, 2026-10-31); 10,693 net new vs the seed crawl (round-1 report); 10,657 unique hosts (dedup, 2026-11-03). Section 4.1 uses 10,697.
2. Round 3 new sites: 9,753 (hand count, 2026-11-05), net +5,909 (recount r3, 2026-11-06), 6,101 (recount r4, 2026-11-08). The latest recount wins.
3. Parking filter: 3,834,419 on the 3,859,210 base (2026-11-05), 3,840,198 on the 3,865,119 base (2026-11-06), 3,992,804 on the 4,020,137 base (2026-11-08). Different bases. The latest one is used. Sale count 18,200, 18,332, 19,898.
4. Shopify quiet period: D32 text says "to about 10:00 UTC"; the record says 11:02 UTC. 11:02 used.
5. status.md header says "Updated 2026-10-26" and its E22 heading says "depth-1 crawl running". Both are stale. Content below them is current.
6. Pool and crawled sizes differ slightly: HPLT pool 516,971 minus 5,000 pilot is 511,971, but 511,763 were crawled; the CC host-index pool minus pilot is 448,428, crawled 447,400. Crawled counts used.
7. The statement "Kontakt false-positive check open" (2026-11-05 In flight) is closed by the audit later that day.
8. The E36 population was 484,573 hosts; the full re-check ran 479,573 (484,573 minus the 5,000 pilot).
9. Resolved (lead, 2026-11-08): of the 4,113 r3 sites that fold into a new r4 site, 3,844 stay credited to their old source under the new site name (first source wins), and 269 merge into a site that was already counted. So the old sources fall by 269 only (3,865,119 to 3,864,850). Check: 3,865,119 - 4,113 + 159,131 = 4,020,137, and 159,131 - 155,287 = 3,844.
10. E41L1 crawled 1,722,700 hosts; the 2026-11-06 plan named 1,730,374 FineWeb-2 non-DACH hosts. Crawled counts used. E41L4 (all TLDs) can overlap the DACH re-check E37; E37 counts first.
11. The docs hold no list of open user proposals for the collection. Only D21 and two gold-set proposals are open, so section 9.3 names those.

Numbers I could not trace to a doc (the text avoids them or marks them):
- (Filled by the lead from recount r4 `release_count.tsv`: all per-source new-site values. Earlier values in the docs, e.g. 276,813, 186,731, 23,518, 11,893 (pre-r3) and 276,801, 186,611, 184,266, 23,450, 11,891, 14,843 (r3), are superseded.)
- The frontier size of outlink round 3 on other TLDs (E41L3; the count file has crawled hosts only).
- The fetcher version used for E41, E43, E44 and the Shopify tests.
- The size of the FineWeb-2 DACH hosts that no pool covers.
- Count of Shopify hosts skipped in all sources.
- The split of the 1,365,261 pool by DACH and other TLD in the full crawl.

## Appendix: ID to section map

| ID | Name in short | Section |
|---|---|---|
| E4 | Fetch yield baseline (20k sample) | 5 |
| E5 | Causes of imprint_not_found | 6 |
| E6 | Static-rule fixes | 5 |
| E7, E2 | Old gold evaluation, baseline | 10 |
| E8, E12, E17, E18, E21 | Gold set pilot, sample, capture, tool, prefill | 10 |
| E9 | Fetcher precision | 5, 6 |
| E10, E11 | Link-expansion pilot, external-host bug | 3, 5 |
| E13 | 100k dry run, provider limiter | 5 |
| E14 | Depth of link expansion | 3 |
| E15 | Cap 8 test | 5 |
| E16 | Seed list crawl | 2 |
| E19 | Recovery passes | 4.1, 4.3 |
| E20 | Memory-leak fix | 5, 8.3 |
| E22 | Outlinks of the seeds (depth 1, 2) | 3.1 |
| E23 | Common Crawl 8-crawl union candidates | 2 |
| E24 | FineWeb-2 and other host lists | 2 |
| E25, E26 | Common Crawl single crawl, pilot and full | 2 |
| E27 | Pilots: host index, FineWeb-2, HPLT | 2 |
| E28, E30 | Pilots and full crawl of 8-crawl union pools | 2 |
| E29 | Full crawl of the E27 pools | 2 |
| E31 | Release count (D34) | 1, 7 |
| E32 | Recall audit | 4.2, 6 |
| E33 | Further dump pilots and full crawl | 2 |
| E34 | Outlinks of new-source pages (rounds 1-4; round 4 pilot only) | 3.2 |
| E35 | Recall patch review | 5 |
| E36, E37 | Re-check pilot, full re-check | 4.2 |
| E39 | Kontakt precision | 6 |
| E40 | Parking filter | 1, 6, 7 |
| E41 | Other-TLD parity crawls (E41L1-L4) | 2, 3.2, 4.2 |
| E43, E44 | HPLT rest, FineWeb-2 dialect configs | 2 |
| E42, E45-E48 | Shopify re-pilot, rate tests, full crawl (E48 running) | 4.3, 9.1 |
| D2 | LLM access, spend limits | 8.4 |
| D10, D11, D12, D13, D14, D15, D17, D21, D24 | Venue, gold and evaluation choices | 10 |
| D16, D19 | Link-expansion scope and depth | 3 |
| D18 | Provider cap 8 | 5 |
| D20, D22, D23 | Crawl VMs, speed route, shared VMs | 8.1 |
| D25, D27, D28 | Recovery round 1 reshard, 403 retry, round 2 IPs | 4.1 |
| D26, D29 | Depth-2 order and rest scope | 3.1 |
| D30 | Round 2 memory, body cap | 5, 8.3 |
| D31, D32 | Shopify tail and throttle | 4.3 |
| D33 | Common Crawl seeds, 10% rule | 2, 3.2 |
| D46 | Full crawl of E34 round 4: C, stop after the pilot (2026-11-09) | 3.2, 9.2 |
| D34 | www dedup | 1, 7 |
| D35 | Next imprint sources | 2, 3.2, 4.2 |
| D36, D37 | Recall patch, full re-check | 4.2, 5 |
| D38 | Outlink round 2 scope | 3.2 |
| D39 | Crawler identification | 5, 8.3 |
| A5, A6, A7, A8 | VM access and setup | 8.1 |
| A9, A10, A12 | Driver range changes | 8.1 |
| A14 | Abuse reply | 8.3 |
| A3, A4 | DPO, APC funding | not part of the collection |
