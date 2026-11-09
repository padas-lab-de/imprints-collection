set -e
R=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2
ssh abelie 'bash -s' < $R/setup_r2.sh > /dev/null
for vm in mispel abelie; do
  scp -q $R/e34r2_rest.txt $vm:GitHub/imprints-collection-e35/datasets/E34r2/e34r2_rest.txt
  scp -q $R/e34r2_full_run.sh $vm:GitHub/imprints-collection-e35/results/E34r2/e34r2_full_run.sh
  echo "$vm: $(ssh $vm 'sha256sum GitHub/imprints-collection-e35/datasets/E34r2/e34r2_rest.txt; ls -la GitHub/imprints-collection-e35/results/E34r2/root/results/')"
done
cat $R/e34r2_rest.txt.sha256
