#!/bin/bash
E=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33
nohup setsid bash $E/chain.sh > $E/chain.log 2>&1 < /dev/null &
echo "chain PID $! at $(date -u +%FT%TZ)"
