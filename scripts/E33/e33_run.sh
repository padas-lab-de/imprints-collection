#!/usr/bin/env bash
# usage: e33_run.sh qN   (one pilot; list must be in $D/datasets/E33/qN_pilot.txt)
D=/home/dinzinger/GitHub/imprints-collection-d29
export ROOT=$D/results/E33/root
export PY=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
q=$1
echo "$(date -u +%FT%TZ) pilot $q start"
bash $D/scripts/E22/run.sh $D/datasets/E33/${q}_pilot.txt $D/datasets/E33/$q 0 0
echo "$(date -u +%FT%TZ) pilot $q end"
