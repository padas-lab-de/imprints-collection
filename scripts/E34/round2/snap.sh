T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2/snap}
D29='$HOME/GitHub/imprints-collection-d29'
E35='$HOME/GitHub/imprints-collection-e35'
for vm in mispel abelie apfel aspe; do
 for dd in E26/full E29/full E34/pilot E34/full E25/pilot E27/p1 E27/p2 E27/p3 E28/p1 E28/p2; do
  n=$(echo $dd | tr / _)
  if ssh $vm "test -f $D29/datasets/$dd/discovered_external_hosts.txt" 2>/dev/null; then
   ssh $vm "cat $D29/datasets/$dd/discovered_external_hosts.txt" > $T/${vm}__d29_$n.txt
   echo "$(date -u +%FT%TZ) $vm d29 $dd $(wc -l < $T/${vm}__d29_$n.txt)"
  fi
 done
 for dd in E33/full E36/pilot; do
  n=$(echo $dd | tr / _)
  if ssh $vm "test -f $E35/datasets/$dd/discovered_external_hosts.txt" 2>/dev/null; then
   ssh $vm "cat $E35/datasets/$dd/discovered_external_hosts.txt" > $T/${vm}__e35_$n.txt
   echo "$(date -u +%FT%TZ) $vm e35 $dd $(wc -l < $T/${vm}__e35_$n.txt)"
  fi
 done
done
D=${D:-$HOME/GitHub/imprints-collection-d29}
for dd in E30/full E28/p1 E28/p2; do
 f=$D/datasets/$dd/discovered_external_hosts.txt
 if test -f $f; then n=$(echo $dd | tr / _); cp $f $T/lorbeer__d29_$n.txt; echo "$(date -u +%FT%TZ) lorbeer d29 $dd $(wc -l < $T/lorbeer__d29_$n.txt)"; fi
done
