R=${R:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round3}
T=$R/snap
mkdir -p $T
# unchanged sources: reuse round 2 snapshots
for f in mispel__d29_E25_pilot mispel__d29_E26_full abelie__d29_E26_full apfel__d29_E26_full aspe__d29_E26_full \
  mispel__d29_E27_p1 mispel__d29_E27_p2 mispel__d29_E27_p3 lorbeer__d29_E28_p1 lorbeer__d29_E28_p2 \
  mispel__d29_E29_full abelie__d29_E29_full apfel__d29_E29_full mispel__d29_E34_full mispel__d29_E34_pilot; do
  cp $R/../round2/snap/$f.txt $T/$f.txt
done
E35='$HOME/GitHub/imprints-collection-e35'
for vm in mispel abelie apfel aspe; do
  for dd in E33/full E37/full E36/pilot E34r2/full E34r2/pilot; do
    n=$(echo $dd | tr / _)
    if ssh $vm "test -f $E35/datasets/$dd/discovered_external_hosts.txt" 2>/dev/null; then
      ssh $vm "cat $E35/datasets/$dd/discovered_external_hosts.txt" > $T/${vm}__e35_$n.txt
      echo "$(date -u +%FT%TZ) $vm e35 $dd $(wc -l < $T/${vm}__e35_$n.txt)"
    fi
  done
done
D29='$HOME/GitHub/imprints-collection-d29'
ssh aspe "cat $D29/datasets/E30/full/discovered_external_hosts.txt" > $T/aspe__d29_E30_full.txt
echo "aspe E30 $(wc -l < $T/aspe__d29_E30_full.txt)"
cp $HOME/GitHub/imprints-collection-d29/datasets/E30/full/discovered_external_hosts.txt $T/lorbeer__d29_E30_full.txt
echo "lorbeer E30 $(wc -l < $T/lorbeer__d29_E30_full.txt)"
ls -la $T
