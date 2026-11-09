#!/bin/bash
cd /home/dinzinger/GitHub/imprints-collection-e43
setsid nohup nice -n 10 bash scripts/E43/run_full.sh > /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E43/driver_full.log 2>&1 &
echo $! > /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E43/driver_full.pid
