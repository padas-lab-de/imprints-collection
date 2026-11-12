#!/usr/bin/env bash
# E53 step 3b: phase-1 screen with the fixed E50 configs (results/E50/final_config.md, POI default retrieve k30),
# two models, innkube only. Runs scripts/E50/e50_run.py unchanged (prompts unchanged); resumable (append jsonl,
# done hosts skipped). The six runs (3 tasks x 2 models) run in parallel, WORKERS concurrent calls each.
#
#   bash scripts/E53/screen_run.sh [LIMIT] [WORKERS]       LIMIT 0 = all of inputs.jsonl (default 0), WORKERS default 4
#
# Output: datasets/E53/screen/preds/{poi3,wz,address}/<tag>.jsonl, logs in datasets/E53/screen/logs/.
# Runs from the root of the tree that holds this script (the full run used the copy datasets/E53/runtime/).
set -u
cd "$(dirname "$0")/../.."   # repository root (or the runtime copy datasets/E53/runtime)
LIMIT=${1:-0}
WORKERS=${2:-4}
D=/home/dinzinger/GitLab/fim/imprints-collection/datasets/E53
IN=$D/screen/inputs.jsonl
OUT=$D/screen/preds
CACHE=$D/cache
LOGS=$D/screen/logs
mkdir -p "$OUT" "$CACHE" "$LOGS"
run() {  # name, args...
  local name=$1; shift
  python3 -I scripts/E50/e50_run.py --dev "$IN" --out-dir "$OUT" --cache "$CACHE" --limit "$LIMIT" \
    --workers "$WORKERS" "$@" >> "$LOGS/$name.log" 2>&1
  echo "$(date -u +%FT%TZ) $name exit $?" >> "$LOGS/$name.log"
}
for m in gemma4-31b-it qwen38-27b; do
  if [ "$m" = gemma4-31b-it ]; then r=short; else r=low; fi   # POI reasoning per final_config.md
  run "poi3_$m" --model "$m" --task topic --schema poi3 --strategy retrieve --reasoning "$r" &
  run "wz_$m" --model "$m" --task topic --schema wz --reasoning none --site-chars 1500 &
  run "address_$m" --model "$m" --task address --reasoning none --mode main --fmt schema &
done
wait
echo "$(date -u +%FT%TZ) all runs finished" >> "$LOGS/driver.log"
