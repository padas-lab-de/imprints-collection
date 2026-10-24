#!/bin/bash
# E14: fetch one round with the current fetcher at low concurrency (8 workers, batches of 2,500).
# Usage: PY=<python with ic deps> bash scripts/E14/run_fetch.sh ROUND   (ROUND = round2 | round3)
# The fetcher writes to ./datasets, so run it from a scratch dir whose datasets/ points to the round dir.
set -e
W=$(cd "$(dirname "$0")/../.." && pwd)
D=/home/dinzinger/GitHub/imprints-collection
ROUND=$1
RUN=${RUN_BASE:-/tmp}/E14-run-$ROUND
rm -rf "$RUN"; mkdir -p "$RUN" "$D/results/logs"
ln -s "$W/topics" "$RUN/topics"; ln -s "$W/prompts" "$RUN/prompts"; ln -s "$W/geojson" "$RUN/geojson"
ln -s "$D/datasets/E14/$ROUND" "$RUN/datasets"
cd "$RUN"
export PYTHONPATH=$W/src
${PY:-python} -c "from ic.ic import main; main()" fetch "$D/datasets/E14/$ROUND/fetch_hosts.txt" 2500 0 999 8 > "$D/results/logs/E14-fetch-$ROUND.log" 2>&1
