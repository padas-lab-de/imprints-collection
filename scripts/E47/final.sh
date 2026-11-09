#!/bin/bash
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E47
D=/home/dinzinger/GitHub/imprints-collection-e35/datasets/E47
mkdir -p $T/res $D
ssh mispel 'ps -p 2776461,2776469 -o pid,cmd || echo procs-gone'
rsync -a mispel:GitHub/imprints-collection-e34r3/pilot_e47/ $T/res/
rsync -a $T/res/ $D/
cp $T/list.txt $T/list.txt.sha256 $D/
f=$T/res/datasets/E47/out/fetch_status_batch000000.tsv
awk -F'\t' 'NR>1{n++; s[$2]++; req+=$6; th+=$7; p[$4]+=$6; ph[$4]++}
  END{print "hosts",n,"requests",req,"throttled",th; for(k in s) print " status",k,s[k]; for(k in p) print " provider",k,"hosts",ph[k],"requests",p[k]}' $f
awk -F'\t' 'NR==2{print "first end_time",$9} END{print "last end_time",$9}' $f
L=$T/res/results/E19/logs/fetch_recovery.log
grep -c " 429 " $L
grep "limiter" $L | tail -1 | grep -oE "limiter.*" | cut -c1-200
grep -E "recovery (start|exit)" $T/res/driver.log
