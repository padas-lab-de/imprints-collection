#!/usr/bin/env bash
D=$HOME/GitHub/imprints-collection-d29
export ROOT=$D/results/E34/root
export PY=$HOME/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
echo "$(date -u +%FT%TZ) full start"
bash $D/scripts/E22/run.sh $D/datasets/E34/e34_rest.txt $D/datasets/E34/full 0 1
echo "$(date -u +%FT%TZ) driver done"
