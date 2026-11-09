#!/bin/bash
cd /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24
for c in gsw nds ltz hsb ksh pfl pdc swg stq lim bar dsb frr; do for s in train test; do
python3 fw_shard2.py HuggingFaceFW/fineweb-2 data/${c}_Latn/$s/000_00000.parquet url dump fw2small 8 >> small_run.log 2>&1; done; done
echo ALLDONE >> small_run.log
