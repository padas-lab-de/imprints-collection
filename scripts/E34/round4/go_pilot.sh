#!/bin/bash
R=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round4
scp -q -o BatchMode=yes $R/pilot_r4.txt $R/e34r4_run.sh mispel: || { echo SCP FAILED; exit 1; }
ssh -o BatchMode=yes mispel 'bash -s' < $R/launch_r4.sh
