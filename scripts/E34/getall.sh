T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/snap}
mkdir -p $T
D=${D:-/home/dinzinger/GH/imprints-collection-d29}
D=$(echo $D | sed 's#/GH/#/Git''Hub/#')
for vm in mispel abelie apfel aspe; do
 for dd in E26/full E29/full E25/pilot E27/p1 E27/p2 E27/p3 E28/p1 E28/p2; do
  n=$(echo $dd | tr / _)
  if ssh -o BatchMode=yes $vm "test -f $D/datasets/$dd/discovered_external_hosts.txt" 2>/dev/null; then
   ssh $vm "cat $D/datasets/$dd/discovered_external_hosts.txt" > $T/${vm}__$n.txt
   echo "$(date -u +%FT%TZ) $vm $dd $(wc -l < $T/${vm}__$n.txt)"
  fi
 done
done
for dd in E30/full E28/p1 E28/p2; do
 f=$D/datasets/$dd/discovered_external_hosts.txt
 if test -f $f; then n=$(echo $dd | tr / _); cp $f $T/lorbeer__$n.txt; echo "$(date -u +%FT%TZ) lorbeer $dd $(wc -l < $T/lorbeer__$n.txt)"; fi
done
