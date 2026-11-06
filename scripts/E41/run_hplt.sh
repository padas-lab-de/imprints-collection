#!/bin/bash
cd /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E41
cat hplt_files_all.txt | xargs -P 4 -I{} python3 hplt_shard.py HPLT/HPLT2.0_cleaned {} u collection hplt 8 >> hplt_run.log 2>&1
echo ALLDONE >> hplt_run.log
