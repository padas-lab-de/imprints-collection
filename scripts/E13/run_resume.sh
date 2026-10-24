#!/usr/bin/env bash
# E13 resume test: 3k extra seeds, 2 batches of 1500. Started, killed with kill -9 mid-batch, restarted with the same command.
ROOT=/home/dinzinger/GitHub/imprints-collection
WT="$(cd "$(dirname "$0")/../.." && pwd)"
PY=${PY:-$ROOT/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
cd "$WT" || exit 1
PYTHONPATH="$WT/src" exec "$PY" -c "from ic.ic import main; main()" fetch \
  "$ROOT/datasets/E13/resume3k_seed_hosts.txt" 1500 \
  --output-dir "$ROOT/datasets/E13/resume_test" --progress-interval 30 "$@"
