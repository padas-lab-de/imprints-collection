#!/usr/bin/env bash
# E34 round 2 full crawl (D38 B): batches $1-$2 of e34r2_rest.txt
D=$HOME/GitHub/imprints-collection-e35
export ROOT=$D/results/E34r2/root
export PY=$HOME/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
echo "$(date -u +%FT%TZ) full $1-$2 start"
bash $D/scripts/E22/run.sh $D/datasets/E34r2/e34r2_rest.txt $D/datasets/E34r2/full $1 $2
echo "$(date -u +%FT%TZ) full $1-$2 end"
echo "$(date -u +%FT%TZ) driver done"
