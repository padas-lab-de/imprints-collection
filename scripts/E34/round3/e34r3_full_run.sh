#!/usr/bin/env bash
# E34 round 3 full crawl (rest of frontier_r3 minus pilot), tree imprints-collection-e34r3 @ 3a23d5d
D=${D:-$HOME/GitHub/imprints-collection-e34r3}
export ROOT=$D
export PY=$D/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
echo "$(date -u +%FT%TZ) full start"
nice -n 10 bash $D/scripts/E22/run.sh $D/datasets/E34r3/e34r3_rest.txt $D/datasets/E34r3/full 0 1
echo "$(date -u +%FT%TZ) full end"
echo "$(date -u +%FT%TZ) driver done"
