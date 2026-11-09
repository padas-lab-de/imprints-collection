#!/usr/bin/env bash
D=/home/dinzinger/GitHub/imprints-collection-d29
export ROOT=$D/results/E27/root
export PY=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
for p in "p1 p1_hostindex" "p2 p2_fineweb2" "p3 p3_hplt_ia"; do
  set -- $p
  rm -f /dev/null
  echo "$(date -u +%FT%TZ) pilot $1 start"
  bash $D/scripts/E22/run.sh $D/datasets/E27/$2.txt $D/datasets/E27/$1 0 0
  echo "$(date -u +%FT%TZ) pilot $1 end"
done
echo "$(date -u +%FT%TZ) driver done"
