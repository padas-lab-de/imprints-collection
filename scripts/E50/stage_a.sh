#!/usr/bin/env bash
# E50 stage A: reasoning screen on the E49 dev 200, both topic schemas. One queue per model (runs one after another),
# the three queues in parallel, 6 workers each. Run from the repository root (worktree root).
#   bash scripts/E50/stage_a.sh qwen38-27b "none short low medium default"
set -u
model=$1; levels=$2
for r in $levels; do
  for s in poi3 wz; do
    python3 scripts/E50/e50_run.py --task topic --schema "$s" --model "$model" --reasoning "$r" --workers 6
  done
done
