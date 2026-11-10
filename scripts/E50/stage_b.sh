#!/usr/bin/env bash
# E50 stage B: one-factor variants from each model's base reasoning, E49 dev 200, 6 workers.
#   bash scripts/E50/stage_b.sh <model> <poi3 base reasoning> <wz base reasoning>
set -u
model=$1; rp=$2; rw=$3
variants=("--lang en" "--wording minimal" "--wording guide" "--fmt json_object" "--fmt schema" "--shots 4"
          "--site-chars 3000" "--site-chars 1500" "--layout list_first")
for v in "${variants[@]}"; do
  python3 scripts/E50/e50_run.py --task topic --schema poi3 --model "$model" --reasoning "$rp" --workers 6 $v
  python3 scripts/E50/e50_run.py --task topic --schema wz --model "$model" --reasoning "$rw" --workers 6 $v
done
