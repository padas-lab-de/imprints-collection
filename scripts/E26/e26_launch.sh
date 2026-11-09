#!/usr/bin/env bash
# usage: e26_launch.sh PY FIRST LAST   (run on the VM)
PYBIN=$1; F=$2; L=$3
D=~/GitHub/imprints-collection-d29
R=$D/results/E26/root
mkdir -p $D/datasets/E26/full $D/results/E26/logs $R/results
for n in src topics prompts scripts; do [ -e $R/$n ] || ln -s $D/$n $R/$n; done
[ -e $R/results/E22 ] || ln -s $D/results/E26 $R/results/E22
for x in $D/results/E26/logs/fetch_$F-*.log $D/results/E26/logs/driver_$F-$L.log; do [ -e "$x" ] && { echo "COLLISION $x"; exit 1; }; done
cd $D
ROOT=$R PY=$PYBIN STEP=1 SKIPGROUPS="v4:23.227.38" setsid nohup bash $D/scripts/E22/run.sh $D/datasets/E26/cc43_dach_rest.txt $D/datasets/E26/full $F $L >> $D/results/E26/logs/driver_$F-$L.log 2>&1 < /dev/null &
echo launched $(date -u +%T)
