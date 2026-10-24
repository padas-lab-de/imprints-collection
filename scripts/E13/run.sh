#!/usr/bin/env bash
# E13 dry run: E9 fetcher with per-provider limits on 100k random seeds, 4 batches of 25k.
# Re-running the same command resumes (finished batches/hosts are skipped).
ROOT=/home/dinzinger/GitHub/imprints-collection
WT="$(cd "$(dirname "$0")/../.." && pwd)"
PY=${PY:-$ROOT/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
cd "$WT" || exit 1
PYTHONPATH="$WT/src" exec "$PY" -c "from ic.ic import main; main()" fetch \
  "$ROOT/datasets/E13/random100k_seed_hosts.txt" 25000 \
  --output-dir "$ROOT/datasets/E13/random100k" "$@"
