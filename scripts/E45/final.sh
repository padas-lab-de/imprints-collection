#!/bin/bash
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E45}
D=${D:-/home/dinzinger/GitHub/imprints-collection-e35/datasets/E45}
mkdir -p $T/res/A $T/res/B $D
ssh apfel 'ps -p 3296865,3296874 -o pid,cmd || echo B-procs-gone'
ssh mispel 'ps -p 1152947,1152955 -o pid,cmd || echo A-procs-gone'
rsync -a mispel:GitHub/imprints-collection-e34r3/pilot_e45a/ $T/res/A/
rsync -a apfel:GitHub/imprints-collection-e41/pilot_e45b/ $T/res/B/
rsync -a $T/res/ $D/
cp $T/listA.txt $T/listB.txt $T/sha256.txt $D/
for r in A B; do
  f=$(ls $T/res/$r/datasets/E45/out/fetch_status_batch*.tsv)
  echo "== run $r: $f"
  head -1 $f
  awk -F'\t' 'NR>1{n++; s[$2]++; req+=$6; th+=$7; p[$4]+=$6; ph[$4]++; if($7>0 && (ft==""||$9<ft)) ft=$9}
    END{print "hosts",n,"requests",req,"throttled",th; for(k in s) print " status",k,s[k]; for(k in p) print " provider",k,"hosts",ph[k],"requests",p[k]; print "first_throttle", ft}' $f
  awk -F'\t' 'NR==2{print "first end_time",$9} END{print "last end_time",$9}' $f
  grep -c " 429 " $T/res/$r/results/E19/logs/fetch_recovery.log
  grep -iE "recovery (start|exit)|throttl" $T/res/$r/results/E19/logs/fetch_recovery.log | grep -v "retry 429" | tail -3
done
