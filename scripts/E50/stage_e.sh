#!/usr/bin/env bash
# E50 phase 2, stage E on dev 500: combined winners and phase-1 candidates, one model per call:
#   bash scripts/E50/stage_e.sh <model> "<extra e50_run args per line, separated by ;>"
# Example: bash scripts/E50/stage_e.sh qwen38-27b "--task topic --schema poi3 --reasoning low"
set -u
model=$1
run="python3 -I scripts/E50/e50_run.py --dev datasets/E50/dev500_inputs.jsonl --out-dir results/E50/preds/dev500 --model $model --workers 6"
IFS=';' read -ra jobs <<< "$2"
for j in "${jobs[@]}"; do
  $run $j
done
echo "stage_e done $model"
