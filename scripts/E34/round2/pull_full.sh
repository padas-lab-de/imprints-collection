# copy E34 round 2 full results from both VMs to res_full/ (read-only on the VMs)
R=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2
mkdir -p $R/res_full
for vm in mispel abelie; do
  scp -q "$vm:GitHub/imprints-collection-e35/datasets/E34r2/full/fetch_status_batch*.tsv" "$vm:GitHub/imprints-collection-e35/datasets/E34r2/full/imprints_batch*.jsonl.gz" $R/res_full/
done
ls $R/res_full | wc -l
