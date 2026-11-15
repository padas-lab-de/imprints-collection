#!/usr/bin/env bash
# Candidate-model runs on the gold inputs (configurations: docs/model_eval_protocol.md, section "Candidates").
#
#   bash evaluation/run_candidates.sh <stage> <lane> [<lane> ...]
#     stage  pilot (hosts in $EVAL/pilot_hosts.txt) | full (all items of $EVAL/gold_inputs.jsonl)
#            | topup (all items of $EVAL/topup_inputs.jsonl, the gold-set top-up; output preds/topup)
#     lane   comma list of <model>:<run>, run = address | poi_k30 | poi_flat | wz; runs of one lane go one after
#            the other, lanes run at the same time (at most 2 lanes).
#   EVAL=datasets/evaluation (default). Run from the repository root. The model endpoint and key come from
#   MODEL_API_ENDPOINT and MODEL_API_KEY (.env at the repository root or the environment).
# Each run: 6 workers, resumable (run.py skips hosts already in the output), log <EVAL>/logs/<stage>/<model>_<run>.log,
# HTTP error log <EVAL>/logs/<stage>/<model>_<run>.http.log, the exact command in <EVAL>/logs/<stage>/commands.txt.
set -u
EVAL=${EVAL:-datasets/evaluation}
stage=$1
shift
[ "$#" -le 2 ] || { echo "at most 2 lanes" >&2; exit 2; }
inputs=$EVAL/gold_inputs.jsonl
case $stage in
  pilot) sel=(--hosts "$EVAL/pilot_hosts.txt") ;;
  full) sel=() ;;
  topup) sel=(); inputs=$EVAL/topup_inputs.jsonl ;;
  *) echo "stage: pilot | full | topup" >&2; exit 2 ;;
esac
out=$EVAL/preds/$stage
logs=$EVAL/logs/$stage
mkdir -p "$out" "$logs"

poi_r() {  # POI reasoning level per model
  case $1 in
    gemma4-31b-it) echo short ;;
    qwen38-27b) echo low ;;
    qwen-agentworld-35b-a3b) echo short ;;
    soofi-s-isar-preview) echo low ;;
    *) echo "no POI reasoning level for $1" >&2; return 1 ;;
  esac
}

run_args() {
  local m=$1 r=$2
  case $r in
    address) echo "--task address --reasoning none --mode main --fmt schema" ;;
    poi_k30) echo "--task topic --schema poi3 --strategy retrieve --k 30 --reasoning $(poi_r "$m")" ;;
    poi_flat) echo "--task topic --schema poi3 --strategy flat --reasoning $(poi_r "$m")" ;;
    wz) echo "--task topic --schema wz --reasoning none --site-chars 1500" ;;
    *) echo "unknown run $r" >&2; return 1 ;;
  esac
}

lane() {
  local item m r args cmd rc
  for item in ${1//,/ }; do
    m=${item%%:*}
    r=${item#*:}
    args=$(run_args "$m" "$r") || continue
    cmd="python3 -I evaluation/run_logged.py --http-log $logs/${m}_$r.http.log -- \
--dev $inputs ${sel[*]} --out-dir $out --cache $EVAL/cache --model $m --workers 6 $args"
    echo "$(date -u +%FT%TZ) $cmd" >> "$logs/commands.txt"
    $cmd >> "$logs/${m}_$r.log" 2>&1
    rc=$?
    echo "$(date -u +%FT%TZ) exit $rc $m $r" >> "$logs/commands.txt"
  done
}

for l in "$@"; do
  lane "$l" &
done
wait
