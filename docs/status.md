# Status — German Imprints Collection, journal extension

Updated 2026-10-26. Decisions and in-flight work: [decisions.md](decisions.md).

## Goal
Target: Scientific Data, Data Descriptor (D10-journal-venue).
Journal extension of the WebSci Companion '26 demo paper (arXiv 2609.03971), which reported no evaluation numbers: (1) evaluation of address extraction, topic classification and geocoding with a model comparison and error analysis; (2) a fresh, larger snapshot via better fetch yield and link expansion.

## Results so far

### E2-gold-baseline-innkube (1,000 gold items, prompt german/simple, temperature 0)
| Model | Address all fields, exact | Address all fields, normalized | Topic acc. | Topic macro-F1 | Failed calls |
|---|---|---|---|---|---|
| Qwen3.8-27B (reasoning off) | 0.904 | 0.953 | 0.736 | 0.595 | 0 |
| Gemma4-31B | 0.885 | 0.945 | 0.752 | 0.605 | 0 |

Source: results/<model>/german/simple/eval/metrics.json.
- Address errors (Qwen, 47 items): mostly town granularity (gold keeps district suffixes like "Grimma /OT Kaditzsch", model writes "Grimma"), single-letter spelling deviations, and a few wrong-address choices on multi-address imprints (ids 279, 678).
- Topic: largest confusions all go into Business and Professional Services (Community 32, Arts 30, Retail 23). Health and Medicine recall ~0.5 at precision ~1.0.
- Caveat: topic is evaluated on the imprint text (gold has no homepage text), while production classifies the homepage.

### E21-gold-prefill (suggestions for the labelling tool; spot-check results/E21/spotcheck.md)
Model suggestions for the gold labels from qwen-agentworld-35b-a3b on innkube (prompt e21-v1), 1,000 hosts.
- Spot-check, 40 random live hosts: main address (or correct absence) right 34/40, operator type 38/40, topic 36/40, site status 39/40.
- Filter e21-v1+filter1 (duplicates, town-only rows, third parties) reduced address rows from 1,254 to 950.
- Shown on all items (D24-gold-prefill-scope, answer B); agreement on second and calibration labels is agreement with suggestions shown.
- Next: measure time per item.

### E24-fineweb2-seed-hosts (done 2026-11-03; outputs tmp/E24/, SHA256SUMS there; lead-verified: sha256 OK, 0 of 2,000 sampled hosts per list are known)
Not-known hosts per source (www-collapsed, vs seeds + E22 frontiers = 10,128,961 hosts):
- FineWeb-2 deu_Latn (ODC-By; 182 shards, url+dump columns read = 21.7 GB): 8,445,933 distinct hosts; 5,447,458 not known (DACH 3,007,940; other TLDs 2,439,518, com 1.38M). Dumps up to 2024 only; DACH not known and last seen 2023+: 441,568.
- CC host index CC-MAIN-2025-18 (commoncrawl/host-index-testing-v2, fetch_200 > 0, de/at/ch): 840,561 not known; 462,368 also not in cc43.
- HPLT v2 deu_Latn (CC0; 2.8% shard sample): 2,275,164 hosts, 1,124,688 not known (DACH 625,019); Internet-Archive-only 405k (DACH 250k): the only non-CC source.
- FineWeb-2 dialect configs (gsw, nds, ltz, bar, ...): 29,436 not known (DACH 7,366).
- Gated or no URLs: CulturaX, OSCAR (gated), German Commons (no URL column), FineWeb2-HQ (subset of FineWeb-2).
Liveness and imprint yield untested -> E27-hf-source-pilots.

### E25-cc-seed-pilot (done 2026-11-03; D33; lists tmp/E25/, mispel d29 tree datasets/E25/pilot)
Candidate list from Common Crawl CC-MAIN-2026-43, .de/.at/.ch hosts with a German page: 2,691,932 -> not known (seeds + E22 frontiers, www-collapsed), passed clean-hosts + E10 platform filters, www-collapsed within the list: 618,841 (de 437,194, ch 112,434, at 69,213; cc43_dach_new.txt sha256 a607305a...). Pilot 20,000 random (seed 25, stratified by TLD), mispel 16:30-17:39 UTC, Shopify skipped: imprint_found 9,918 = 49.6% of all hosts (53.3% of reachable); de 57.1%, at 44.0%, ch 24.0%. host_not_found 5.7%. Lead-verified (sha256 + status counts). Yield > 10% -> full crawl E26-cc-dach-full-crawl (598,841 rest hosts) running since 17:43 UTC on mispel/abelie/apfel/aspe; 50% imprint_found in the first 33.7k rows.

### E33-more-dump-pilots
- Four new pools minus all known/crawled hosts: Q3 CC host index 2024-46..2025-13 DACH 453,428; Q4 HPLT v2 IA-only DACH 516,971; Q1 FineWeb-2 DACH last seen before 2023 1,475,809; Q2 FineWeb-2 non-DACH 1,730,374.
- Pilots (5,000 each): Q3 20.7%, Q4 20.9%, Q1 18.1% imprint_found (pass D33); Q2 8.1% (fails; net 12.7%, eu 11.3%, com 9.4%). Q1/Q4 host_not_found ~64%.
- Full crawl of Q4+Q3+Q1: 2,429,968 hosts (tmp/E33/e33_rest.txt), waits for D36-fetch-recall-patch. Details tmp/E33/summary.md.

### E34-new-seed-outlink-pilot
- Frontier of hosts linked from E25-E30 pages (snapshot 21:21 UTC), minus all known/crawled: 49,142 (tmp/E34/frontier_new_seeds.txt, sha256 cf9361b7...); ~0.11 new hosts per fetched host; com 34%, de 15%, ch 8%, at 2%.
- Pilot 5,000: imprint_found 555 = 11.1% (14.6% of reachable); DACH 406/1,239 = 32.8%, other TLDs 149/3,761 = 4.0%; host_not_found 24%. Passes D33; full crawl of 44,142 running on mispel since 22:10 UTC (datasets/E34/full). D16 address filter at merge.

### E32-imprint-recall-audit
- 300 DACH imprint_not_found hosts (150 E26, 150 E16): 20 (6.7%, CI 4.4-10.1%) have a real imprint (name + postal address); 6 of them are crawl-time errors. Missed by today's code 4.7%.
- Best changes: accept the already fetched Kontakt page with imprint word + evidence (7 strict), /impressum.php and /impressum.htm, probe after failed link candidates. Patch finds 18/20 on 32 replayed hosts; new yield 4.0% (CI 2.3-6.9%). Details tmp/E32/summary.md; decision D36-fetch-recall-patch.

### E28-cc-other-tld-pilot (done 2026-11-03 20:26 UTC; D33; tmp/E28/, lorbeer d29 tree datasets/E28/p1, p2; summary tmp/E28/summary.md)
Pools from E23 minus the E25/E26 list and E27 pilots: P1 non-DACH TLD 1,051,969, P2 DACH from older crawls 515,649. Pilots 5,000 random each (seed 28), Shopify skipped. P1: imprint_found 918 = 18.4% (22.0% of reachable, host_not_found 14.4%); com 18.6%, org 24.7%, net 19.8%, eu 27.3%, info 29.7%; it/nl/pl ~4-6% (~100 hosts each). P2: 1,901 = 38.0% (45.5% of reachable); de 41.3%, at 36.0%, ch 21.5%. Per German page count, P1 1 page 15.9%, 2 15.6%, 3-5 17.9%, 6+ 20.0% -> no page threshold (all buckets > 10%). Both > 10% -> full crawl E30-cc-other-tld-full-crawl (minus E27/E29 pools).

### E27-hf-source-pilots (done 2026-11-03 20:07 UTC; D33; tmp/E27/, mispel d29 tree datasets/E27/p1-p3)
Three disjoint DACH pools from E24, minus the E25/E26 list and known hosts (www-collapsed), classify() filters: P1 Common Crawl host index 2025-18 558,420 (pool_p1.txt 07d77156...), P2 FineWeb-2 last seen 2023+ 229,894 (ddb1a3e9...), P3 HPLT Internet-Archive-only 212,634 (d2e025ca...). Pilots 5,000 random each (seed 27), Shopify skipped. imprint_found / all: P1 1,391 = 27.8% (37.8% of reachable, host_not_found 25.1%), P2 1,459 = 29.2% (61.5%, host_not_found 51.2%), P3 1,077 = 21.5% (64.2%, host_not_found 54.3%; 604 filtered, mostly *.blogspot.de / *.blog.de). .ch weakest in all three (14.6-21.3%). Lead-verified (status counts, sha256, driver exit 0). All > 10% -> full crawl E29-hf-pools-full-crawl.

### E23-cc-seed-candidates (done 2026-11-03; D33; tmp/E23/, script scripts/E23/cc_candidates.py, commit e0e4036)
German hosts on ALL TLDs from 8 Common Crawl crawls (CC-MAIN-2026-43 back to 2026-12), rule: primary content language deu; minus known hosts (seeds + E22 frontiers, www-collapsed), clean-hosts (-177,802) and E10 platform filter (-7,597): cc_german_candidates.txt 2,175,470 hosts (sha256 03b7860b...). DACH 1,123,501 (de 826,700, ch 183,632, at 113,169); other TLDs 1,051,969 (com 527,404, net 58,011, org 52,189, eu 47,381). New hosts per extra crawl level off at ~5% (115-130k). Lead-verified: sha256 OK, distinct after collapse, 0 of 3,000 sampled hosts known. Overlaps (www-collapsed): with the E26 list cc43_dach_new 605,815; with E24 host index 437,170, FineWeb-2 707,648, HPLT sample 162,363. Noise: 20% of hosts have only one German page; 603k hosts seen in one crawl only; subdomains/infrastructure hosts included; name sample of com/org/eu/net/info ~40-50% look German. Liveness and imprint yield untested -> other-TLD pilot (proposal E28).

### E16-snapshot-crawl-seeds (done 2026-10-29; imprint count vs the original dataset)
Dedup count 2026-11-03 15:59 UTC (scripts/E22/dedup_count.py; exact host): E16 3,256,728 + E19 r1 10,657 + E19 r2 44,087 + E22 depth-1 A 224,811 + B 5,085 + depth2P 19,988 + depth2R (22% done) 3,638 = 3,564,994 unique imprint_found hosts vs original 3,226,331 (+10.5%). With www.x = x: 3,136,881 (headline count per D34-release-www-dedup; the paper reports no comparison with the original), because 423k E16 sites are found under both www.x and x. The original count was probably exact-host too (E16 alone matches it within +0.9%).
Count 2026-10-29 ~16:00 UTC (unique hosts with status imprint_found, all VMs): E16 seeds 3,256,728 of 6,560,119 rows (49.6%) vs original 3,226,331 (+30,397, +0.9%). Added so far: E19 round 1 10,559 (4 shards 82-94% + 22,909 old rows), E22 depth 1 137,916 of 1,396,338 rows (9.9%). Projection before depth 2: E22 A ~225k, B ~9k, E19 round 1 ~12-13k, E19 round 2 (batches 50-262, not started) ~40-55k (round-1 rate scaled) -> ~3.5M (+~10%). Caveats: D16 keeps link-expansion imprints only with a DACH address (E10: 83%), so E22's final count is lower; E9 precision of newly gained imprints 49/50.

### E22-link-frontier-round1 (frontier A built; depth-1 crawl running on 5 VMs; scripts/E22/)
Frontier A, 2026-10-29 02:01 UTC snapshot of E16 discovered hosts from 6.3M fetched seeds (252 of 263 batches): 2,275,329 new hosts (0.361 per fetched host), sha256 dcd5f325...; aspe datasets/E22/snapA/. Funnel: 12.45M discovered lines -> 4.39M unique -> 2.05M seeds dropped -> 23k platforms -> 36k www duplicates. TLD: other 42.8%, .com 32.9%, .de 9.0%, .org 6.8%, .net 3.9%, .ch 2.1%, .at 1.4%, .eu 1.1%. Projection to all seeds: ~2.36-2.37M (below the 2.74-3.01M from the earlier partial snapshot; saturation). 0 overlap with E19 lists.
E22 TLD yield (2026-10-29 ~06:00 UTC, scripts/E22/tld_yield.py, first 352,168 depth-1 hosts = random 15.5% of A): Impressum 9.9%, German-language Impressum 8.65% of hosts (E16 seeds: 46.5%), host_not_found 21.4%. German Impressum per host: .de 54.4%, .at 51.4%, .ch 33.7%, .eu 13.1%, .info 11.8%, .net 4.1%, .com 3.4%, .org 1.9%. DACH TLDs: 12.5% of hosts, 73.4% of German pages; .com: 33% of hosts, 12.9%. Projection for all of A: ~197k German Impressum pages. Depth 2 order: D26 B (all TLDs; de,at,ch,eu,info,shop list first).
E22 depth-2 probe (2026-10-29 ~06:30 UTC, aspe depth1A, 125,086 fetched depth-1 hosts; seeds + frontier A known): 1.33M discovered lines -> 429k unique -> 157k new (1.25 per fetched host); projection for all of A 1.6M (Heaps) to 2.9M (linear). Priority TLDs only 6,653 (4.2%; .de 2,694); .com 61k, other 72k. Depth 2 drifts away from DACH.

E22 depth 2 priority + B (done 2026-10-31; tld_yield.py on abelie): depth2P 86,098 hosts, 19,988 imprint_found (23.2%), German-language Impressum 18,471 (21.5%; .de 35.8%, .at 55.0%, .ch 22.6%, .eu 2.4%, .info 1.7%, .shop 3.4%) vs depth 1 on the same TLDs 45.6% (abelie depth1A, 43,288 hosts): yield halves per depth step. Depth-1 non-priority TLDs: 2.36% (com 3.35%, net 4.17%, org 1.92%, nl 0.22%; 256,712 hosts). Frontier B depth 1 (apfel): 59,046 hosts, 5,085 imprint_found (8.6%). Card D29-depth2-rest-scope.
Earlier partial snapshot (superseded):
Round-1 frontier from E16 discovered hosts, snapshot 2026-10-26 17:23 UTC (batches 0-57 aspe, 157-164 apfel; 1,624,945 seed hosts fetched); E14 rules (clean-hosts filter, drop seeds incl. www variant, E10 platform filter, www collapse).
- 745,075 new hosts = 0.459 per fetched host (E14 on 20k: 0.59); 52.6% of unique discovered hosts are seeds. Lead recount of the file matches.
- By TLD: .com 32.9%, .de 9.3%, .org 6.8%, .net 4.1%, .ch 2.1%, .at 1.4%, .eu 1.1%, other 42.3%; .de/.at/.ch 12.8% (E14 13.6%).
- Projection to all 6.56M seeds: 2.74M (Heaps fit) to 3.01M (linear) depth-1 fetches, below E14's 3.5-3.9M; the drop is saturation (the fit gives ~0.63 at 20k). One fit from 10 checkpoints, extrapolated ~4x.
- No overlap with the E19 recovery lists (those are seeds).

### E20-fetch-memory-leak (merged)
Orphaned request threads kept downloading endless bodies; fixed. Test: RSS 1,901 -> 1,061 MB after 3x1,000 hosts. Production check pending.

### E19-crawl-recovery-pass (rounds 1-2 done except 36,577 Shopify hosts, D32)

Round 2 report (2026-11-03, lorbeer results/E19/round2_report.tsv): 227,711 listed, 191,134 done, 44,087 imprint_found (23.1% of listed), all net new vs E16; by cause throttle 29,885/114,193 (38.5%), timeout 10,644/85,594 (12.4%), conn_refused 3,558/27,924 (12.7%); 36,577 not retried (Shopify, D32).
41,516 of 525,000 hosts (7.9%) retryable: 403 21.3k, timeout 8.7k, 429/503 8.4k, conn 3.1k; many on Cloudflare.
Pilot, 1,000 random retryable hosts re-fetched from apfel (second IP, same /24 as aspe; 2 per provider, 2 s gap; results/E19/pilot_report.tsv on aspe):

| First-pass cause | Hosts | Imprint found | Reachable, no imprint | Still failing | Imprint found % |
|---|---|---|---|---|---|
| 429/503 throttle | 222 | 120 | 21 | 81 | 54.1% |
| 403 | 525 | 3 | 3 | 519 | 0.6% |
| timeout | 185 | 19 | 23 | 143 | 10.3% |
| conn/refused | 68 | 6 | 6 | 56 | 8.8% |
| total | 1,000 | 148 | 53 | 799 | 14.8% |

- 403 is site/CDN policy, not the IP: recovery rounds skip it. Strato hosts: 11 of 23 reachable from apfel, so the second IP is not blocked wholesale.
- Round 1: 55,887 non-403 retryable hosts from E16 batches 0-49 (throttle 29.5k, timeout 19.4k, conn 7.4k of 1.25M crawled; 403 50.6k skipped).

### E17-gold-capture (merged; captures in datasets/gold/<host>/, summary results/E17/capture_summary.md)
952 items captured: 620 landing+imprint, 283 landing only, 49 failed (37 no DNS); 48 Strato hosts deferred to a second IP: captured 2026-10-26 from apfel and akazie: 26 landing+imprint, 12 landing only, 10 failed (Strato throttles each IP after a few dozen requests). All 1,000 gold hosts now attempted: 941 captured (646 landing+imprint, 295 landing only), 59 failed. 8 pages keep a cookie banner after reject; 12 screenshots cut at 20,000 px (flagged). 2.22 GB.

### E18-gold-labelling-tool (merged; docs/annotation_guideline.md, docs/annotation_howto.md)
- Local labelling tool `PYTHONPATH=src python -m ic.gold.annotate --labeller L1|L2|L3` (screenshot, DOM text, form; select-and-split for addresses; no model or stratum info shown). Browser check scripts/gold/e18_browser_check.py: 22/22.
- Assignment datasets/gold/assignment.jsonl: L1 650, L2 325, L3 325 labels (50 calibration by all three; 950 single primary; 200 second labels on a different person). Guideline judgement calls: card D21-guideline-open-points.

 (merged; design docs/gold_set_design.md v0.2, tables results/E12/screening_prevalence.md, results/E12/gold_sample_quotas.md)
- 10,000 random seed hosts screened (frame 6,557,719): live 71.4%, HTTP error 12.6%, unreachable 7.5%, cross-domain redirect 6.9%; imprint found 57.7% of live; address only in an image 15 hand-confirmed (0.36% of imprints).
- Gold sample datasets/E12/gold_sample.jsonl: 1,000 items = 700 random core + 300 oversample, target 30 per stratum (seed 20261025); 799 live, 219 no-imprint and 201 not-live negatives (core only); Horvitz-Thompson weights 656-16,582. Short strata (all screened hosts used): Nightlife 3, Blogger 8, Landmarks 13, image-only 15.
- Doubts: Strato /24 answered 503 for 578 hosts (gold capture must run from another IP); no-imprint share on live .de/.at/.ch 16.3% vs 12.1% in E8 (unexplained).

### E14-link-expansion-depth (merged; report docs/experiments/E14-link-expansion-depth.md)
- DACH-address imprints per 1,000 fetched: seeds 432, round 1 85, round 2 20, round 3 8; on .de/.at/.ch hosts 603, 413, 181, 121. Frontier grows per round (0.59, 1.27, 2.07, 3.11 new hosts per fetched host). ~40% of round 2-3 imprints duplicate earlier operators.
- Full run from 6.56M seeds: depth 1 all TLDs 3.5-3.9M fetches / 302-332k DACH imprints; + depth 2-3 on .de/.at/.ch only 3.9-4.6M / 363-439k; depth 3 all TLDs 11.4-19.1M / 407-512k. Card D19-link-expansion-depth.

### E13-snapshot-dry-run (merged; report docs/experiments/E13-snapshot-dry-run.md)
- Per-provider limit in fetch.py (group = resolved /24 or /48; 4 concurrent, 0.25 s gap, 10 s pause after 429/503, one retry), crash resume per batch; 115 tests.
- 100k random seeds in 283 min (353 hosts/min; steady ~490/min), shared VM. Found/reachable 62.5%, .de 85.0% (E9 63.5%, 83.6%). Strato: 24 of 6,433 hosts blocked (E8: nearly all). 429/503 failures mostly Cloudflare bot challenges.
- 6.56M seeds at the measured rate: ~310 h, ~33 GB (66 GB free). Memory grows ~0.5 GB/h, so run in ranges of ~10 batches. Card D18-snapshot-provider-cap.

### E8-gold-strata-pilot (merged; design docs/gold_set_design.md, tables results/E8/pilot_prevalence.md)
- 1,000 random seed hosts: live 69.4%, HTTP error 13.2% (inflated: Strato hosts answered 503 to the crawl VM), unreachable 8.2%, cross-domain redirect 7.7%.
- Of live: WordPress 31.6%, site builder 10.7%, custom PHP 7.8%, static 7.8%, SPA 3.3%, Blogger 0.3%; JS required 1.2%; domain age <2010 40%, >=2023 11.5%; no imprint 39% (.de/.at/.ch 12%, other TLDs 75%).
- Of imprints: multiple addresses 30%, obfuscation 33%, address only in an image 0.5% (2/422), PDF 0.
- Design: ~1,300 items = 600 random core + ~700 oversampled rare strata, marginal quotas, Horvitz-Thompson weights (card D17-gold-set-size). Detectors spot-checked by hand (tech 20/20, multi-address 18/20, LLM operator type 12/13).

### E11-external-host-discovery (merged; report docs/experiments/E11-external-host-discovery.md)
- The original fetcher stored landing-page links keyed by URL path, so external links (path "/") overwrote each other; fixed in 5d5afa2. Current count (34,771 unique external hosts on 20k seeds vs 19,980) is correct; on 77 re-fetched hosts the fix alone explains the whole difference. E10 estimate stands.

### E10-link-expansion-pilot (merged; report docs/experiments/E10-link-expansion-pilot.md)
- 11,969 new hosts (not in seeds) linked from the 20k seeds: imprint found 1,231/9,182 reachable = 13.4%; 83% of them with DACH address.
- .de/.at/.ch new hosts: 413 DACH imprints per 1,000 fetched (seeds 432); other TLDs 34 per 1,000. Full round adds roughly +2-4% (wide range). Card D16-link-expansion-scope.

### E9-fetch-precision (merged; report docs/experiments/E9-fetch-precision.md) — current fetcher
- Same 20k hosts: 10,246/16,129 = 63.5% of reachable (E4 59.2%, E6 64.2%); .de 83.6% (E4 79.7%).
- Precision of gains vs E4: 49/50 (CI ~89-100%; E6 was 40/50 on a different sample). Recovers 37 of 43 E5 rule misses.
- Not yet judged: ~140 hosts lost vs E6 (likely mostly rejected false positives; 30-host sample would settle it).

### E7-eval-homepage-location (old 1,000-item gold set; report docs/experiments/E7-eval-homepage-location.md)
- Homepages re-fetched for 890/1,000 gold hosts (84 unreachable, 23 empty, 3 filtered; 90 redirect to another host).
- Topic, same 890 items: homepage input is ~2.5 points below imprint input (Qwen acc 0.710 vs 0.734, macro-F1 0.566 vs 0.594; Gemma 0.722 vs 0.748, 0.576 vs 0.601). Likely partly because old gold topics were labelled from imprint text and sites changed since; the new gold set (D14 A) fixes the label source.
- Address by geocoded location (D12): street level <=250 m Qwen 0.982, Gemma 0.972; town level 0.992 / 0.986 (vs exact 0.904 / 0.885). 22/31 Qwen town errors resolve. Caveat: Photon is fuzzy, so street level is lenient (wrong house number can still match); 7 gold addresses do not geocode.

### E4-fetch-yield-baseline
- Small alphabetical sample (1,000): 437 imprints / 819 reachable = 53.4%; not representative.
- Random 20k sample (seed 20261023, 29 min): reachable 16,217; imprint found 9,606 = 59.2% of reachable (paper 58.2%); host_not_found 17.9%.
  - Imprint/reachable by TLD: .de 79.7% (7,106/8,917), .at 86.2%, .ch 78.0%, .eu 65.4%, .net 36.8%, .com 30.4%, .org 20.1%, other 13.6%.
  - Biggest yield target: 1,811 reachable .de hosts without imprint.
- Link expansion signal: the 20k fetch discovered 19,980 unique external hosts, 5,360 (27%) not in the 6.56M seed list; of these 602 .de, 1,985 .com.

### E5-imprint-not-found-causes (200 of the 1,811 .de hosts; report docs/experiments/E5-imprint-not-found-causes.md)
- Parked/placeholder 20.5%, JS-only/empty 17.5%, missed by fetch rules 17.0%, genuinely no imprint 11.5%, redirect/spam 7.0%, link target failed 6.0%, imprint on landing page 5.0%, /impressum exists but unlinked 4.5%, other 11%.
- Static-rule fixes would recover 42/200 = 21% (CI 15.9-27.2%), about 380 of the 1,811: .de found rate 79.7% -> ~84.0%. Top fixes: key links by full URL (5.5%), keep pages with empty main-content extraction (5%), probe /impressum (4.5%).

### E6-fetch-rule-fixes (merged 8e35e07; report docs/experiments/E6-fetch-rule-fixes.md)
- Same 20k hosts: imprint found 10,327/16,093 = 64.2% of reachable (E4 59.2%); .de 7,469/8,888 = 84.0% (E4 79.7%).
- 873 gained, 152 lost (56 removed old false positives: landing-page shells, PDFs decoded as "None"; 96 crawl noise). Recovers 39 of the 42 E5 rule misses.
- Precision of gains 40/50 = 80% (CI 67-89%); 5 of 10 errors from the English keyword "imprint" (product pages). Changed URLs 17/20. Superseded by E9.
- stats.py/merge.py now count an address only if a field is non-empty.

### Findings on the original pipeline
- stats.py counts all-empty LLM addresses as extracted: the paper's 3,225,347 "extracted address" is a count of responses.
- Qwen3-Next (paper model) is no longer served on innkube.

## Next steps
See "Next" of the latest brief and decisions.md "In flight".
