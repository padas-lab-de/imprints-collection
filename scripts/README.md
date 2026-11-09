# scripts/

Experiment scripts of the German Imprints Dataset. One folder per experiment ID (`E<n>`).
The experiment IDs are defined in [`docs/decisions.md`](../docs/decisions.md); the history of the whole
data collection is in [`docs/collection_history.md`](../docs/collection_history.md) (its appendix maps
each ID to a section). How to reproduce the collection: [`docs/reproduce_collection.md`](../docs/reproduce_collection.md).

The crawler itself is `ic fetch` (`src/ic/cli/fetch.py`). The scripts here build host lists, start
`ic fetch` on the crawl VMs, and count and filter the results. Many scripts hold absolute paths of the
crawl VMs (`/home/dinzinger/...`, `~/.claude/jobs/.../tmp`); see "Known non-reproducible parts" in
`docs/reproduce_collection.md`.

## Pipeline steps

| Step | Meaning |
|---|---|
| list build | Make a host list to crawl (seed list, link frontier, Common Crawl / FineWeb-2 / HPLT pools, pilots). |
| crawl launch | Start or drive `ic fetch` on one or more VMs for a list (resumable). |
| recount | Pull the `fetch_status_batch*.tsv` rows of all crawl dirs and count unique sites (D34 rule). |
| filter | Drop parked, for-sale and hosting-default sites from the count (E40). |
| fetcher test | Pilot, dry run or analysis that tuned the fetcher before the main crawl. Not needed to reproduce the data. |

## Collection experiments

| ID | Folder | What it does | Step |
|---|---|---|---|
| E6 | `E6/` | Static-rule fixes of the fetcher: compare E4 vs E6 output on the random 20k, loss categories, hand judgements of a precision sample. | fetcher test |
| E9 | `E9/` | Fetcher precision: compare E9 with E4/E6, precision sample with hand judgements. | fetcher test |
| E10 | `E10/` | Link-expansion pilot: build new-host candidates from discovered external hosts (`candidates.py`), fetch them (`run_fetch.sh`), yield analysis. | list build, crawl launch |
| E11 | `E11/` | External-host discovery bug: run the E4 and the current `discover_links` on the same landing pages. | fetcher test |
| E13 | `E13/` | 100k dry run with the per-provider limiter: sample, run, resume test, capacity and RSS analysis. | fetcher test |
| E14 | `E14/` | Depth of link expansion: per-round candidates, frontier sample, full-run estimate. | list build |
| E15 | `E15/` | Cap test: 8 concurrent requests per provider network on 25k random seeds (D18). | fetcher test |
| E16 | `E16/` | Seed-list crawl: `shuffle.py` shuffles `seed_hosts.txt.gz` (seed 20261024) to `datasets/E16/seed_hosts_shuffled.txt`; `run.sh` crawls 263 batches of 25k, cap 8; `rss_log.sh` logs memory. | list build, crawl launch |
| E19 | `E19/` | Recovery passes from a second IP: `collect.py` selects retryable E16 failures, `run.sh` crawls them slowly, `reshard.py` splits the rest (D25 B), `merge_report.py` reports what was won back. | list build, crawl launch |
| E22 | `E22/` | Outlinks of the seeds (depth 1, 2): `frontier.py` builds the frontier, `run.sh` is the generic crawl driver (also used by E41), `dedup_count.py` the first dedup count, `tld_yield*.py` yield per TLD. | list build, crawl launch, recount |
| E23 | `E23/` | Common Crawl 8-crawl union: German hosts on all TLDs not crawled yet (DuckDB over cc-index Parquet). | list build |
| E31 | `E31/` | Release count (D34): `sources.tsv` lists every crawl dir per VM in count order; `extract.py` makes compact (host, status, redirect target) rows; `pull.py` runs it on all VMs; `release_count.py` counts sites; `compare_r3_r4.py` checks recount r3 against r4 and writes the site lists with sha256. | recount |
| E40 | `E40/` | Parking / for-sale / hosting-default filter: `targets.py` + `targets_classified.tsv` (big redirect targets), `parking_filter.py` (patterns; `scan` per crawl dir, `apply` on the E31 sites), `scan_all.py` (scan of every E31 dir), `finalize_r2.py` (after-filter site list, SHA256SUMS), `sample*.py`, `label_sample.py`, `discover_r2.py`, `r1_view.py` (precision samples and round-1 view). | filter |
| E41 | `E41/` | Other-TLD parity crawls L1-L4: `build_e41.py` builds the lists (FineWeb-2, HPLT, other TLDs), `hplt_shard.py` / `run_hplt.sh` read the HPLT url columns, `verify_lists.py` checks them, `counts_*.json` and `L*.txt.sha256` record the result; `setup_*.sh`, `deploy.sh`, `ship.sh`, `launch.sh`, `run_e41_vm.sh` deploy the tree and drive `scripts/E22/run.sh` per VM; `st.sh`, `vmcheck.sh` read-only status. | list build, crawl launch |
| E43, E44 | `E43/` | HPLT rest (E43) and FineWeb-2 dialect configs (E44): `mkfiles.py`, `hplt_shard.py`, `run_hplt.sh` read HPLT; `build_e43e44.py` builds pools and 5k pilots; `run.sh` (copy of `E22/run.sh` plus `WORKERS`, `LOGS`), `run_pilots.sh`, `run_full.sh` (restart loop, D41 A) drive the crawls; `analyze.py` pilot yield. | list build, crawl launch |

`E41/hplt_shard.py` and `E43/hplt_shard.py` (and the two `run_hplt.sh`) differ only in their output folder; both are kept as the record of each run.

### Not in this folder yet

Run scripts of E24-E30, E33, E34, E35-E37, E42 and E45-E48 were run from the lead's temp folder and the
crawl VMs, not from git. TODO(lead): import them (D47 step 2).

## Other module: gold set and extraction

`gold/` (E8, E12, E17, E18, E21) and `gold_homepages.py` (E7) belong to the gold-set module (see
`docs/gold_set_design.md`). They are not part of the data collection and are documented there.
