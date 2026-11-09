#!/usr/bin/env bash
D=${D:-/home/dinzinger/GitHub/imprints-collection-d29}
export ROOT=$D/results/E28/root
export PY=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
for p in "p1 p1_other_tld" "p2 p2_old_dach"; do
  set -- $p
  echo "$(date -u +%FT%TZ) pilot $1 start"
  bash $D/scripts/E22/run.sh $D/datasets/E28/$2.txt $D/datasets/E28/$1 0 0
  echo "$(date -u +%FT%TZ) pilot $1 end"
done
echo "$(date -u +%FT%TZ) driver done"
