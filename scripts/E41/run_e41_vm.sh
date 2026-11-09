#!/bin/bash
# E41 driver on one VM (one crawl job per VM). Runs the VM's shard of L4, L3, L1, L2 in this order with
# scripts/E22/run.sh (provider cap 8, 64 workers, skip v4:23.227.38 = Shopify, nice 10); tree = D39 B (3a23d5d).
# Shard file datasets/E41/<list>_<vm>.txt is waited for (delivered by scp then mv, so it is complete when it appears).
# Usage: run_e41_vm.sh VMNAME
VM=$1
D=$HOME/GitHub/imprints-collection-e41
export ROOT=$D
export PY=$D/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
for L in L4 L3 L1 L2; do
  F=$D/datasets/E41/${L}_${VM}.txt
  until [ -s "$F" ]; do sleep 60; done
  n=$(wc -l < "$F")
  last=$(( (n + 24999) / 25000 - 1 ))
  echo "$(date -u +%FT%TZ) $L start hosts=$n batches=0-$last sha256=$(sha256sum "$F" | cut -c1-16)"
  nice -n 10 bash $D/scripts/E22/run.sh "$F" $D/datasets/E41/${L}_${VM} 0 $last
  echo "$(date -u +%FT%TZ) $L end"
done
echo "$(date -u +%FT%TZ) driver done"
