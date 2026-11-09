#!/bin/bash
# Start E48 on the 5 VMs at RATE s per request to each provider group. Writes pgids.tsv (vm tree pgid).
W=${W:-/home/dinzinger/E48-shopify}
RATE=3
sha256sum $W/list_*.txt > $W/lists.sha256
: > $W/pgids.tsv
for spec in apfel:imprints-collection-e41 aspe:imprints-collection-e41 abelie:imprints-collection-e41 mispel:imprints-collection-e41 lorbeer:imprints-collection-e43; do
  vm=${spec%%:*}; tree=${spec#*:}
  if [ "$vm" = "$(hostname)" ]; then
    cp $W/list_$vm.txt $HOME/e48_list.txt
    out=$(TREE=$tree STAGE=e48_list.txt RATE=$RATE bash $W/launch.sh 2>&1)
  else
    scp -q $W/list_$vm.txt $vm:e48_list.txt
    out=$(ssh -o BatchMode=yes $vm "TREE=$tree STAGE=e48_list.txt RATE=$RATE bash -s" < $W/launch.sh 2>&1)
  fi
  echo "== $vm"; echo "$out"
  pg=$(echo "$out" | awk '/^PGID/{print $3}')
  [ -n "$pg" ] && echo "$vm $tree $pg" >> $W/pgids.tsv
done
cat $W/pgids.tsv
