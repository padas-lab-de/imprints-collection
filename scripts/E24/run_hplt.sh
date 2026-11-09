#!/bin/bash
cd /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24
cat hplt_files.txt | xargs -P 2 -I{} python3 fw_shard2.py HPLT/HPLT2.0_cleaned {} u collection hplt 8 >> hplt_run.log 2>&1
echo ALLDONE >> hplt_run.log
