#!/usr/bin/env bash
# E17 gold capture driver (run from the repository root with nohup):
#   nohup bash scripts/gold/e17_run.sh > /dev/null 2>&1 &
# Extra arguments go to e17_capture.py (e.g. --hosts deferred_strato.txt --no-strato-filter on another machine).
# PY: a Python with requests, resiliparse, playwright, pillow. RENDER_LIBS: extracted Chromium system libraries.
set -u
ROOT=/home/dinzinger/GitHub/imprints-collection
E8WT=$ROOT/.claude/worktrees/agent-ac37363e2dedffa7e
PY=${PY:-$E8WT/.venv-render/bin/python}
RENDER_LIBS=${RENDER_LIBS:-$E8WT/.render-libs/root}
export PYTHONPATH=src
export LD_LIBRARY_PATH=$RENDER_LIBS/usr/lib/x86_64-linux-gnu
export FONTCONFIG_PATH=$RENDER_LIBS/etc/fonts
LOG=$ROOT/results/E17/logs
mkdir -p "$LOG"
echo "start $(date -u +%FT%TZ)" >> "$LOG/capture.log"
$PY scripts/gold/e17_capture.py --workers 8 "$@" >> "$LOG/capture.log" 2>&1
echo "end $(date -u +%FT%TZ)" >> "$LOG/capture.log"
