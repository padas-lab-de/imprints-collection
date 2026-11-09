#!/bin/bash
# E44 rest then E43 rest (D41 A) on lorbeer, one driver. Tree = D39 B at ~/GitHub/imprints-collection-e43.
# 32 workers, provider cap 8, Shopify group skipped, nice 10, STEP=1. Restart loop: re-runs scripts/E43/run.sh
# (which resumes from done hosts) until every range of a pass exits 0 (max 30 passes, 60 s apart).
# List files rest_<X>.txt + .sha256 are in $T/<X>; copied to datasets/<X>/rest_<X>.txt. Output datasets/<X>/full.
D=$HOME/GitHub/imprints-collection-e43
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp
export ROOT=$D PY=$D/.venv/bin/python STEP=1 SKIPGROUPS="v4:23.227.38" WORKERS=32
for X in E44 E43; do
  F=$T/$X/rest_$X.txt
  until [ -s "$F.sha256" ]; do sleep 60; done
  mkdir -p $D/datasets/$X
  cp $F $D/datasets/$X/rest_$X.txt
  L=$D/datasets/$X/rest_$X.txt
  n=$(wc -l < $L); last=$(( (n + 24999) / 25000 - 1 ))
  export LOGS=$D/results/$X/logs
  mkdir -p $LOGS
  echo "$(date -u +%FT%TZ) $X start hosts=$n batches=0-$last sha256=$(sha256sum $L | cut -c1-16)"
  for pass in $(seq 1 30); do
    nice -n 10 bash $D/scripts/E43/run.sh $L $D/datasets/$X/full 0 $last > $LOGS/pass_$pass.out 2>&1
    bad=$(grep -E 'range .* exit ' $LOGS/pass_$pass.out | grep -vc 'exit 0$')
    ok=$(grep -c 'all done' $LOGS/pass_$pass.out)
    echo "$(date -u +%FT%TZ) $X pass $pass bad_ranges=$bad all_done=$ok"
    [ "$bad" = 0 ] && [ "$ok" = 1 ] && break
    sleep 60
  done
  echo "$(date -u +%FT%TZ) $X end"
done
echo "$(date -u +%FT%TZ) driver done"
