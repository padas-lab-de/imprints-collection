#!/usr/bin/env bash
# E15: E13 fetcher with 8 concurrent requests per provider network on 25k random seeds (D18 C).
# Re-running the same command resumes (finished hosts are skipped).
ROOT=/home/dinzinger/GitHub/imprints-collection
PY=${PY:-$ROOT/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
cd "$ROOT" || exit 1
PYTHONPATH="$ROOT/src" exec "$PY" -c "from ic.ic import main; main()" fetch \
  "$ROOT/datasets/E15/random25k_seed_hosts.txt" 25000 \
  --provider-concurrency 8 --output-dir "$ROOT/datasets/E15/random25k" "$@"
