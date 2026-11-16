#!/usr/bin/env bash
# Reproduce the final site count of the German Imprints Dataset from the downloaded crawl tables.
# No crawling. Steps: count sites -> apply the parking filter -> write the final list -> compare checksums.
#
# Usage: collection/reproduce_final_count.sh DATA_DIR OUT_DIR
#   DATA_DIR  dir written by collection/download_release_data.sh
#   OUT_DIR   output dir (created): OUT_DIR/sites, OUT_DIR/filter, OUT_DIR/compare.tsv
# Env: PY (default python3; standard library only).
# Needs about 6 GB RAM and 8 minutes. Exit code 1 if an output differs from the published checksums.
#
# Expected: OUT_DIR/filter/canonical_sites_after_filter.txt with 3,945,356 lines and sha256
# 93bd4d30dcc4d290a63953d5df98b2e64d8e0bef413a68653ed1b58d3cf0c461.
set -euo pipefail

if [ $# -ne 2 ]; then
  sed -n '2,12p' "$0"
  exit 2
fi
DATA=$(cd "$1" && pwd)
OUT=$2
PY=${PY:-python3}
HERE=$(cd "$(dirname "$0")" && pwd)

for p in crawl_tables/manifest.tsv page_scans/coverage.tsv earlier_filter/flagged_sites.tsv redirect_targets.tsv \
  expected/sites.sha256 expected/filter.sha256 expected/delta_by_category.tsv; do
  [ -e "$DATA/$p" ] || { echo "missing $DATA/$p (run collection/download_release_data.sh first)" >&2; exit 2; }
done
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

echo "== 1/3 count sites"
"$PY" "$HERE/count_sites.py" --in "$DATA/crawl_tables" --out "$OUT/sites" > "$OUT/sites.log"

echo "== 2/3 apply the parking filter"
# scan files in the row order of coverage.tsv: a later file wins for a host that is in two files
mapfile -t SCANS < <(tail -n +2 "$DATA/page_scans/coverage.tsv" | cut -f3 | sed "s|\.tsv\$|.scan.tsv|; s|^|$DATA/page_scans/|")
"$PY" "$HERE/filter_parking_domains.py" apply --in "$DATA/crawl_tables" --scan "${SCANS[@]}" \
  --targets "$DATA/redirect_targets.tsv" --out "$OUT/filter" --name-for-sale-flag-only

echo "== 3/3 write the final site list"
"$PY" "$HERE/write_final_site_list.py" --sites "$OUT/sites/canonical_sites.txt" --filter "$OUT/filter" \
  --earlier "$DATA/earlier_filter" > "$OUT/filter/finalize.log"

echo "== compare sha256 with the published values"
bad=0
compare() {  # $1 = sums file, $2 = output dir, $3 = label prefix
  while read -r sum f; do
    [ -e "$2/$f" ] || continue
    got=$(sha256sum "$2/$f" | cut -d' ' -f1)
    if [ "$got" = "$sum" ]; then r=match
    elif [ "$f" = delta_by_category.tsv ] \
      && cmp -s <(LC_ALL=C sort "$DATA/expected/$f") <(LC_ALL=C sort "$2/$f"); then
      # rows with equal counts are written in set order, which depends on the Python hash seed
      r="match (same lines, order of ties differs)"
    else r=DIFFERS; bad=1; fi
    printf '%s%s\t%s\t%s\t%s\n' "$3" "$f" "$sum" "$got" "$r"
  done < "$1"
}
{
  printf 'file\texpected\tgot\tresult\n'
  compare "$DATA/expected/sites.sha256" "$OUT/sites" "sites/"
  compare "$DATA/expected/filter.sha256" "$OUT/filter" "filter/"
} > "$OUT/compare.tsv"
cut -f1,4 "$OUT/compare.tsv" | column -t -s $'\t'
echo "canonical sites before the filter: $(wc -l < "$OUT/sites/canonical_sites.txt")"
echo "canonical sites after the filter:  $(wc -l < "$OUT/filter/canonical_sites_after_filter.txt")"
echo "sha256 of the final list:          $(sha256sum "$OUT/filter/canonical_sites_after_filter.txt" | cut -d' ' -f1)"
exit $bad
