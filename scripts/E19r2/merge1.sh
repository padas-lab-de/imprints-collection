set -e
R=${R:-$HOME/GitHub/imprints-collection}
W=$R/datasets/E19/merge_work
L=${L:-/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026}

mkdir -p $W/e16_0_49
for i in $(seq 0 49); do ln -sf ../e16/fetch_status_batch$(printf %06d $i).tsv $W/e16_0_49/; done
ls $W/e16_0_49 | wc -l
mkdir -p $R/results/E19
cd $R
python3 $L/scripts/E19/merge_report.py --e16-dir $W/e16_0_49 \
  --recovery-dir $W/r1/round1 --recovery-dir $W/r1/round1_s0 --recovery-dir $W/r1/round1_s1 \
  --recovery-dir $W/r1/round1_s2 --recovery-dir $W/r1/round1_s3 \
  --list $W/round1_recovery_input.txt --out $R/results/E19/round1_report.tsv
