#!/usr/bin/env bash
# E50 phase 2 tables for one set (dev500 | heldout300): per schema, the pooled set and each data part.
#   bash scripts/E50/report_set.sh dev500 <out dir>
# Parts: all, e49 (E49 rendered DOM, E49-style refs), e49_noimprint (E49 hosts with an empty imprint text),
# e51 (E51 static HTML, E51 refs). Base reasoning: POI gemma r-short, qwen r-default, agentworld r-short; WZ and
# address r-none.
set -u
set_name=$1
out=$2
preds=results/E50/preds/$set_name
mkdir -p "$out"
for part in all e49 e49_noimprint e51; do
  hosts=""
  if [ "$part" != all ]; then hosts="--hosts results/E50/parts/${set_name}_${part}.txt"; fi
  python3 -I scripts/E50/compare.py --schema poi3 --refs results/E50/refs/poi3_$set_name.jsonl --dir $preds/poi3 \
    --base gemma=r-short --base qwen=r-default --base agentworld=r-short $hosts --title "$set_name $part" \
    --out "$out/poi3_$part.md" --json "$out/poi3_$part.json" > /dev/null
  python3 -I scripts/E50/compare.py --schema wz --refs results/E50/refs/wz_$set_name.jsonl --dir $preds/wz \
    --base gemma=r-none --base qwen=r-none --base agentworld=r-none $hosts --title "$set_name $part" \
    --out "$out/wz_$part.md" --json "$out/wz_$part.json" > /dev/null
  python3 -I scripts/E50/compare.py --schema address --refs results/E50/refs/addr_$set_name.jsonl --dir $preds/address \
    --base gemma=r-none --base qwen=r-none --base agentworld=r-none $hosts --title "$set_name $part" \
    --out "$out/address_$part.md" --json "$out/address_$part.json" > /dev/null
  python3 -I scripts/E50/addr_score.py --refs results/E50/refs/addr_$set_name.jsonl $hosts $preds/address/*.jsonl \
    > "$out/address_metrics_$part.jsonl"
  python3 -I scripts/E50/joint_compare.py --dir $preds --refs-dir results/E50/refs --set $set_name $hosts \
    --sep gemma=poi3:r-short,wz:r-none,address:r-none --sep qwen=poi3:r-default,wz:r-none,address:r-none \
    --sep agentworld=poi3:r-short,wz:r-none,address:r-none --title "$set_name $part" --out "$out/joint_$part.md" > /dev/null
  echo "$part done"
done
