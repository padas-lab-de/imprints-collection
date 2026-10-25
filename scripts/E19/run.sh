#!/usr/bin/env bash
# E19 recovery pass: retry the retryable E16 failures (403/429/503/timeout/conn/refused + the 48 Strato
# gold hosts) from a SECOND IP at a low rate. Re-running resumes (status log per batch, see ic fetch).
# Usage: run.sh [list]    list defaults to $DATA/datasets/E19/recovery_all.txt (from scripts/E19/collect.py,
#                         run on the VM that holds the E16 status files; copy the list to the second VM)
# Variables (all optional): ROOT repo checkout, DATA dir holding datasets/ and results/ (default ROOT),
#   PY python with ic installed, OUT output dir, WORKERS (16; E16 uses 64), PCONC (2; E16 8),
#   PDELAY (2.0 s between requests per provider /24; default 0.25), PCOOL (60 s pause after 429/503),
#   BACKOFF (300 s before the single re-fetch of a 429/503 host), BATCH (25000 hosts per batch).
# Frozen input: the list is copied to $OUT/recovery_input.txt on the first run and reused afterwards, because
# ic fetch shuffles the list and resumes by position in it; a changed list would shift the batches.
ROOT=${ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
DATA=${DATA:-$ROOT}
PY=${PY:-python3}
OUT=${OUT:-$DATA/datasets/E19/recovery}
WORKERS=${WORKERS:-16}; PCONC=${PCONC:-2}; PDELAY=${PDELAY:-2.0}
PCOOL=${PCOOL:-60}; BACKOFF=${BACKOFF:-300}; BATCH=${BATCH:-25000}
LIST=${1:-$DATA/datasets/E19/recovery_all.txt}
mkdir -p "$OUT" "$DATA/results/E19/logs" || exit 1
[ -s "$OUT/recovery_input.txt" ] || cp "$LIST" "$OUT/recovery_input.txt" || exit 1
cd "$ROOT" || exit 1   # ic reads topics/ and prompts/ relative to the repo root
echo "$(date -u +%FT%TZ) recovery start: $(wc -l < "$OUT/recovery_input.txt") hosts, workers $WORKERS, provider conc $PCONC delay ${PDELAY}s"
PYTHONPATH="$ROOT/src" "$PY" -c "from ic.ic import main; main()" fetch \
  "$OUT/recovery_input.txt" "$BATCH" 0 -1 "$WORKERS" \
  --provider-concurrency "$PCONC" --provider-delay "$PDELAY" \
  --provider-cooldown "$PCOOL" --retry-backoff "$BACKOFF" \
  --output-dir "$OUT" >> "$DATA/results/E19/logs/fetch_recovery.log" 2>&1
echo "$(date -u +%FT%TZ) recovery exit $?"
