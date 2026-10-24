#!/usr/bin/env bash
# E12 screening pipeline (run from the repository root with nohup).
# PY: a Python with requests, resiliparse, playwright, pillow, openai, python-dotenv.
# RENDER_LIBS: extracted Chromium system libraries (no sudo on the crawl VM).
set -u
ROOT=/home/dinzinger/GitHub/imprints-collection
E8WT=$ROOT/.claude/worktrees/agent-ac37363e2dedffa7e
PY=${PY:-$E8WT/.venv-render/bin/python}
RENDER_LIBS=${RENDER_LIBS:-$E8WT/.render-libs/root}
export PYTHONPATH=src
export LD_LIBRARY_PATH=$RENDER_LIBS/usr/lib/x86_64-linux-gnu
export FONTCONFIG_PATH=$RENDER_LIBS/etc/fonts
LOG=$ROOT/results/E12/logs
DATA=$ROOT/datasets/E12
S=scripts/gold/e12_screen.py
mkdir -p "$LOG"

$PY $S wayback > "$LOG/wayback.log" 2>&1 &
WB=$!
$PY $S static --workers 8 > "$LOG/static.log" 2>&1
$PY $S llm --workers 4 --follow > "$LOG/llm.log" 2>&1 &
LLM=$!
$PY $S render --workers 4 > "$LOG/render.log" 2>&1
touch "$DATA/render.done"
wait $LLM
echo "pause before retry $(date -u)" >> "$LOG/retry.log"
sleep 1800
$PY $S static --retry --workers 4 >> "$LOG/retry.log" 2>&1
$PY $S render --retry --workers 2 >> "$LOG/retry.log" 2>&1
# re-run the text judgement for retried hosts
cat "$DATA/static_retry_hosts.txt" "$DATA/render_retry_hosts.txt" | sort -u > "$DATA/retried_hosts.txt"
$PY -c "
import json,sys
p='$DATA/llm_text_gemma4-31b-it.jsonl'
r=set(l.strip() for l in open('$DATA/retried_hosts.txt') if l.strip())
keep=[l for l in open(p) if json.loads(l)['host'] not in r]
open(p,'w').writelines(keep)
print('llm records dropped for re-run:', len(r))
" >> "$LOG/retry.log" 2>&1
$PY $S llm --workers 4 >> "$LOG/llm.log" 2>&1
$PY $S vision --workers 3 > "$LOG/vision.log" 2>&1
wait $WB
$PY $S features > "$LOG/features.log" 2>&1
echo "pipeline done $(date -u)" >> "$LOG/features.log"
