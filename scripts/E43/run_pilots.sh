#!/bin/bash
# E44 pilot then E43 pilot, one after the other, on lorbeer. Tree = D39 B (3a23d5d) at ~/GitHub/imprints-collection-e43.
# 32 workers, provider cap 8, Shopify group skipped, nice 10, STEP=1. Each pilot waits for its list (pilot_<X>.txt.sha256 written last).
D=$HOME/GitHub/imprints-collection-e43
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp
export ROOT=$D PY=$D/.venv/bin/python STEP=1 SKIPGROUPS="v4:23.227.38" WORKERS=32
for X in E44 E43; do
  F=$T/$X/pilot_$X.txt
  until [ -s "$F.sha256" ]; do sleep 60; done
  mkdir -p $D/datasets/$X
  cp $F $D/datasets/$X/pilot_$X.txt
  n=$(wc -l < $F); last=$(( (n + 24999) / 25000 - 1 ))
  echo "$(date -u +%FT%TZ) $X start hosts=$n batches=0-$last sha256=$(sha256sum $F | cut -c1-16)"
  nice -n 10 bash $D/scripts/E43/run.sh $D/datasets/$X/pilot_$X.txt $D/datasets/$X/pilot 0 $last
  echo "$(date -u +%FT%TZ) $X end"
done
echo "$(date -u +%FT%TZ) driver done"
