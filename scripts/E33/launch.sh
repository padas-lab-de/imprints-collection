#!/bin/bash
# usage: launch.sh qN  -> starts the pilot detached, prints PID
D=${D:-/home/dinzinger/GitHub/imprints-collection-d29}
q=$1
cp /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33/${q}_pilot.txt $D/datasets/E33/
nohup setsid bash /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33/e33_run.sh $q > $D/results/E33/logs/driver_$q.log 2>&1 < /dev/null &
echo "driver PID $! at $(date -u +%FT%TZ)"
