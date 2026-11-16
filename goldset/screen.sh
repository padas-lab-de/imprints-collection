#!/usr/bin/env bash
# Phase-1 screen: run the two screen models over the S1 inputs with the fixed release configurations
# (POI retrieve k30). Runs evaluation/run.py unchanged (prompts unchanged); resumable (append jsonl, done hosts
# skipped). The six runs (3 tasks x 2 models) run in parallel, WORKERS concurrent calls each.
#
#   bash goldset/screen.sh [LIMIT] [WORKERS]       LIMIT 0 = all of inputs.jsonl (default 0), WORKERS default 4
#
# Data folder: $IC_GOLD_DATA (default <repo root>/datasets/goldset). Input: screen/inputs.jsonl (goldset/screen_inputs.py).
# Output: screen/preds/{poi3,wz,address}/<tag>.jsonl, logs in screen/logs/.
# The model endpoint and key come from MODEL_API_ENDPOINT and MODEL_API_KEY (.env at the repo root or the environment).
set -u
cd "$(dirname "$0")/.."   # repository root
LIMIT=${1:-0}
WORKERS=${2:-4}
D=${IC_GOLD_DATA:-$PWD/datasets/goldset}
IN=$D/screen/inputs.jsonl
OUT=$D/screen/preds
CACHE=$D/cache
LOGS=$D/screen/logs
mkdir -p "$OUT" "$CACHE" "$LOGS"
run() {  # name, args...
  local name=$1; shift
  python3 -I evaluation/run.py --dev "$IN" --out-dir "$OUT" --cache "$CACHE" --limit "$LIMIT" \
    --workers "$WORKERS" "$@" >> "$LOGS/$name.log" 2>&1
  echo "$(date -u +%FT%TZ) $name exit $?" >> "$LOGS/$name.log"
}
for m in gemma4-31b-it qwen38-27b; do
  if [ "$m" = gemma4-31b-it ]; then r=short; else r=low; fi   # POI reasoning level per model
  run "poi3_$m" --model "$m" --task topic --schema poi3 --strategy retrieve --reasoning "$r" &
  run "wz_$m" --model "$m" --task topic --schema wz --reasoning none --site-chars 1500 &
  run "address_$m" --model "$m" --task address --reasoning none --mode main --fmt schema &
done
wait
echo "$(date -u +%FT%TZ) all runs finished" >> "$LOGS/driver.log"
