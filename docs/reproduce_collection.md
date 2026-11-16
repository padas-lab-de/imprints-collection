# Reproduce the site count

The 2026 snapshot of the German Imprints Dataset has **3,945,356** canonical sites with an imprint.
This page shows how to compute this number again from the published data package.

## What is counted

1. Every crawl dir of `ic fetch` is reduced to a crawl table: one row per host with the fetch status
   and the host of the landing URL after redirects.
2. `count_sites.py` merges all crawl tables. A host counts if its last row in a crawl says
   `imprint_found`. `www.` is removed. A host that redirects to another crawled host counts as that
   host. Result: `canonical_sites.txt`, 4,057,186 sites.
3. `filter_parking_domains.py` flags home pages of parked domains, domains for sale and hoster
   default pages (text rules on the home page, plus redirects to known parking and sale services in
   `redirect_targets.tsv`).
4. `write_final_site_list.py` removes the flagged sites. Result: `canonical_sites_after_filter.txt`,
   3,945,356 sites.

## Requirements

- Linux or macOS with bash, Python 3.10 or later (standard library only), `sha256sum`.
- About 6 GB RAM and 3 GB of free disk space.
- The MinIO client [`mc`](https://min.io/docs/minio/linux/reference/minio-mc.html) and a read key for
  the data package (ask the maintainers).

No crawling and no LLM is needed.

## Steps

1. Set up access to the storage (replace `KEY` and `SECRET` with your read key):

   ```console
   mc alias set innkube https://share.innkube.fim.uni-passau.de KEY SECRET
   ```

2. Download the inputs (about 1.1 GB) and check their sha256 against the package manifest:

   ```console
   collection/download_release_data.sh data/collection
   ```

   Expected last lines: `218 files OK` and `== done: ...`. Set `MC` if `mc` is not on your `PATH`, and
   `IC_DATA_PACKAGE` if the package is at another location.

3. Compute the count:

   ```console
   collection/reproduce_final_count.sh data/collection out
   ```

   This takes about 10 minutes. Lines that start with `note:` on stderr are expected.

4. Check the result. The script ends with:

   ```text
   canonical sites before the filter: 4057186
   canonical sites after the filter:  3945356
   sha256 of the final list:          93bd4d30dcc4d290a63953d5df98b2e64d8e0bef413a68653ed1b58d3cf0c461
   ```

   `out/compare.tsv` lists every output file with the published and the computed sha256. All rows must
   say `match`. Rows of `delta_by_category.tsv` with equal counts can be written in a different order
   (this depends on the Python hash seed); the script then compares the sorted lines and reports
   `match (same lines, order of ties differs)`. The exit code is 0 if all files match.

## Outputs

`out/sites/` (from `count_sites.py`):

- `canonical_sites.txt`: canonical sites before the filter, sorted
- `canonical_sites_found_only.txt`: variant in which a host follows its redirect only if the target
  also has an imprint
- `release_count.tsv`, `release_stats.tsv`: counts per crawl source
- `redirect_cases.tsv`: hosts that fold into another host

`out/filter/` (from `filter_parking_domains.py apply` and `write_final_site_list.py`):

- `canonical_sites_after_filter.txt`: the final site list, sorted
- `flagged_sites.tsv`, `flagged_site_hosts.tsv`: flagged sites with category and rule
- `filter_by_source.tsv`, `release_count_after_filter.tsv`: counts per crawl source after the filter
- `delta_by_category.tsv`, `delta_by_source.tsv`: comparison with the first version of the filter
- `sample_found_hosts.tsv`: fixed random sample of hosts with the page text, for manual precision checks
- `SHA256SUMS.txt`

In the comparison files, `first_version` is the first version of the filter and `final` the version
that gives the published count. Rule labels that start with `added_` belong to the rules added in the
final version.

The filter reads the page scans in the row order of `page_scans/coverage.tsv`. When a host appears in
two scan files, the later file wins, so this order is part of the published result.

## Build the inputs from your own crawl

The data package already contains the crawl tables and page scans. To build them from your own
`ic fetch` output dirs:

1. List the crawl dirs in a sources table with the columns `source` and `dir`
   (see `collection/crawl_sources.example.tsv`). The row order is the order in which the sources are
   counted.

2. Build the crawl tables:

   ```console
   collection/build_crawl_tables.py --sources sources.tsv --crawl-root CRAWLS --out data/mine/crawl_tables
   ```

3. Scan the home pages:

   ```console
   collection/scan_crawl_pages.py --manifest data/mine/crawl_tables/manifest.tsv --crawl-root CRAWLS \
     --targets collection/redirect_targets.tsv --out data/mine/page_scans
   ```

4. Run the count and the filter with the same commands as in `reproduce_final_count.sh`:

   ```console
   collection/count_sites.py --in data/mine/crawl_tables --out out/sites
   collection/filter_parking_domains.py apply --in data/mine/crawl_tables \
     --scan data/mine/page_scans/*.scan.tsv --targets collection/redirect_targets.tsv \
     --out out/filter --name-for-sale-flag-only
   collection/write_final_site_list.py --sites out/sites/canonical_sites.txt --filter out/filter
   ```

   Without `--earlier`, the comparison tables compare with an empty earlier result.
