cd ~/GitHub/imprints-collection/datasets/E22/code || exit 1
PY=~/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python
nice -n 19 $PY -m pytest -q tests/test_e22_frontier.py -p no:cacheprovider 2>&1 | tail -8
cmp ~/GitHub/imprints-collection/datasets/E16/seed_hosts_shuffled.txt ~/GitHub/imprints-collection/datasets/E16/seed_hosts_shuffled.txt && wc -l ~/GitHub/imprints-collection/datasets/E16/seed_hosts_shuffled.txt
