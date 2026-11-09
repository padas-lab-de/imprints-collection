set -e
R=${R:-$HOME/GitHub/imprints-collection}
W=$R/datasets/E19/merge_work
L=${L:-/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026}
D=$R/datasets/E19/round2
mkdir -p $D $W/emptystatus
awk -F'\t' 'NR>1 && $2!="403"{print $1}' $W/r2_collect/recovery_hosts.tsv | sort -u > $D/cand.tmp
sort -u $W/round1_recovery_input.txt > $W/r1.sorted
comm -23 $D/cand.tmp $W/r1.sorted > $D/recovery_round2.txt
rm $D/cand.tmp
wc -l $D/recovery_round2.txt
(cd $D && sha256sum recovery_round2.txt > recovery_round2.sha256 && cat recovery_round2.sha256)
python3 $L/scripts/E19/reshard.py --input $D/recovery_round2.txt --status-dir $W/emptystatus --shards 2 --out-dir $D
for k in 0 1; do mv $D/remaining_shard$k.txt $D/round2_shard$k.txt; done
(cd $D && sha256sum round2_shard0.txt round2_shard1.txt | tee shards.sha256)
cp $W/r2_collect/recovery_hosts.tsv $D/recovery_hosts_all_causes.tsv
cp $W/r2_collect/counts_by_cause.tsv $D/
