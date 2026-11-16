#!/usr/bin/env bash
# Same-day `ic fetch` of the gold items with the release fetcher and the release settings (as in
# docs/reproduce_collection.md):
#   pass 1: 64 workers, --provider-concurrency 8, the Shopify IP group skipped;
#   pass 2: the skipped Shopify hosts at 4 workers, --provider-concurrency 1, --provider-delay 5,
#   --provider-cooldown 5, --retry-backoff 300.
# Run on the crawl machine from the repository root (ic reads topics/ and prompts/ relative to it):
#   nohup bash goldset/fetch.sh datasets/goldset/hosts.txt datasets/goldset/fetch > datasets/goldset/fetch_driver.log 2>&1 &
# PY (default .venv/bin/python) is the Python with the package installed. Re-running resumes (ic fetch skips
# hosts with a status row).
set -u
LIST=$1; OUT=$2
ROOT=${ROOT:-$PWD}
PY=${PY:-$ROOT/.venv/bin/python}
SHOPIFY=v4:23.227.38
[ -s "$LIST" ] && [ -n "$OUT" ] || { echo "usage: fetch.sh LIST OUT"; exit 1; }
mkdir -p "$OUT/main" "$OUT/shopify" || exit 1
N=$(wc -l < "$LIST"); LASTB=$(( (N + 24999) / 25000 - 1 ))
echo "$(date -u +%FT%TZ) pass1 start $N hosts"
PYTHONPATH="$ROOT/src" "$PY" -c "from ic.ic import main; main()" fetch \
  "$LIST" 25000 0 "$LASTB" 64 --provider-concurrency 8 --skip-provider-group "$SHOPIFY" \
  --output-dir "$OUT/main" >> "$OUT/fetch_main.log" 2>&1
echo "$(date -u +%FT%TZ) pass1 exit $?"
# hosts of the skipped Shopify group (last row per host wins)
cat "$OUT"/main/fetch_status_batch*.tsv | awk -F'\t' 'NF>=2{s[$1]=$2} END{for(h in s) if(s[h]=="skipped_provider") print h}' \
  | sort > "$OUT/shopify_hosts.txt"
M=$(wc -l < "$OUT/shopify_hosts.txt")
echo "$(date -u +%FT%TZ) pass2 start $M Shopify hosts"
if [ "$M" -gt 0 ]; then
  PYTHONPATH="$ROOT/src" "$PY" -c "from ic.ic import main; main()" fetch \
    "$OUT/shopify_hosts.txt" 25000 0 0 4 --provider-concurrency 1 --provider-delay 5 \
    --provider-cooldown 5 --retry-backoff 300 --output-dir "$OUT/shopify" >> "$OUT/fetch_shopify.log" 2>&1
  echo "$(date -u +%FT%TZ) pass2 exit $?"
fi
echo "$(date -u +%FT%TZ) all done"
