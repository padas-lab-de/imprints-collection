# E10: Link expansion pilot

Date: 2026-10-23. Branch `E10-link-expansion-pilot` (from `lead-record` 109bb07). Follows D6 (snapshot growth source: better fetch yield and link expansion). No change to `fetch.py`.

Question: does fetching the external hosts that the 20k random seed fetch discovered grow the German-speaking snapshot, and which filter keeps a full expansion round on target?

## Candidates

Inputs: `discovered_external_hosts.txt` of E4 (25,353 lines, 19,980 unique) and E9 (41,853 lines, 34,771 unique). E9 uses the current fetcher; it discovers more external hosts per seed than E4 (see doubts). Seed list: `seed_hosts.txt.gz` (6,560,119 hosts).

Normalisation as in `ic clean-hosts`: lower-case, strip, dedupe, `check_url(host, is_host=True)`; all 35,075 unique hosts pass.

| Step | Hosts |
|---|---|
| Union of E4 and E9, unique | 35,075 |
| After clean-hosts filter | 35,075 |
| In seed list (exact) | 21,395 (61%) |
| In seed list as `www.` variant | 1,559 |
| New, not in seed | 12,121 |
| Dropped platforms | 101 |
| `www.x` and `x` both new, collapsed | 51 |
| **Candidates fetched** | **11,969** |

Platforms dropped (`results/E10/dropped_platforms.tsv`): `*.wordpress.com` 63 (hosted blogs; arguably real sites, dropping them is conservative), Mailchimp `list-manage` 7, `*.amazonaws.com` 6, Weebly 4, SourceForge 4, Typeform 3, Weibo 3, Medium 2, CloudFront 2, Zendesk 2, Airbnb 2, `googleapis`, `windows.net`, GitLab 1 each. Few platforms remain because facebook, youtube, google, app stores and the like are already in the 6.56M seed list (the 22,954 hosts removed by the seed check include them). User-site hosts (github.io, blogspot, wixsite, netlify, ...) were kept and fetched.

Candidates by TLD (`results/E10/tld_final.tsv`): .com 3,857, .de 1,199, .org 776, .uk 518, .net 340, .ca 274, .it 262, .ch 230, .nl 205, .fr 205, .ru 196, .tr 192, .at 190, .io 176, .jp 171, .eu 140, other 3,038. In short: 13.5% are .de/.at/.ch (1,619), 32% .com.

## Run

Same settings as E9 (64 workers, UA `Mozilla/5.0`, one batch). `datasets` in the worktree is a symlink to `datasets/E10/expansion`.

```
python scripts/E10/candidates.py results/E10        # candidate list, TLD tables, occurrence counts
cp results/E10/candidate_hosts.txt datasets/E10/candidate_hosts.txt
PY=<python with ic deps> bash scripts/E10/run_fetch.sh   # ic fetch datasets/E10/candidate_hosts.txt
PY=<python with ic deps> bash scripts/E10/run_analysis.sh
```

`run_fetch.sh` runs `PYTHONPATH=$PWD/src python -c "from ic.ic import main; main()" fetch /home/dinzinger/GitHub/imprints-collection/datasets/E10/candidate_hosts.txt`. Output `datasets/E10/expansion/imprints_batch000000.jsonl.gz`, log `results/logs/E10-fetch-expansion.log`, 25.5 min (7.8 hosts/s), analysis output `results/E10/analysis.txt`.

Crawl status of the 11,969 hosts: imprint found 1,231 (10.3%), imprint not found 7,951 (66.4%), host not found 2,704 (22.6%), filtered 64, no valid HTML 19. Reachable (records written) 9,182 (76.7%).

## Results by TLD

"DACH address" = postcode plus town in the imprint text with a country-consistent signal (`scripts/E10/analyze_lib.py`): DE needs a 5-digit postcode + capitalised town and a German legal-notice word or Deutschland/Germany; AT/CH need a 4-digit postcode + town and an Austria/Switzerland marker. "Loose" = the unmodified `_POSTCODE_RE` of `imprint_utils.py` (4-5 digits + town, any country).

| TLD | Fetched | Reachable | Imprint found | Found / reachable | Found / fetched | Loose postcode+town | DACH address (strict) | Strict / found |
|---|---|---|---|---|---|---|---|---|
| .de | 1,199 | 989 (82.5%) | 577 | 58.3% | 48.1% | 550 (95.3%) | 526 | 91.2% |
| .at | 190 | 163 (85.8%) | 103 | 63.2% | 54.2% | 85 (82.5%) | 85 | 82.5% |
| .ch | 230 | 208 (90.4%) | 85 | 40.9% | 37.0% | 69 (81.2%) | 58 | 68.2% |
| .eu | 140 | 103 (73.6%) | 23 | 22.3% | 16.4% | 21 (91.3%) | 18 | 78.3% |
| .com | 3,857 | 2,875 (74.5%) | 220 | 7.7% | 5.7% | 189 (85.9%) | 167 | 75.9% |
| .net | 340 | 241 (70.9%) | 26 | 10.8% | 7.6% | 20 (76.9%) | 20 | 76.9% |
| .org | 776 | 620 (79.9%) | 28 | 4.5% | 3.6% | 28 (100%) | 22 | 78.6% |
| other | 5,237 | 3,983 (76.1%) | 169 | 4.2% | 3.2% | 153 (90.5%) | 124 | 73.4% |
| **all** | 11,969 | 9,182 (76.7%) | 1,231 | 13.4% | 10.3% | 1,115 (90.6%) | 1,020 | 82.9% |
| de/at/ch | 1,619 | 1,360 (84.0%) | 765 | 56.2% | 47.3% | 704 (92.0%) | 669 | 87.5% |
| not de/at/ch | 10,350 | 7,822 (75.6%) | 466 | 6.0% | 4.5% | 411 (88.2%) | 351 | 75.3% |

Among other TLDs the DACH-address imprints sit in `.it` 21 (South Tyrol and German firms with Italian shops), `.info` 13, `.io` 8, `.shop` 7, `.swiss` 4, `.ai` 4; `.uk`, `.ca`, `.fr`, `.ru`, `.tr`, `.cn`, `.au`, `.jp` give almost none (0-2 per 200-500 hosts).

Comparison with the seed list (E9, same fetcher and settings, 20,000 random seeds):

| | Seed (E9) | Expansion (E10) |
|---|---|---|
| Reachable / fetched | 80.6% | 76.7% |
| Imprint found / reachable | 63.5% | 13.4% |
| Imprint found / fetched | 51.2% | 10.3% |
| .de found / reachable | 83.6% | 58.3% |
| DACH-address imprints / 1,000 fetched | 432 | 85 |

New .de hosts reach 58.3%, well below seed .de (83.6%): new .de hosts are often subdomains: 166 of 437 reachable .de subdomains have an imprint (38%) against 411 of 552 for apex and `www.` hosts (74.5%), because subdomains are mostly service, shop and tool pages. Hosts that are linked from two or more of the 20k seeds yield almost nothing: 8 imprints in 477 hosts (1.7%, 6 DACH) against 1,223 in 11,492 (10.6%) for hosts linked once; these are the widely linked service, agency and tool hosts.

Precision of the strict DACH-address flag outside .de/.at/.ch: I read a random sample of 30 (`random.seed(20261023)`, `results/E10/nondach_tld_dach_sample.jsonl`). 29 of 30 contain a real DACH address of the site operator (e.g. `peterproell.com`, `drahtverarbeitung.net`, `sofortimplantat.berlin`, `panzer.quest` with a Swiss company). One page (`living-tunes.hpage.com`) is a privacy text where the address is further down. Caveat: 4 of the 30 are DACH companies behind a non-German-language host (`help.perangkaum.net`, `help.triburile.ro` are InnoGames support pages; `pneumatici100.it`), so "DACH address" means a DACH operator, not a German-language site.

## Filters for a full round

Yield counted in DACH-address imprints per 1,000 fetched hosts (Wilson 95% CI).

| Filter | Hosts fetched | Imprints found | DACH-address imprints | Per 1,000 fetched | Share of all DACH imprints reached |
|---|---|---|---|---|---|
| (a) ccTLD .de/.at/.ch only, fetch only these | 1,619 | 765 | 669 | **413** (389-437) | 65.6% |
| (b) any TLD, keep imprints with DACH address (all must be fetched) | 11,969 | 1,231 | 1,020 | 85 (80-90) | 100% |
| (c) both: fetch all, keep ccTLD or DACH address | 11,969 | 1,231 | 1,020 plus 96 DACH-ccTLD imprints without a strict address | 85 (80-90) for strict; 93 counting the 96 | 100% |

(c) equals (b) in cost, because a TLD filter applied after fetching saves nothing; only (a) cuts fetching. The marginal numbers are what decides: the 10,350 non-DACH-TLD hosts (86.5% of the cost) give 351 DACH imprints (34 per 1,000, CI 31-38), 34.4% of the total. Per group per 1,000 fetched: .de 439, .at 447, .ch 252, .eu 129, .net 59, .com 43, .org 28, other 24. For comparison the seed list yields 432 per 1,000 fetched.

A middle path would add .com (43 per 1,000, 167 DACH imprints for 3,857 fetches) to (a); I do not recommend it as a default.

Recommendation for a full round: filter (a) as the fetch filter. It reaches two thirds of the DACH imprints at 13.5% of the cost and its yield (413 per 1,000) matches the seed list (432). Also drop hosts linked from two or more seeds before fetching (negligible loss, removes the tool and service hosts). Filter (c) would add 34% more DACH imprints at 7 times the crawl cost; worth it only if crawl time is cheap and the DACH-address filter is applied after fetching.

## Estimate of a full expansion round

Pieces measured in the pilot (E9 discovery, 20,000 seeds):

- 11,910 new non-platform unique hosts, 0.596 per seed host (E4's older discovery gave 4,200, 0.21 per seed).
- 96% of them (11,433) are linked by exactly one of the 20k seeds, 411 by two, 66 by three or more. A random subsample of the occurrences gives 781, 1,555, 3,083, 6,095, 11,910 new hosts for 1,250 / 2,500 / 5,000 / 10,000 / 20,000 seeds: no saturation visible (Heaps fit exponent 0.98).
- DACH-address imprints per fetched new host: 8.5% (CI 8.0-9.0%) for all hosts, 41.3% for the .de/.at/.ch share, which is 13.5% of the new hosts.

Scaling to 6.56M seeds:

| Scenario | New hosts | DACH imprints, fetch all (b/c) | DACH imprints, ccTLD only (a) | Hosts fetched for (a) |
|---|---|---|---|---|
| Lower bound: Chao1 pool at 20k seeds (170,929), no further growth | 171,000 | 14,600 | 9,500 | 23,000 |
| Linear in seeds (0.596 x 6.56M) | 3.9 million | 333,000 (CI 314,000-353,000) | 218,000 | 528,000 |
| Heaps extrapolation (exponent 0.98) | 3.6 million | 304,000 (CI 287,000-322,000) | 199,000 | 483,000 |

The honest range for a full round is therefore 15,000 to about 300,000 DACH-address imprints. The width comes entirely from how many distinct new hosts 6.56M seeds link to. Singletons dominate (96%), so the 20k sample is far from saturated and the pool is probably much larger than the Chao1 lower bound, but a 328-fold extrapolation has no empirical support: in the full link graph the same new host is linked by many more seeds, so the unique count grows slower than linear. A plausible middle (not computed, a guess) is 1-2 million new hosts, giving 90,000-170,000 DACH imprints for all and 60,000-110,000 for (a).

Context: the seed snapshot has about 6.56M x 51.2% x (8,644 / 10,246 DACH-address) = about 2.8M DACH-address imprints at E9 yield, so (a) would add 0.3-8% (middle scenario 2-4%) and (b/c) 0.5-12% (middle scenario 3-6%). Link expansion is a modest growth source compared with the better fetch yield (D6's other half): E9 raised the .de yield by 4 points on the seed list.

Fetch time at the pilot speed (7.8 hosts/s, 64 workers): 483,000-528,000 hosts for filter (a) take 17-19 hours; the full 3.6-3.9 million for (b/c) take 5-6 days.

Assumptions: (1) the 20k seeds are a uniform random sample of the 6.56M (E4 seed 20261023); (2) discovery per seed and the yield per new host stay the same in the full round, i.e. the pilot's first-hop hosts are representative; the yield is likely lower for the long tail of hosts reached only in a full round and is already low for multiply linked hosts; (3) the DACH-address yield uses my strict regex, whose precision is about 97% on a 30-host sample and whose recall was not measured (96 DACH-ccTLD imprints lack a strict match, 12.5%); (4) a full round fetches hosts once, with no second hop; (5) no deduplication against hosts that appear in the future seed list.

## Open doubts

- E4 and E9 discovered files differ by a factor of 1.7 in unique external hosts (19,980 vs 34,771) on the same seeds. `fetch.py` changed in E6/E9 (candidate ranking, retries, base href, link handling), but I did not find which change causes the extra discovery; if the earlier E4 behaviour is the correct one the new-host rate is 0.21 per seed and the totals above shrink by 65%. Worth a one-line check of the E6 diff before the full round.
- The 12.5% of DACH-ccTLD imprints without a strict address are not inspected (PO box only, no postcode, foreign-format?). A 30-sample file is written to `results/E10/dachtld_noaddr_sample.jsonl`, not yet read.
- The scale-up of the new-host count is the dominant uncertainty; a 200k-seed pilot (10 times larger, about 2 hours of discovery fetch plus 2 hours expansion fetch) would give a second rarefaction point and settle linear versus saturating.
- `*.wordpress.com` hosted blogs (63) were dropped as platforms; user sites on other builders were kept.
- "DACH address" says operator location, not German-language content; for the German-speaking snapshot, language identification of the homepage (`identify_language`) was not applied here.
- Single run, no repeat; crawl noise in E9 vs E6 was about +-100 hosts of 20,000, here roughly +-60 hosts of the 11,969.

Files: `scripts/E10/{candidates,analyze,analyze_lib,seed_dach_yield}.py`, `scripts/E10/run_{fetch,analysis}.sh`; outputs under `results/E10/` (untracked): `analysis.txt`, `candidates.txt`, `candidate_stats.json`, `tld_*.tsv`, `dropped_platforms.tsv`, `e9_new_occurrences.tsv`, sample jsonl files.
