#!/usr/bin/env bash
# Recount the release without crawling: E31 release_count -> E40 r2 parking filter apply -> finalize_r2 -> sha256 compare.
#
# Usage: scripts/E31/recount.sh PKG OUT [--r5 | --final]
#   PKG   data package dir (S3 innkube/datasets/imprints/20261109/, see docs/reproduce_collection.md). Reads only:
#           counts/r4/E31_in/ (manifest.tsv + 99 status tables), counts/r4/E40_out/ (round-1 filter result),
#           counts/r4/SHA256SUMS.txt, filter/E40r2/scan/*.scan.tsv, filter/E40r2/targets_classified.tsv,
#           filter/E40r2/SHA256SUMS.txt
#   OUT   output dir (created): OUT/E31_out, OUT/E40r2, OUT/compare.tsv
#   --r5  r2_name_for_sale is flag only (parking_filter.py apply --name-for-sale-flag-only): those sites stay
#         listed in flagged_sites.tsv but are not dropped. The after-filter files then differ from the package (expected).
#   --final  the final count r5: the r5 rule (as --r5) on the r5 data. Reads counts/r5/E31_in (105 tables),
#         counts/r5/E40r2_scan/*.scan.tsv, counts/r4/E40_out, filter/E40r2/targets_classified.tsv, and compares
#         with counts/r5/SHA256SUMS.txt and counts/r5/E40r2/SHA256SUMS.txt.
# Env: PY (default python3; stdlib only). Exit 1 if a file differs from the package sha256 (without --r5).
# Measured on lorbeer (2026-11-09): 7 min 44 s wall time, 5.1 GB peak RSS (parking filter step).
# delta_by_category.tsv: tied transition rows come out in hash-seed order, so its sha256 can differ; the script
# then compares the sorted lines and reports "match (same lines, order of ties differs)".
set -euo pipefail

if [ $# -lt 2 ]; then
  sed -n '2,18p' "$0"
  exit 2
fi
PKG=$(cd "$1" && pwd)
OUT=$2
R5=0
FINAL=0
[ "${3:-}" = "--r5" ] && R5=1
[ "${3:-}" = "--final" ] && R5=1 && FINAL=1
CNT=counts/r4        # input tables and expected E31_out sums
SCAN=filter/E40r2/scan
EXP2=filter/E40r2    # expected after-filter sums and files
if [ $FINAL = 1 ]; then CNT=counts/r5; SCAN=counts/r5/E40r2_scan; EXP2=counts/r5/E40r2; fi
PY=${PY:-python3}
HERE=$(cd "$(dirname "$0")/.." && pwd)  # scripts/

for p in $CNT/E31_in/manifest.tsv counts/r4/E40_out/flagged_sites.tsv $CNT/SHA256SUMS.txt \
  filter/E40r2/targets_classified.tsv $EXP2/SHA256SUMS.txt; do
  [ -e "$PKG/$p" ] || { echo "missing $PKG/$p" >&2; exit 2; }
done
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

echo "== 1/3 release_count (E31, D34 rule)"
"$PY" "$HERE/E31/release_count.py" --in "$PKG/$CNT/E31_in" --out "$OUT/E31_out"

echo "== 2/3 parking filter apply (E40 r2$([ $R5 = 1 ] && echo ', name_for_sale flag only'))"
# scan files in sorted order, as in filter/E40r2/apply.log (a later file wins for a host seen twice)
mapfile -t SCANS < <(ls "$PKG"/$SCAN/*.scan.tsv | LC_ALL=C sort)
EXTRA=()
[ $R5 = 1 ] && EXTRA=(--name-for-sale-flag-only)
"$PY" "$HERE/E40/parking_filter.py" apply --in "$PKG/$CNT/E31_in" --scan "${SCANS[@]}" \
  --targets "$PKG/filter/E40r2/targets_classified.tsv" --out "$OUT/E40r2" "${EXTRA[@]}"

echo "== 3/3 finalize (after-filter list, deltas vs round 1)"
"$PY" "$HERE/E40/finalize_r2.py" --sites "$OUT/E31_out/canonical_sites.txt" --r1 "$PKG/counts/r4/E40_out" \
  --r2 "$OUT/E40r2" > "$OUT/E40r2/finalize.log"

echo "== compare sha256 with the package"
# expected: counts/r4/SHA256SUMS.txt lists E31_out/<file>; filter/E40r2/SHA256SUMS.txt lists <file>
bad=0
{
  printf 'file\texpected\tgot\tresult\n'
  while read -r sum f; do
    case $f in E31_out/*) ;; *) continue ;; esac
    [ -e "$OUT/$f" ] || continue
    got=$(sha256sum "$OUT/$f" | cut -d' ' -f1)
    if [ "$got" = "$sum" ]; then r=match; else r=DIFFERS; bad=1; fi
    printf '%s\t%s\t%s\t%s\n' "$f" "$sum" "$got" "$r"
  done < "$PKG/$CNT/SHA256SUMS.txt"
  while read -r sum f; do
    [ -e "$OUT/E40r2/$f" ] || continue
    got=$(sha256sum "$OUT/E40r2/$f" | cut -d' ' -f1)
    pkgf="$PKG/$EXP2/$f"
    if [ "$got" = "$sum" ]; then r=match
    elif { [ $R5 = 0 ] || [ $FINAL = 1 ]; } && [ -e "$pkgf" ] && [ "$(sha256sum < "$pkgf" | cut -d' ' -f1)" = "$sum" ] \
      && cmp -s <(LC_ALL=C sort "$pkgf") <(LC_ALL=C sort "$OUT/E40r2/$f"); then
      # finalize_r2.py writes tied transition counts in set order (depends on the Python hash seed)
      r="match (same lines, order of ties differs)"
    elif [ $R5 = 1 ] && [ $FINAL = 0 ]; then r="differs (expected, --r5)"
    else r=DIFFERS; bad=1; fi
    printf 'E40r2/%s\t%s\t%s\t%s\n' "$f" "$sum" "$got" "$r"
  done < "$PKG/$EXP2/SHA256SUMS.txt"
} > "$OUT/compare.tsv"
cut -f1,4 "$OUT/compare.tsv" | column -t -s $'\t'
echo "canonical_sites.txt              $(wc -l < "$OUT/E31_out/canonical_sites.txt") sites (D34)"
echo "canonical_sites_after_filter.txt $(wc -l < "$OUT/E40r2/canonical_sites_after_filter.txt") sites (after sale+park+host filter)"
exit $bad
