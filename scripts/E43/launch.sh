#!/bin/bash
cd /home/dinzinger/GitHub/imprints-collection-e43
nohup setsid bash scripts/E43/run_pilots.sh > /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E43/driver.log 2>&1 &
echo $! > /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E43/driver.pid
