#!/bin/bash
# run on the target VM: launch.sh <k> <expected sha256 of ~/round2_shard<k>.txt as staged>
set -e
k=$1; sha=$2
R=${R:-$HOME/GitHub/imprints-collection-e22}
S=$R/datasets/E19/round2_s$k
mkdir -p $R/datasets/E19 $S $R/results/E19/logs
got=$(sha256sum $R/datasets/E19/round2_shard$k.txt | cut -d' ' -f1)
[ "$got" = "$sha" ] || { echo "SHA MISMATCH $got"; exit 1; }
echo "sha ok $got"
wc -l $R/datasets/E19/round2_shard$k.txt
cd $R
ROOT=$R DATA=$R PY=$R/.venv/bin/python OUT=$S WORKERS=16 PCONC=2 PDELAY=2.0 \
  setsid nohup bash scripts/E19/run.sh $R/datasets/E19/round2_shard$k.txt \
  >> $R/results/E19/logs/driver_round2_s$k.log 2>&1 < /dev/null &
sleep 2
echo launched
