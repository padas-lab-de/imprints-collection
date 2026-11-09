#!/usr/bin/env bash
# E34 round 4 pilot (5,000 hosts, all TLDs, seed 344), D39 B user agent, tree imprints-collection-e34r3
D=${D:-$HOME/GitHub/imprints-collection-e34r3}
export ROOT=$D
export PY=$D/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
echo "$(date -u +%FT%TZ) pilot start"
nice -n 10 bash $D/scripts/E22/run.sh $D/datasets/E34r4/pilot_r4.txt $D/datasets/E34r4/pilot 0 0
echo "$(date -u +%FT%TZ) pilot end"
echo "$(date -u +%FT%TZ) driver done"
