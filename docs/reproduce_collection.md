# Reproduce the data collection

State: 2026-11-09 (D47 wrap-up, recount r4, parking filter round 2). Data package: `innkube/datasets/imprints/20261109/`.

## Quick start: recompute the count from the package (no crawling)

```console
mc cp --recursive innkube/datasets/imprints/20261109/ ./package/
git clone -b collection-release https://github.com/padas-lab-de/imprints-collection ic && cd ic
scripts/E31/recount.sh ../package ../out    # stdlib only; PY=python3 by default; no pip install needed
cat ../out/compare.tsv                      # every row must say "match"
```

Offline: `package/code/collection-release.bundle` holds the branch as ref `refs/remotes/origin/collection-release`
(`git clone package/code/collection-release.bundle ic && cd ic && git checkout -b cr origin/collection-release`).
TODO(lead): the bundle of 2026-11-09 is at edc3d83, before `scripts/E31/recount.sh` was added; rebuild it from the
pushed branch. For a crawl (not for the recount) also run `python3 -m venv .venv && .venv/bin/pip install -e .`.

`recount.sh` runs `release_count.py` (E31, D34 rule), `parking_filter.py apply` (E40 round 2) and `finalize_r2.py`, then
compares every output with the sha256 values in the package. It exits 1 on a mismatch. Expected result:

| File | Lines | sha256 |
|---|---|---|
| `out/E31_out/canonical_sites.txt` | 4,020,137 sites (D34) | `e4645f32babe1fa3b7cdb22a976f11e7c3c3182129ef6081379cf50f12911f11` |
| `out/E40r2/canonical_sites_after_filter.txt` | 3,908,045 sites | `748f70f44517f62e627997e7697d910956b477fb560b025db1cab1b3c1e717a2` |

Test run on lorbeer (2026-11-09, 16 cores, input = the e35 datasets the package was built from): 7 min 44 s wall
time, 5.1 GB peak RSS (in the parking filter step). 12 of the 13 compared files match byte for byte.
`delta_by_category.tsv` has the same lines, but tied rows of its transition table come out in a different order:
`finalize_r2.py` orders ties by set iteration, which depends on the Python hash seed. `recount.sh` then compares
the sorted lines and reports "match (same lines, order of ties differs)". The package download is about 1.15 GB if
you take only `counts/` and `filter/E40r2/` (the whole package is 21.7 GB, mostly raw crawl output).

`--r5` as third argument makes `r2_name_for_sale` flag only (`parking_filter.py apply --name-for-sale-flag-only`, the
r5 rule): those sites stay in `flagged_sites.tsv` with category `sale_flag` but are not dropped. The after-filter
files then differ from the package; `compare.tsv` marks this as expected.

Integrity of the whole package: `cd package && sha256sum -c MANIFEST.sha256`.

## Overview

The collection crawls host lists with `ic fetch` (`src/ic/cli/fetch.py`): for every host it fetches the landing
page, looks for an Impressum page and writes one status row per host. The steps are:

1. **List build**: the seed list `seed_hosts.txt.gz` (6,560,119 hosts) plus later lists (link frontiers, Common
   Crawl, FineWeb-2, HPLT pools, rest lists, Shopify retries). Every list is in the package under `lists/` with a
   `.sha256` file; the build scripts are in `scripts/E<n>/` (table below).
2. **Crawl**: `ic fetch LIST 25000 FIRST LAST [WORKERS] --provider-concurrency 8 --output-dir OUT`, driven per VM
   by `scripts/E16/run.sh`, `scripts/E22/run.sh`, `scripts/E19/run.sh` or `scripts/E43/run*.sh`. Output per batch:
   `fetch_status_batch<N>.tsv`, `imprints_batch<N>.jsonl.gz`, `discovered_external_hosts.txt`.
3. **Compact tables** (E31): `scripts/E31/pull.py` runs `scripts/E31/extract.py` on every crawl dir named in
   `scripts/E31/sources.tsv` and writes one table (host, status, redirect target) per dir plus `manifest.tsv`.
   The package holds the result as `counts/r4/E31_in/` (99 tables).
4. **Recount** (E31, D34 rule): one site per `www.x` / `x` pair; a found host folds into its redirect target if
   that target was crawled. The first source in manifest order wins.
5. **Filter** (E40 round 2): `scripts/E40/scan_all.py` scans the page text of every found host
   (`filter/E40r2/scan/`); `parking_filter.py apply` drops sites whose found hosts are all domain-sale, parking or
   hosting-default pages; `finalize_r2.py` writes the after-filter list.

Current counts (recount r4, filter round 2): 4,020,137 D34 sites, 3,908,045 after the filter. The final count is
recount r5 (after E48; see `docs/decisions/D47-collection-wrap-up.md`).
TODO(lead): put the r5 numbers here when r5 is done.

Step by step without `recount.sh` (same commands, `PKG` = package dir):

```console
python3 scripts/E31/release_count.py --in PKG/counts/r4/E31_in --out out/E31_out
python3 scripts/E40/parking_filter.py apply --in PKG/counts/r4/E31_in \
  --scan $(ls PKG/filter/E40r2/scan/*.scan.tsv | LC_ALL=C sort) \
  --targets PKG/filter/E40r2/targets_classified.tsv --out out/E40r2 [--name-for-sale-flag-only]
python3 scripts/E40/finalize_r2.py --sites out/E31_out/canonical_sites.txt --r1 PKG/counts/r4/E40_out --r2 out/E40r2
```

The scan files must be given in sorted order (a later file wins for a host that is in two files), as in
`filter/E40r2/apply.log`.

## Data package

S3 instance `innkube` (mc alias, https://share.innkube.fim.uni-passau.de), bucket `datasets`, prefix
`imprints/20261109/`. 1,413 files, 21,670,409,443 bytes. Built 2026-11-09 on lorbeer.

| Path | Content |
|---|---|
| `README.md`, `MANIFEST.sha256` | package notes; sha256 of every other file |
| `code/collection-release.bundle` | git bundle of branch `collection-release` |
| `docs/` | `collection_history.md`, `status.md`, `reproduce_collection.md` (this file), `scripts_README.md` (= `scripts/README.md`), `inventory.tsv`, `inventory.md`, `data_layout.md` |
| `counts/r4/E31_in/` | input of the count: `manifest.tsv` + 99 per-dir tables (929 MB) |
| `counts/r4/E31_out/` | `canonical_sites.txt`, `canonical_sites_found_only.txt`, `redirect_cases.tsv`, `release_count.tsv`, `release_stats.tsv` |
| `counts/r4/E40_out/` | parking filter round 1 output (input of `finalize_r2.py --r1`) |
| `counts/r4/` other | `E40_scan_new/`, `compare/` (r3 vs r4), `SHA256SUMS.txt`, `pull.log`, `release_count.tsv`, `sources.tsv` (absolute lorbeer paths) |
| `filter/E40r2/` | `scan/` (99 `*.scan.tsv` + `coverage.tsv`), `targets_classified.tsv`, `apply.log`, `scan_all.log`, outputs (`flagged_sites.tsv`, `filter_by_source.tsv`, `flagged_site_hosts.tsv`, `sample_found_hosts.tsv`, `canonical_sites_after_filter.txt`, `delta_by_*.tsv`, `release_count_after_filter.tsv`), `SHA256SUMS.txt`, evidence (`discovery/`, `labels/`, `r1_check/`, `r1_view.scan.tsv`) |
| `filter/E40r3/` | evidence for the under-construction labels (round 3) |
| `crawls/` | raw crawl output (status tables, `imprints_*.jsonl.gz`): E28 (p1, p2), E30 (`full_lorbeer_batches0-27`, `full_aspe_batches28-54`), E33 (abelie, apfel, aspe, mispel), E33p (q1-q4), E34r2, E34r3, E37 (4 VMs), E39 (audit evidence only), E41 (4 VMs), E43, E44, E45 (A, B), E46, E47 |
| `lists/` | every host list with `.sha256`: `seed_hosts.txt.gz`, `E16/`, `E19/` (round 1 recovery input and reshard, round 2, 2b, 2c, 2d), `frontiers/` (E22 depth-1 A and depth-2 rest, E34 r1-r4), one folder per crawl E25-E47 and E42 |

Not in the package: raw output of E16, E19, E22, E25-E27, E29, E34, E36 (on the crawl VMs only); E48 and the E34r4
pilot (come with r5); `counts/r5/`; the build inputs `E41/e41.duckdb` and the E24 parquets. See "Gaps".

## Per experiment: list, script, code tree

Order = order of sources in the count (`counts/r4/E31_in/manifest.tsv`, `scripts/E31/sources.tsv`). "New sites" =
new D34 sites in r4 (`counts/r4/E31_out/release_count.tsv`). List sha256 = first 8 hex digits, the full value is in
the `.sha256` file next to the list. Tree = commit of the checkout the fetcher ran from (the fetcher code differs
between trees; see "User-Agent and fetcher versions"). Scripts that are not in `scripts/E<n>/` of the source's own
number are in the folder named in the table; all were moved into git by D47 (see `scripts/README.md`).

| Source | New sites | List in package (sha256) | List build | Crawl driver | Tree |
|---|---:|---|---|---|---|
| E16 | 2,631,463 | `lists/E16/seed_hosts_shuffled.txt` (d89354b8), from `lists/seed_hosts.txt.gz` (c6b507d4) | `scripts/E16/shuffle.py` (seed list itself: no script, gap 3) | `scripts/E16/run.sh` (263 batches of 25k) | 69c5c6b; early batches 90a97f1 |
| E19r1 | 8,740 | `lists/E19/round1_recovery_input.txt` (f3ff5258), `round1_reshard/` | `scripts/E19/collect.py`, `reshard.py` | `scripts/E19/run.sh`; `scripts/E19r1/d25_*.sh` | 69c5c6b |
| E19r2 | 37,375 | `lists/E19/round2/` (8b458240), `round2b/`, `round2c/`, `round2d/` | `scripts/E19/collect.py`, `reshard.py`; 2c/2d: `scripts/E19r2/plan_d30.py`, `plan_d31.py` | `scripts/E19/run.sh`; `scripts/E19r2/launch_*.sh`, `deploy_d30.sh`, `deploy_d31.sh` | s0/s1 e22 tree; 2b main/e22; 2c/2d 321db96 |
| E22d1A | 156,638 | `lists/frontiers/E22_round1_frontier_A.txt` (dcd5f325) | `scripts/E22/frontier.py` | `scripts/E22/run.sh`; `scripts/E19r1/e22_start.sh`, `e22all.sh` | 69c5c6b |
| E22d1B | 3,272 | not in package (VM only, 48631fd0) | `scripts/E22/frontier.py --known A` | `scripts/E22/run.sh` | 69c5c6b |
| E22d2P | 14,841 | not in package (VM only, 91e9c10e) | `scripts/E22/frontier.py` | `scripts/E22/run.sh` | 69c5c6b |
| E22d2R | 11,987 | `lists/frontiers/E22_round2_frontier_rest.txt` (e67ee0b9) | `scripts/E22/frontier.py` | `scripts/E22/run.sh`; `scripts/E22d2R/deploy.sh`, `launch_all.sh` | f9da3ad (d29) |
| E25 | 9,775 | `lists/E25/pilot20k.txt` (aa268740) | `scripts/E25/build.py` (+ `scripts/E23/cc_candidates.py`) | `scripts/E22/run.sh` | f9da3ad |
| E26 | 290,897 | `lists/E26/cc43_dach_rest.txt` (5eb0021e) | `scripts/E25/build.py` | `scripts/E26/e26_launch.sh` | f9da3ad |
| E27 | 2,591 | `lists/E27/p1_hostindex.txt` (638f87bc), `p2_fineweb2.txt` (a5139112), `p3_hplt_ia.txt` (e219643c), `pool_p*.txt` | `scripts/E27/build.py` from `scripts/E24/*` | `scripts/E27/e27_run.sh` | f9da3ad |
| E28 | 2,631 | `lists/E28/p1_other_tld.txt` (269e3eaf), `p2_old_dach.txt` (918275b6) | `scripts/E28/build.py` | `scripts/E28/e28_run.sh` | f9da3ad |
| E29 | 184,254 | `lists/E29/e29_rest.txt` (c99935b1) | `scripts/E29/build.py` | `scripts/E29/launch_*.sh` | f9da3ad |
| E30 | 276,785 | `lists/E30/e30_rest.txt` (438aba2c) | `scripts/E30/build.py` | `scripts/E30/launch_lorbeer.sh`, `launch_aspe.sh` | f9da3ad |
| E33p | 1,624 | `lists/E33p/q1_pilot.txt` .. `q4_pilot.txt` (a0fbbef6, a837fcc3, 28ae394b, 02da4152) | `scripts/E33/build.py`, `mkexcl.py`, `mkq3.py`, `q3_load.py`, `hplt_shard.py` | `scripts/E33/e33_run.sh`, `launch.sh` | f9da3ad |
| E33 | 186,395 | `lists/E33/e33_rest.txt` (c57938cd), `pool_q1..4.txt` | `scripts/E33/build_rest.py` | `scripts/E33/launch_e33.sh` + `scripts/E22/run.sh` | b54aaa1 (e35) |
| E34 | 3,893 | `lists/E34/pilot.txt` (7a54f7f1), `e34_rest.txt` (eacfdf43); frontier `lists/frontiers/E34_r1_frontier_new_seeds.txt` (cf9361b7) | `scripts/E34/build.py`, `build_rest.py` | `scripts/E34/e34_run.sh`, `full_run.sh`, `launch_full.sh` | f9da3ad |
| E34r2 | 11,880 | `lists/E34r2/pilot_r2.txt` (2a549e83), `e34r2_rest.txt` (d3956fc8); frontier c2fae09d | `scripts/E34/round2/build_r2.py`, `mk_all.py`, `mk_dach.py` | `scripts/E34/round2/*run.sh`, `launch_*.sh` | b54aaa1 |
| E34r3 | 6,101 | `lists/E34r3/pilot_r3.txt` (066890d1), `e34r3_rest.txt` (2f6935dc); frontier 02810592 | `scripts/E34/round3/build_r3.py` | `scripts/E34/round3/launch_r3.sh`, `launch_full.sh` | 3a23d5d |
| E36 | 261 | `lists/E36/pilot.txt` (9fe5c6ef) | `scripts/E33/mk.py` | `scripts/E33/launch_e36.sh` | b54aaa1 |
| E37 | 23,447 | `lists/E37/e37_rest.txt` (61c54c82) | `scripts/E37/mk.py` | `scripts/E37/launch_e37.sh`, `deploy.sh` | b54aaa1 |
| E41L4 | 6,234 | `lists/E41/L4.txt` (45ad7fc3) | `scripts/E41/build_e41.py` | `scripts/E41/launch.sh`, `run_e41_vm.sh` | 3a23d5d |
| E41L3 | 5,451 | `lists/E41/L3.txt` (11ea8e50) | same | same | 3a23d5d |
| E41L1 | 79,177 | `lists/E41/L1.txt` (0d1760ba) | same | same | 3a23d5d |
| E41L2 | 18,679 | `lists/E41/L2.txt` (e1df2fdd) | same | same | 3a23d5d |
| E43 | 45,449 | `lists/E43/pilot_E43.txt` (6a0b1e77), `rest_E43.txt` (c060acb0), `pool_E43.txt` (ca44cf8e) | `scripts/E43/build_e43e44.py`, `mkfiles.py` | `scripts/E43/run_pilots.sh`, `run_full.sh` | 3a23d5d |
| E44 | 159 | `lists/E44/pilot_E44.txt` (65bc72ad), `rest_E44.txt` (4b045ab9), `pool_E44.txt` (062bb788) | `scripts/E43/build_e43e44.py` | `scripts/E43/run.sh` | 3a23d5d |
| E45 | 52 | `lists/E45/listA.txt` (bd5ce3d6), `listB.txt` (51cd02ba) | `scripts/E45/draw.py` (seed 45) | `scripts/E45/launch.sh` -> `scripts/E19/run.sh` | 3a23d5d |
| E46 | 49 | `lists/E46/list.txt` (7dd6ecc0) | `scripts/E46/draw.py` (seed 46) | `scripts/E46/start.sh`, `launch.sh` | 3a23d5d |
| E47 | 37 | `lists/E47/list.txt` (9707c84f) | `scripts/E47/draw.py` | `scripts/E47/start.sh`, `launch.sh` | 3a23d5d |
| E48 (r5) | r5 | not in package (c75a07f8, 96,722 hosts) | `scripts/E48/draw.py` (seed 48) from `scripts/E42/s1.py`, `s1b.py` | `scripts/E48/start.sh`, `launch.sh` -> `scripts/E19/run.sh` | 3a23d5d |
| E34r4 pilot (r5) | r5 | not in package (64bda38a); frontier `lists/frontiers/E34_r4_frontier_r4.txt` (d18a36f1) | `scripts/E34/round4/build_r4.py` | `scripts/E34/round4/launch_r4.sh`, `go_pilot.sh` | 3a23d5d |
| E42 (not counted) | — | `lists/E42/pilot100.txt` (6e6d1915) | `scripts/E42/s2.py` | `scripts/E42/launch.sh` | 3a23d5d |

Tree commits: 90a97f1 and 69c5c6b = main tree (before and after E20); 321db96 = d30 tree; f9da3ad = d29 tree;
b54aaa1 = e35 tree; 3a23d5d = e41/e43 tree. The VM, batch range and crawl dir of every source are in
`docs/inventory.tsv` (columns `vms`, `vm_crawl_dirs`).

Lists go through `clean-hosts`, the E10 platform filter and the www collapse; each builder removes all hosts of
earlier lists. Most builders read hard-coded paths of the lead machine; these are env-overridable since D47
(`scripts/README.md`, section "Absolute paths").

## User-Agent and fetcher versions

| Era | Sources | User-Agent |
|---|---|---|
| before D39 B | E16, E19r1, E19r2, E22 (all), E25-E30, E33p, E33, E34, E34r2, E36, E37 | older UA string of the tree in the table above |
| after D39 B | E34r3, E41 L1-L4, E43, E44, E45, E46, E47, E48, E34r4 pilot | `Mozilla/5.0 (compatible; ImprintsCollectionBot/1.0; +https://www.fim.uni-passau.de/data-science)` |

Current fetcher (`src/ic/cli/fetch.py`): D39 B User-Agent, E35 recall patch, 10 MB body cap (D30),
`THROTTLE_CODES = (429, 503)` with per-provider cool-down and one retry. A re-crawl with the current tree does not
reproduce the rows of the old-UA crawls; see `docs/collection_history.md` section 5.

## Re-run a crawl from a list

This sends HTTP requests to millions of websites. Run it only from the crawling subnet, with the D39 B
User-Agent, and expect results that differ from ours (see "Not reproducible").

```console
python3 -m venv .venv && .venv/bin/pip install -e . pytest && .venv/bin/pytest
# seed crawl (E16): shuffle with the fixed seed, then 263 batches of 25k, cap 8 per provider network
python3 scripts/E16/shuffle.py           # writes datasets/E16/seed_hosts_shuffled.txt (sha256 d89354b8...)
ROOT=$PWD bash scripts/E16/run.sh 0 262  # resumable; split the batch range over VMs
# any other list (E22, E25-E37, E41)
ROOT=$PWD PY=.venv/bin/python STEP=1 SKIPGROUPS="v4:23.227.38" bash scripts/E22/run.sh LIST OUT_DIR FIRST LAST
# retries and Shopify (E19, E45-E48)
WORKERS=4 PCONC=1 PDELAY=3 BACKOFF=300 RESTARTS=5 bash scripts/E19/run.sh LIST
```

`ic fetch` shuffles the list again with `random.seed(42)` and cuts batches by position, so every VM must hold the
identical list file (check its sha256) and get a disjoint batch range. Then, for a new count: extract with
`scripts/E31/pull.py --out OUT/E31_in --sources scripts/E31/sources.tsv` (remap the absolute paths in
`sources.tsv` first), scan with `scripts/E40/scan_all.py --manifest OUT/E31_in/manifest.tsv --targets
scripts/E40/targets_classified.tsv --out OUT/scan`, and run the quick start steps on these dirs.

r5 (after E48): add E48 and the E34r4 pilot to `sources.tsv` after E47, extract them, rerun count and filter with
`--r5` (`r2_name_for_sale` flag only; about 269 sites stay in).

## Gaps

1. **Raw crawl output of the old sources is not in the package.** E16, E19r1/r2, E22 (all), E25-E27, E29, E34 and
   E36 exist only on the crawl VMs (aspe, apfel, mispel, abelie, lorbeer; E16 about 31 GB). The count is safe:
   `counts/r4/E31_in` holds the compact table of every dir, and `filter/E40r2/scan` the scan result.
   TODO(lead): decide whether the raw data of these old sources is to be copied off the VMs and archived.
2. **akazie and aralie hold the only raw copy** of E19r2 s0/s1/2b/2d and parts of E22d1A/d2R.
3. **The original seed list has no build recipe.** `seed_hosts.txt.gz` (6,560,119 hosts, c6b507d4) comes from the
   paper (Open Web Index, Common Crawl, Curlie).
4. **List builders are not deterministic from the web and need inputs that are not in the package.**
   `scripts/E41/build_e41.py` and `scripts/E43/build_e43e44.py` need `E41/e41.duckdb` (1.1 GB) and the E24
   parquets. E23, E24, E27, E33 read Common Crawl and Hugging Face over the network. Use the lists in `lists/`.
5. **Some launch files were VM-only or lead-tmp-only.** D47 moved 163 of them into git (`scripts/README.md`);
   `~/stage_run.sh` (copy of `scripts/E19/run.sh`) and the per-VM ssh commands of E33/E37/E41 are partly not
   recorded. The E22 depth-1 B and depth-2 priority lists are only on the VMs.
6. **The r4 recount was run by hand.** `scripts/E31/recount.sh` reproduces it from the package (added by D47).
   `counts/r4/sources.tsv` holds absolute lorbeer paths for E33, E34r2, E34r3, E37, E41, E43-E47.
7. **E48 and the E34r4 pilot are not in r4 or in the package; E42 is not counted.**
8. **Corrupt or truncated data.** `crawls/E45/B/datasets/E45/out/imprints_batch000000.jsonl.gz` is truncated
   (`gzip -t` fails; stored as is). 10 E19 dirs have `truncated_gz=1` in `counts/r4/E31_in/manifest.tsv`. Neither
   changes the count.
9. **Environments are not captured.** VM venvs, Python versions and `pip freeze` were not recorded;
   `pyproject.toml` is the only pin.

## Not reproducible

- **Live web.** A re-crawl sees a different web: sites change, expire or move; the yield differs.
- **Rate limits and blocks.** Hosts answer 429/503/403 depending on client IP and rate (Shopify group
  `v4:23.227.38`, 270,624 hosts with 403 in the seed crawl). Our results depend on the seven VM IPs in the
  crawling subnet and the per-provider cap of 8.
- **Fetcher versions.** See "User-Agent and fetcher versions".
- **External list sources.** Hugging Face datasets are read through `resolve/main` with no pinned revision:
  `HuggingFaceFW/fineweb-2`, `HPLT/HPLT2.0_cleaned`, `commoncrawl/host-index-testing-v2` (crawl CC-MAIN-2025-18).
  Common Crawl: `scripts/E23/cc_candidates.py` takes the latest 8 crawls from `collinfo.json` at run time (up to
  CC-MAIN-2026-43); `scripts/E33/q3_load.py` uses CC-MAIN-2024-46, 2024-51, 2025-05, 2025-08, 2025-13.
  TODO(lead): record the Hugging Face dataset revisions (commit hashes) that were current on the build dates, if
  they can still be found.
- **Shuffles.** `ic fetch` uses `random.seed(42)`; `scripts/E16/shuffle.py` uses seed 20261024. Batch contents
  are reproducible only from the identical input file.
