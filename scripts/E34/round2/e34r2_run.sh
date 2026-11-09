#!/usr/bin/env bash
D=$HOME/GitHub/imprints-collection-e35
export ROOT=$D/results/E34r2/root
export PY=$HOME/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
echo "$(date -u +%FT%TZ) pilot start"
bash $D/scripts/E22/run.sh $D/datasets/E34r2/pilot_r2.txt $D/datasets/E34r2/pilot 0 0
echo "$(date -u +%FT%TZ) pilot end"
echo "$(date -u +%FT%TZ) driver done"
