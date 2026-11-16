#!/usr/bin/env bash
# Download the files that reproduce_final_count.sh needs from the data package, and check their sha256.
#
# Usage: collection/download_release_data.sh [DATA_DIR]
#   DATA_DIR   target dir (default: $IC_DATA_ROOT/collection, or ./data/collection). About 1.1 GB.
# Env:
#   MC               MinIO client binary (default: mc)
#   IC_DATA_PACKAGE  package location as an mc path (default: innkube/datasets/imprints/20261116).
#                    Set up the alias first: mc alias set innkube https://share.innkube.fim.uni-passau.de KEY SECRET
#
# Local layout written (names used by reproduce_final_count.sh):
#   crawl_tables/          one compact table (host, status, redirect target) per crawl dir + manifest.tsv
#   page_scans/            parking / for-sale scan of the home pages, one *.scan.tsv per crawl dir, and
#                          coverage.tsv (one row per scan file, in the order the filter applies them)
#   earlier_filter/        result of the first version of the parking filter (for the comparison tables)
#   redirect_targets.tsv   classified redirect targets (same file as collection/redirect_targets.tsv)
#   expected/              published checksums and the published delta_by_category.tsv
set -euo pipefail

MC=${MC:-mc}
PACKAGE=${IC_DATA_PACKAGE:-innkube/datasets/imprints/20261116}
DATA=${1:-${IC_DATA_ROOT:-./data}/collection}

# Left: local name; right: path in the package.
PACKAGE_PATHS=(
  "crawl_tables/                  count/crawl_tables/"
  "page_scans/                    count/page_scans/"
  "earlier_filter/                count/earlier_filter/"
  "redirect_targets.tsv           count/redirect_targets.tsv"
  "expected/sites.sha256          count/expected/sites.sha256"
  "expected/filter.sha256         count/expected/filter.sha256"
  "expected/delta_by_category.tsv count/filter/delta_by_category.tsv"
)

mkdir -p "$DATA/expected"
DATA=$(cd "$DATA" && pwd)
echo "== download from $PACKAGE to $DATA"
"$MC" cp "$PACKAGE/MANIFEST.sha256" "$DATA/expected/MANIFEST.sha256" >/dev/null

checks="$DATA/expected/download_check.sha256"
: > "$checks"
for entry in "${PACKAGE_PATHS[@]}"; do
  read -r local remote <<<"$entry"
  echo "   $local"
  if [[ $remote == */ ]]; then
    mkdir -p "$DATA/$local"
    "$MC" cp --recursive "$PACKAGE/$remote" "$DATA/$local" >/dev/null
  else
    "$MC" cp "$PACKAGE/$remote" "$DATA/$local" >/dev/null
  fi
  # every package file under this path must be present locally with the sha256 of the package manifest
  awk -v r="$remote" -v l="$local" '
    { p = substr($0, 67) }
    (r ~ /\/$/ && index(p, r) == 1) { print $1 "  " l substr(p, length(r) + 1); n++ }
    (r !~ /\/$/ && p == r)          { print $1 "  " l; n++ }
    END { if (!n) { print "no manifest entry for " r > "/dev/stderr"; exit 1 } }
  ' "$DATA/expected/MANIFEST.sha256" >> "$checks"
done

echo "== check sha256 against the package manifest"
(cd "$DATA" && sha256sum --quiet -c "$checks")
echo "   $(wc -l < "$checks") files OK"

echo "== done: $DATA"
