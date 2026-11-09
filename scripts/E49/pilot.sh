#!/usr/bin/env bash
# E49 pilot: every strategy and option once on the 20 pilot hosts (no reference labels; checks that the
# code runs end to end and measures calls, tokens and latency). Run from the repository root.
#   bash scripts/E49/pilot.sh [poi|wz|all]
set -u
OUT=results/E49/pilot/preds
H=results/E49/pilot_hosts.txt
R="python3 scripts/E49/run.py --hosts $H --out-dir $OUT"
WHICH=${1:-all}

if [[ $WHICH == poi || $WHICH == all ]]; then
  S="--schema poi"
  while read -r args; do
    [[ -z $args ]] && continue
    echo "== poi $args"; $R $S $args 2>&1 | tail -1
  done <<'EOF'
--strategy flat --node-text path
--strategy flat --node-text name
--strategy flat --node-text kw
--strategy flat --node-text desc
--strategy flat --output top3
--strategy flat --reason short
--strategy flat --think on
--strategy flat --shots 4
--strategy flat --lang en
--strategy flat --input imprint
--strategy flat --input both
--strategy flat --depth 1
--strategy flat --no-none
--strategy flat --samples 5 --temperature 0.7
--strategy flat --model gemma4-31b-it
--strategy flat --model qwen-agentworld-35b-a3b
--strategy flat --model soofi-s-isar-preview
--strategy hier --node-text path
--strategy hier --node-text kw
--strategy hier --node-text desc
--strategy hier --beam 2
--strategy retrieve --k 10
--strategy retrieve --k 30
--strategy retrieve --k 60
--strategy retrieve --k 30 --rerank
--strategy retrieve --k 30 --emb-text desc
--strategy retrieve --k 30 --emb-text name
--strategy describe --k 30
--strategy describe --k 30 --chooser both
--strategy describe --k 30 --rerank
EOF
  python3 scripts/E49/ensemble.py --out $OUT/poi/ens__flat__4models.jsonl \
    $OUT/poi/flat__qwen__home__dmax__nt-path.jsonl $OUT/poi/flat__gemma__home__dmax__nt-path.jsonl \
    $OUT/poi/flat__agentworld__home__dmax__nt-path.jsonl $OUT/poi/flat__soofi__home__dmax__nt-path.jsonl
fi

if [[ $WHICH == wz || $WHICH == all ]]; then
  S="--schema wz"
  while read -r args; do
    [[ -z $args ]] && continue
    echo "== wz $args"; $R $S $args 2>&1 | tail -1
  done <<'EOF'
--strategy flat --depth 2 --node-text path
--strategy flat --depth 3 --node-text path
--strategy flat --depth 3 --node-text incl
--strategy hier --node-text path
--strategy hier --node-text kw
--strategy hier --node-text incl
--strategy hier --node-text incl --beam 2
--strategy retrieve --k 30 --node-text path
--strategy retrieve --k 30 --node-text incl --emb-text incl
--strategy retrieve --k 30 --node-text kw --rerank
--strategy describe --k 30 --node-text incl
EOF
fi
