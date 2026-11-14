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

`E31/recount.sh PKG OUT [--r5|--final]` runs the whole no-crawl chain on the data package (release count, parking
filter, finalize, sha256 compare). `--final` gives the final count r5 from `counts/r5/`; see
[`docs/reproduce_collection.md`](../docs/reproduce_collection.md).
`E40/parking_filter.py apply --name-for-sale-flag-only` keeps sites flagged only by `r2_name_for_sale` (r5 rule).

### Imported run scripts (D47)

These scripts ran from the lead's temp folder (`/home/dinzinger/.claude/jobs/cfd8c2d0/tmp`) or from the crawl
VMs and were imported unchanged in D47 (source path per file: `docs/inventory.tsv` and `scripts_to_import.tsv`
in the data package). They are the record of what ran, not cleaned-up tools.

| ID | Folder | What it does | Step |
|---|---|---|---|
| E19 round 1 | `E19r1/` | D25 reshard launch (`d25_apfel.sh`, `d25_waiter.sh`), E22 depth-1 start (`e22_start.sh`, `e22all.sh`, `run_frontier.sh`, `hosts_e22.py`), `run_test.sh`, `e19.sh`. | crawl launch |
| E19 round 2 | `E19r2/` | Round 2b-2d: `plan_d30.py` / `plan_d31.py` build the round2c / round2d lists; `deploy_d30.sh`, `deploy_d31.sh`, `launch_d30.sh`, `launch_all.sh`, `launch_e19agent.sh`, `pilot.sh`, `pre.sh`, `prep.sh` start them; `collect*.sh`, `gather.sh`, `merge1.sh`, `list2.sh` collect results; `stop*.sh`; `net.py`, `shopcount.py`, `ua.sh` (403 / User-Agent checks). | list build, crawl launch |
| E22 depth 2 rest | `E22d2R/` | `pre.sh`, `deploy.sh`, `launch_all.sh`: deploy the d29 tree and crawl `round2_frontier_rest.txt`. | crawl launch |
| E24 | `E24/` | Host extraction from FineWeb-2 (`fw_shard*.py`, `run_fw.sh`), HPLT (`hplt_meta.py`, `run_hplt.sh`), Common Crawl host index (`hostindex.py`, `hi.py`); `httpfile.py` HTTP range reads; `agg.py`, `mkknown.py`, `extra.py`, `meta.py`, `hf*.py`. Output: the E24 parquets used by E27, E33, E41. | list build |
| E25, E26 | `E25/`, `E26/` | `E25/build.py` builds the CC-MAIN-2026-43 DACH pool, the 20k pilot (E25) and the rest (E26); `E26/e26_launch.sh` (copied from mispel). | list build, crawl launch |
| E27-E30 | `E27/` ... `E30/` | `build.py` per experiment (pilots P1-P3, CC 8-crawl pilots, full pools); `e27_run.sh`, `e28_run.sh`, `launch_*.sh`, `setup_*.sh`, `remote.sh` start `scripts/E22/run.sh` on the VMs. | list build, crawl launch |
| E33, E36 | `E33/` | Pilots Q1-Q4 and the full crawl: `build.py`, `mkexcl.py`, `mkq3.py`, `q3_load.py`, `hplt_shard.py`, `run_hplt.sh`, `run_q3load.sh`, `build_rest.py`; `deploy.sh`, `launch*.sh`, `chain.sh`, `e33_run.sh`, `setup_lorbeer.sh`. E36 (re-check pilot) is here too: `mk.py`, `launch_e36.sh`. | list build, crawl launch |
| E34 | `E34/`, `E34/round2/` ... `round4/` | Outlink rounds 1-4: `build*.py`, `mk_*.py`, `tld_groups.py`, `snap*.sh` (frontier snapshots); `setup_*.sh`, `deploy*.sh`, `launch*.sh`, `*_run.sh`, `go_pilot.sh` start the crawls; `pull*.sh`, `getall.sh` collect results; `round3/verify_ua.sh` checks the D39 B User-Agent. | list build, crawl launch |
| E37 | `E37/` | Re-check of E16 DACH not-found: `mk.py`, `deploy.sh`, `launch_e37.sh`, `a12.sh`. | list build, crawl launch |
| E31, E40 extras | `E31/`, `E40/` | `E31/run_pull.sh`, `copy.sh` (r3 pull and copy); `E40/run_apply.sh`, `keep.sh`, `classify.py`, `counts.py`, `labels.py` (round-1 runs). | recount, filter |
| E41, E43, E44 extras | `E41/`, `E43/`, `E44/` | `copy_all.sh`, `copy_full.sh` (copy results to lorbeer), `E43/launch*.sh`, `mkrest.sh`, `wait_e43.sh`. | crawl launch |
| E42, E45-E48 | `E42/`, `E45/` ... `E48/` | Shopify: `E42/s1.py`, `s1b.py` (Shopify host set), `s2.py` (re-pilot list); `draw.py` (lists, fixed seeds), `start.sh`, `launch.sh`, `watch.sh`, `final.sh`, `E45/loop.sh`, `E48/vmrun.sh`, `chk.sh` drive `scripts/E19/run.sh` at 1 request per 2-60 s. | list build, crawl launch |

Five candidates were not imported because they are byte-identical to files in git: `tmp/e22_run.sh` and
`datasets/E22/code/scripts/E22/run.sh` (= `scripts/E22/run.sh` before f9da3ad), `~/stage_run.sh` and
`datasets/E19/code/scripts/E19/run.sh` (= `scripts/E19/run.sh` before f9da3ad), `datasets/E19/reshard/reshard.py.used`
(= `scripts/E19/reshard.py`).

### Absolute paths

Most scripts were written for one machine. Path constants at the top of a script (`ROOT`, `T`, `D`, `R`, `W`,
`PY*`, `OUT`, ...) can be set from the environment; the old value is the default, so a script without env runs
as before:

```console
T=/data/tmp D=$HOME/trees/imprints-collection-d29 bash scripts/E34/round2/snap.sh
ROOT=$PWD python3 scripts/E16/shuffle.py
```

Not covered (read the script before you run it):

- paths inside the script body: `cd /home/dinzinger/GitLab/.../worktrees/agent-...` (`E31/run_pull.sh`,
  `E40/run_apply.sh`), `os.chdir(...)` (`E42/s2.py`), `sys.path.insert(0, '/home/.../tmp/E24')` (`E24/fw_shard*.py`),
  DuckDB `temp_directory` (`E24/hostindex.py`), and literal paths in `open(...)` (`E40/counts.py`, `E40/labels.py`);
- remote paths in single quotes that the VM shell expands (`'$HOME/GitHub/imprints-collection-d29'` in `snap*.sh`,
  `PYA='...'` in `E37/deploy.sh`) and VM names in ssh loops;
- relative paths (`E42/s1.py` reads `E31/r3/in/` from the current folder).

## Other module: gold set and extraction

`gold/` (E8, E12, E17, E18, E21) and `gold_homepages.py` (E7) belong to the gold-set module (see
`docs/gold_set_design.md`). They are not part of the data collection and are documented there.
