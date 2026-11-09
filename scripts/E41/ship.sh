#!/bin/bash
# Split E41/<LIST>.txt into contiguous shards (equal line counts) over the VMs and deliver them (scp to .part, then mv).
# Usage: ship.sh L4 [vm ...]   (default apfel aspe abelie mispel). Shards kept in E41/shards_<LIST>/<LIST>_<vm>.txt
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E41
L=$1; shift
VMS=${*:-apfel aspe abelie mispel}
set -- $VMS
N=$#
mkdir -p $T/shards_$L
rm -f $T/shards_$L/*
split -n l/$N -d --additional-suffix=.part $T/$L.txt $T/shards_$L/x
i=0
for vm in $VMS; do
  f=$T/shards_$L/x$(printf %02d $i).part
  mv $f $T/shards_$L/${L}_$vm.txt
  i=$((i+1))
  scp -q $T/shards_$L/${L}_$vm.txt $vm:GitHub/imprints-collection-e41/datasets/E41/${L}_$vm.txt.part &&
    ssh $vm "mv GitHub/imprints-collection-e41/datasets/E41/${L}_$vm.txt.part GitHub/imprints-collection-e41/datasets/E41/${L}_$vm.txt"
  echo "$L $vm $(wc -l < $T/shards_$L/${L}_$vm.txt) $(sha256sum $T/shards_$L/${L}_$vm.txt | cut -c1-16)"
done
