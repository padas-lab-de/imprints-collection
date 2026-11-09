#!/bin/bash
cd /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33
python3 q3_load.py > q3_load.log 2>&1
echo EXIT $? >> q3_load.log
