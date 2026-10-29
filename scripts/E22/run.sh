#!/usr/bin/env bash
# E22 depth-1 link-expansion crawl of a frontier list (D19: depth 3, all TLDs; this is depth 1).
# Same fetch settings as E16: 25k batches, cap 8 per provider network, one process per range of
# STEP batches (memory grows within a process, E20). Re-running resumes.
# Usage: run.sh LIST OUT FIRST LAST   (batches inclusive; every VM must hold the identical LIST, check sha256,
#                                      because ic fetch shuffles the list and cuts batches by position)
# Variables (optional): ROOT repo checkout (default: this script's repo), PY python with ic deps
#   (default $ROOT/.venv/bin/python), STEP batches per process (3; 1 on VMs with little free RAM).
ROOT=${ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
PY=${PY:-$ROOT/.venv/bin/python}
LIST=$1; OUT=$2; FIRST=$3; LAST=$4; STEP=${STEP:-3}
[ -s "$LIST" ] && [ -n "$OUT" ] && [ -n "$FIRST" ] && [ -n "$LAST" ] || { echo "usage: run.sh LIST OUT FIRST LAST"; exit 1; }
LOGS=$ROOT/results/E22/logs
mkdir -p "$OUT" "$LOGS" || exit 1
cd "$ROOT" || exit 1   # ic reads topics/ and prompts/ relative to the repo root
for ((s = FIRST; s <= LAST; s += STEP)); do
  e=$((s + STEP - 1)); ((e > LAST)) && e=$LAST
  echo "$(date -u +%FT%TZ) range $s-$e start"
  PYTHONPATH="$ROOT/src" "$PY" -c "from ic.ic import main; main()" fetch \
    "$LIST" 25000 "$s" "$e" \
    --provider-concurrency 8 --output-dir "$OUT" \
    >> "$LOGS/fetch_$s-$e.log" 2>&1
  echo "$(date -u +%FT%TZ) range $s-$e exit $?"
done
echo "$(date -u +%FT%TZ) all done"
