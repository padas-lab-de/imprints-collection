#!/usr/bin/env bash
# E34 round 3 pilot (5,000 DACH hosts), D39 B user agent, tree imprints-collection-e34r3 @ 3a23d5d
D=$HOME/GitHub/imprints-collection-e34r3
export ROOT=$D
export PY=$D/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
echo "$(date -u +%FT%TZ) pilot start"
nice -n 10 bash $D/scripts/E22/run.sh $D/datasets/E34r3/pilot_r3.txt $D/datasets/E34r3/pilot 0 0
echo "$(date -u +%FT%TZ) pilot end"
echo "$(date -u +%FT%TZ) driver done"
