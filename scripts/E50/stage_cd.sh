#!/usr/bin/env bash
# E50 phase 2, stages C and D on dev 500 (E49 dev 200 + E51 dev2 300), one model per call:
#   bash scripts/E50/stage_cd.sh <model> <POI base reasoning> "<extra address reasoning levels>"
# Topic bases and phase-1 candidates, address factors (stage C), call layout (stage D).
set -u
model=$1
poi_r=$2
addr_levels=${3:-short}
run="python3 -I scripts/E50/e50_run.py --dev datasets/E50/dev500_inputs.jsonl --out-dir results/E50/preds/dev500 --model $model --workers 6"
# topic bases (E49 part from the disk cache)
$run --task topic --schema poi3 --reasoning "$poi_r"
$run --task topic --schema wz --reasoning none
# stage C: address factors (base: mode list, fmt free, r-none, imprint input, 6000 chars)
$run --task address --reasoning none
$run --task address --reasoning none --mode main
$run --task address --reasoning none --fmt schema
$run --task address --reasoning none --site-chars 3000
for r in $addr_levels; do
  $run --task address --reasoning "$r"
done
# stage D: call layout
$run --task topic --schema poi3 --reasoning "$poi_r" --layout list_first_q
$run --task topic --schema poi3 --reasoning "$poi_r" --strategy retrieve
$run --task joint --parts poi,wz --reasoning "$poi_r"
$run --task joint --parts poi,wz,address --reasoning "$poi_r"
# phase-1 cost option for WZ
$run --task topic --schema wz --reasoning none --site-chars 1500
echo "stage_cd done $model"
