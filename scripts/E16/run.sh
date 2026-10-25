#!/usr/bin/env bash
# E16 snapshot crawl of the full seed list: 25k batches, cap 8 per provider network (D18 via E15),
# one process per range of STEP batches (default 3; memory grows ~2.5 GB per batch in one process, seen 2026-10-25). Re-running resumes.
# Usage: run.sh [first_batch] [last_batch]   (inclusive; default all 263 batches)
ROOT=/home/dinzinger/GitHub/imprints-collection
PY=${PY:-$ROOT/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
FIRST=${1:-0}; LAST=${2:-262}; STEP=${STEP:-3}
cd "$ROOT" || exit 1
for ((s = FIRST; s <= LAST; s += STEP)); do
  e=$((s + STEP - 1)); ((e > LAST)) && e=$LAST
  echo "$(date -u +%FT%TZ) range $s-$e start"
  PYTHONPATH="$ROOT/src" "$PY" -c "from ic.ic import main; main()" fetch \
    "$ROOT/datasets/E16/seed_hosts_shuffled.txt" 25000 "$s" "$e" \
    --provider-concurrency 8 --output-dir "$ROOT/datasets/E16/seeds" \
    >> "$ROOT/results/E16/logs/fetch_$s-$e.log" 2>&1
  echo "$(date -u +%FT%TZ) range $s-$e exit $?"
done
echo "$(date -u +%FT%TZ) all done"
