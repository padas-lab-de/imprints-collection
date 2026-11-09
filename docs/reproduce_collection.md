# Reproduce the data collection

State: 2026-11-09 (D47 wrap-up). Skeleton: parts marked TODO(lead) are not yet checked against the
data package or the run scripts outside git.

## Overview

The collection crawls host lists with `ic fetch` (`src/ic/cli/fetch.py`): for every host it fetches the
landing page, looks for an Impressum page and writes one status row per host. The steps are:

1. **List build**: the seed list `seed_hosts.txt.gz` (6,560,119 hosts) plus later lists (link frontiers,
   Common Crawl, FineWeb-2, HPLT pools). Scripts in `scripts/E<n>/`; see the table in
   [`scripts/README.md`](../scripts/README.md).
2. **Crawl**: `ic fetch LIST 25000 FIRST LAST [WORKERS] --provider-concurrency 8 --output-dir OUT`, driven per VM
   by `scripts/E16/run.sh`, `scripts/E22/run.sh` or `scripts/E43/run.sh`. Output per batch:
   `fetch_status_batch<N>.tsv`, `imprints_batch<N>.jsonl.gz`, `discovered_external_hosts.txt`.
3. **Recount** (E31, D34 rule): one site per `www.x` / `x` pair; a found host folds into its redirect target
   if that target was crawled. First source in `scripts/E31/sources.tsv` order wins.
4. **Filter** (E40 round 2): drop sites whose found hosts are all domain-sale, parking or hosting-default pages.

Current counts (recount r4, filter round 2): 4,020,137 D34 sites; 3,908,045 after the filter.
The final count is recount r5 (after E48; see `docs/decisions/D47-collection-wrap-up.md`). TODO(lead): put the r5
numbers here when r5 is done.

Fetcher settings of the release crawls (in `src/ic/cli/fetch.py`): User-Agent
`Mozilla/5.0 (compatible; ImprintsCollectionBot/1.0; +https://www.fim.uni-passau.de/data-science)` (D39 B),
E35 recall patch, 10 MB body cap (D30), `THROTTLE_CODES = (429, 503)` with per-provider cool-down and one retry.
Earlier crawls (E16, E19, E22, E26-E30) ran with older fetcher trees; see
`docs/collection_history.md` section 5.

## Data package

Location: S3 instance `innkube` (mc alias, https://share.innkube.fim.uni-passau.de), bucket `datasets`,
prefix `imprints/20261109/`.

```console
mc ls innkube/datasets/imprints/20261109/
mc cp --recursive innkube/datasets/imprints/20261109/ ./package/
```

TODO(lead): list the package contents and layout when the upload is done. The recount below needs:

- the E31 input dir: `manifest.tsv` plus one `<vm>_<source>_<sub>.tsv` per crawl dir (output of `scripts/E31/pull.py`;
  columns host, status, redirect target host);
- the E40 scan files: one `<stem>.scan.tsv` per crawl dir (output of `scripts/E40/scan_all.py`);
- the reference outputs with sha256 (`canonical_sites.txt`, `canonical_sites_after_filter.txt`, `SHA256SUMS.txt`).

TODO(lead): state whether the raw crawl outputs (`imprints_batch*.jsonl.gz`, status TSVs) are in the package.

## Recompute the count from the package (no crawling)

Needs only Python 3 (stdlib). No network. Memory: about 5 GB (`compare_r3_r4.py` docstring); TODO(lead): measure
for `release_count.py` and `parking_filter.py apply`.

```console
# 1. D34 site count over all sources (manifest order)
python3 scripts/E31/release_count.py --in package/<E31_in> --out out/E31
#    -> out/E31/release_count.tsv, release_stats.tsv, canonical_sites.txt, redirect_cases.tsv

# 2. Parking filter (E40 round 2 patterns are in parking_filter.py)
python3 scripts/E40/parking_filter.py apply --in package/<E31_in> \
    --scan package/<E40_scan>/*.scan.tsv --targets scripts/E40/targets_classified.tsv --out out/E40

# 3. After-filter site list, deltas and SHA256SUMS
python3 scripts/E40/finalize_r2.py --sites out/E31/canonical_sites.txt --r1 <round-1 E40 output> --r2 out/E40

# 4. Compare with the published sha256
sha256sum out/E31/canonical_sites.txt out/E40/canonical_sites_after_filter.txt
```

TODO(lead): fill in the real folder names of the package (`<E31_in>`, `<E40_scan>`, round-1 E40 output) and the
expected sha256 values (r4: D34 site list `e4645f32…`, filtered list `85e12846…`; r5: tbd).
TODO(lead): the r5 rule "r2_name_for_sale flag-only" (D47 answer 4) is not in `parking_filter.py` on this branch;
add the code or the command line that applies it.

## Re-run the crawl from the seed lists

This sends HTTP requests to millions of websites. Run it only from the crawling subnet, with the D39 B User-Agent,
and expect results that differ from ours (see the last section).

```console
python3 -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/pytest
# seed crawl (E16): shuffle with the fixed seed, then 263 batches of 25k, cap 8 per provider network
python3 scripts/E16/shuffle.py           # writes datasets/E16/seed_hosts_shuffled.txt (sha256 d89354b8...)
bash scripts/E16/run.sh 0 262            # resumable; split the batch range over VMs
```

`ic fetch` shuffles the list again with `random.seed(42)` and cuts batches by position, so every VM must hold the
identical list file (check its sha256) and get a disjoint batch range.

Generic driver for any other list (as used by E22, E41):

```console
ROOT=$PWD PY=.venv/bin/python STEP=1 SKIPGROUPS="v4:23.227.38" \
  bash scripts/E22/run.sh LIST OUT_DIR FIRST LAST
```

TODO(lead): the later lists (E19 recovery, E22 frontiers, E23-E30, E33, E34, E37, E41, E43, E44, E48) are in the
data package or must be rebuilt with their scripts; name the list files and their sha256 per experiment.
TODO(lead): the scripts in `scripts/E16/`, `E13/`, `E15/` use `ROOT=/home/dinzinger/GitHub/imprints-collection` and a
fixed venv path; set `ROOT` / `PY` or make them relative.

## Pipeline steps per experiment

Order = order of sources in the count (`scripts/E31/sources.tsv`). Folder `—` = scripts not in git yet.

| ID | Source / role | List build | Crawl launch | In count |
|---|---|---|---|---|
| E16 | Seed list, 6.56M hosts | `scripts/E16/shuffle.py` | `scripts/E16/run.sh` | yes |
| E19 | Recovery passes (second IP) | `scripts/E19/collect.py`, `reshard.py` | `scripts/E19/run.sh` | yes |
| E22 | Outlinks of the seeds, depth 1 and 2 | `scripts/E22/frontier.py` | `scripts/E22/run.sh` | yes |
| E23 | Common Crawl 8-crawl union candidates | `scripts/E23/cc_candidates.py` | via E28, E30 | via E28, E30 |
| E24-E30, E33 | Common Crawl, FineWeb-2, HPLT pilots and full crawls | — TODO(lead) | — TODO(lead) | E25-E30, E33 yes; E24 builds lists only |
| E34 | Outlinks of new-source pages, rounds 1-4 | — TODO(lead) | — TODO(lead) | yes (round 4: pilot only) |
| E35-E37 | Recall patch review, re-check pilot, full re-check | fetcher: `src/ic/cli/fetch.py`; lists — TODO(lead) | — TODO(lead) | E36, E37 yes |
| E41 | Other-TLD parity crawls L1-L4 | `scripts/E41/build_e41.py`, `verify_lists.py` | `scripts/E41/ship.sh`, `launch.sh`, `run_e41_vm.sh` | yes |
| E43, E44 | HPLT rest, FineWeb-2 dialect configs | `scripts/E43/build_e43e44.py` | `scripts/E43/run_pilots.sh`, `run_full.sh` | yes |
| E42, E45-E48 | Shopify re-pilot, rate tests, full crawl | — TODO(lead) | — TODO(lead) | E45-E47 in r4; E48 in r5 |
| E31 | Recount | `scripts/E31/pull.py` (extract on VMs) | — | `scripts/E31/release_count.py` |
| E40 | Filter | `scripts/E40/targets.py`, `scan_all.py` | — | `scripts/E40/parking_filter.py apply`, `finalize_r2.py` |

TODO(lead): check the "In count" column against `scripts/E31/sources.tsv` of recount r5.

## Known non-reproducible parts

- **Live web.** A re-crawl sees a different web: sites change, expire or move; the yield will differ.
- **Rate limits and blocks.** Hosts answer 429/503/403 depending on client IP and rate (Shopify group
  `v4:23.227.38`, 270,624 hosts with 403 in the seed crawl). Our results depend on the seven VM IPs in the
  crawling subnet and the per-provider cap of 8.
- **Fetcher versions.** Early crawls ran with older trees (before the body cap, the recall patch and the D39 B
  User-Agent); one current tree will not reproduce their exact rows.
- **VM-specific paths.** `scripts/E31/sources.tsv` and `pull.py` name VMs (aspe, apfel, mispel, lorbeer, abelie,
  akazie, aralie) and their trees; E41/E43 scripts use `/home/dinzinger/.claude/jobs/cfd8c2d0/tmp`; E13-E16 use
  `/home/dinzinger/GitHub/imprints-collection`. The recount from the package does not need them.
- **External list sources.** Common Crawl indexes, FineWeb-2 and HPLT are read over the network (DuckDB,
  Hugging Face HTTP range requests); their content can change. TODO(lead): record the dataset revisions used.
- **Shuffles.** `ic fetch` uses `random.seed(42)`; `E16/shuffle.py` uses seed 20261024. Batch contents are
  reproducible only from the identical input file.
