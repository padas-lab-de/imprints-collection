cd /home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/agent-a27575026707ca6ad
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp}
nice -n 19 python3 scripts/E40/parking_filter.py apply --in $T/E31/r3/in --scan $T/E40/r3/scan/*.scan.tsv --targets scripts/E40/targets_classified.tsv --out $T/E40/r3/out
