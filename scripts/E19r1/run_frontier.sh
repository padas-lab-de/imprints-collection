R=${R:-$HOME/GitHub/imprints-collection}
cd $R/datasets/E22/code/scripts/E22 || exit 1
PY=$R/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python
nice -n 19 $PY -I frontier.py --seeds $R/datasets/E16/seed_hosts_shuffled.txt \
  --input-dir $R/datasets/E22/input/aspe $R/datasets/E22/input/apfel \
  --out-dir $R/datasets/E22 \
  --overlap $R/datasets/E19/recovery_all.txt $R/datasets/E19/round1/recovery_all.txt $R/datasets/E19/round1/round1_no403.txt $R/datasets/E19/deferred_strato_hosts.txt \
  > $R/datasets/E22/tmp/frontier_run.log 2>&1
cat $R/datasets/E22/tmp/frontier_run.log
