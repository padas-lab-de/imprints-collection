set -e
R=${R:-$HOME/GitHub/imprints-collection}
W=$R/datasets/E19/merge_work
L=${L:-/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026}
mkdir -p $W/e16_50_262
for i in $(seq 50 262); do ln -sf ../e16/fetch_status_batch$(printf %06d $i).tsv $W/e16_50_262/; done
ls $W/e16_50_262 | wc -l
# validation on batches 0-49: does the rule minus primary cause 403 reproduce the round-1 list?
python3 $L/scripts/E19/collect.py --seeds-dir $W/e16_0_49 --out-dir $W/val_0_49 --seed-file $W/seed_hosts_shuffled.txt --deferred /nonexistent
awk -F'\t' 'NR>1 && $2!="403"{print $1}' $W/val_0_49/recovery_hosts.tsv | sort > $W/val_0_49/non403.sorted
sort $W/round1_recovery_input.txt > $W/val_0_49/round1.sorted
echo "round1 list lines: $(wc -l < $W/val_0_49/round1.sorted)  rule non403: $(wc -l < $W/val_0_49/non403.sorted)"
echo "in rule not in round1: $(comm -23 $W/val_0_49/non403.sorted $W/val_0_49/round1.sorted | wc -l)  in round1 not in rule: $(comm -13 $W/val_0_49/non403.sorted $W/val_0_49/round1.sorted | wc -l)"
# round 2
python3 $L/scripts/E19/collect.py --seeds-dir $W/e16_50_262 --out-dir $W/r2_collect --seed-file $W/seed_hosts_shuffled.txt --deferred /nonexistent
cat $W/r2_collect/counts_by_cause.tsv
