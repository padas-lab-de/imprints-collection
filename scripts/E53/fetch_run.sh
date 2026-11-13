#!/usr/bin/env bash
# E53 step 5: same-day `ic fetch` of the gold items with the release fetcher (collection-release tree,
# D39 B User-Agent, E35 recall patch) and the release settings:
#   pass 1 (as scripts/E22/run.sh, STEP=1): 64 workers, --provider-concurrency 8, Shopify group skipped;
#   pass 2 (as E48, scripts/E19/run.sh at D59 A): the skipped Shopify hosts at WORKERS=4 PCONC=1 PDELAY=5
#   PCOOL=5 BACKOFF=300.
# Run on the crawl VM from the checkout root (ic reads topics/ and prompts/ relative to it):
#   nohup bash scripts/E53/fetch_run.sh datasets/E53/hosts.txt datasets/E53/fetch > datasets/E53/fetch_driver.log 2>&1 &
# Re-running resumes (ic fetch skips hosts with a status row).
set -u
LIST=$1; OUT=$2
ROOT=${ROOT:-$PWD}
PY=${PY:-$ROOT/.venv/bin/python}
SHOPIFY=v4:23.227.38
[ -s "$LIST" ] && [ -n "$OUT" ] || { echo "usage: fetch_run.sh LIST OUT"; exit 1; }
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
