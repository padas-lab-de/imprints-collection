#!/bin/bash
cd /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24
cat fw_files.txt | xargs -P 3 -I{} python3 fw_shard2.py HuggingFaceFW/fineweb-2 {} url dump fw2deu 16 >> fw_run.log 2>&1
echo ALLDONE >> fw_run.log
