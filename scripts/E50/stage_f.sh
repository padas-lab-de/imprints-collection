#!/usr/bin/env bash
# E50 stage F: the frozen configs of results/E50/final_config.md on held-out 300, once, one model per call:
#   bash scripts/E50/stage_f.sh <model> <POI reasoning>
set -u
model=$1
poi_r=$2
run="python3 -I scripts/E50/e50_run.py --dev datasets/E50/heldout300_inputs.jsonl --allow-heldout --out-dir results/E50/preds/heldout300 --model $model --workers 6"
$run --task topic --schema poi3 --reasoning "$poi_r"
$run --task topic --schema wz --reasoning none --site-chars 1500
$run --task address --reasoning none --mode main --fmt schema
echo "stage_f done $model"
