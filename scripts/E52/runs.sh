#!/usr/bin/env bash
# E52 steps 3-4: candidate x run predictions on the gold inputs (innkube; configs of results/E50/final_config.md).
#
#   bash scripts/E52/runs.sh <stage> <lane> [<lane> ...]
#     stage  pilot (hosts in $E52/pilot_hosts.txt) | full (all items of $E52/gold_inputs.jsonl)
#            | topup (all items of $E52/topup_inputs.jsonl, the E53 r5 top-up; output preds/topup)
#     lane   comma list of <model>:<run>, run = address | poi_k30 | poi_flat | wz; runs of one lane go one after
#            the other, lanes run at the same time (at most 2 lanes).
#   E52=datasets/E52 (default). Run from the repository root.
# Each run: 6 workers, resumable (e50_run.py skips hosts already in the output), log <E52>/logs/<stage>/<model>_<run>.log,
# HTTP error log <E52>/logs/<stage>/<model>_<run>.http.log, the exact command in <E52>/logs/<stage>/commands.txt.
set -u
E52=${E52:-datasets/E52}
stage=$1
shift
[ "$#" -le 2 ] || { echo "at most 2 lanes" >&2; exit 2; }
inputs=$E52/gold_inputs.jsonl
case $stage in
  pilot) sel=(--hosts "$E52/pilot_hosts.txt") ;;
  full) sel=() ;;
  topup) sel=(); inputs=$E52/topup_inputs.jsonl ;;
  *) echo "stage: pilot | full | topup" >&2; exit 2 ;;
esac
out=$E52/preds/$stage
logs=$E52/logs/$stage
mkdir -p "$out" "$logs"

poi_r() {  # POI reasoning level per model (final_config)
  case $1 in
    gemma4-31b-it) echo short ;;
    qwen38-27b) echo low ;;
    qwen-agentworld-35b-a3b) echo short ;;
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
    cmd="python3 -I scripts/E52/run.py --http-log $logs/${m}_$r.http.log -- \
--dev $inputs ${sel[*]} --out-dir $out --cache $E52/cache --model $m --workers 6 $args"
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
