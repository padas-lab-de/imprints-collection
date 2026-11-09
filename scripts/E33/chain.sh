#!/bin/bash
# waits for q4, then runs q1 and q2 pilots one after another (one E33 fetch at a time)
E=${E:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33}
D=${D:-/home/dinzinger/GitHub/imprints-collection-d29}
until grep -q "pilot q4 end" $D/results/E33/logs/driver_q4.log; do sleep 15; done
for q in q1 q2; do
  cp $E/${q}_pilot.txt $D/datasets/E33/
  bash $E/e33_run.sh $q > $D/results/E33/logs/driver_$q.log 2>&1
done
echo chain done > $D/results/E33/logs/chain.done
