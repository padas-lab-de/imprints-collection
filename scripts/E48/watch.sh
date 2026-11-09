#!/bin/bash
# E48 global watcher (D45): every 5 min check all 5 VMs; if any VM's last-200-request window has >5%
# throttled (429/503), kill the run on ALL VMs (process groups in pgids.tsv). Exit when all runs ended.
W=/home/dinzinger/E48-shopify
LOG=$W/watch.log
while true; do
  stop=0; alive=0
  while read vm tree pgid; do
    line=$(bash $W/chk.sh $vm $tree 2>&1 | tail -1)
    if echo "kill -0 -$pgid 2>/dev/null" | bash $W/vmrun.sh $vm; then a=up; alive=$((alive+1)); else a=gone; fi
    echo "$(date -u +%FT%TZ) $line run=$a" >> $LOG
    echo "$line" | grep -q WINDOW_STOP && stop=1
  done < $W/pgids.tsv
  if [ $stop -eq 1 ]; then
    while read vm tree pgid; do
      echo "kill -- -$pgid" | bash $W/vmrun.sh $vm >> $LOG 2>&1
      echo "$(date -u +%FT%TZ) killed $vm pgid $pgid" >> $LOG
    done < $W/pgids.tsv
    echo "$(date -u +%FT%TZ) GLOBAL STOP (window rule)" >> $LOG; exit 0
  fi
  if [ $alive -eq 0 ]; then echo "$(date -u +%FT%TZ) ALL ENDED" >> $LOG; exit 0; fi
  sleep 300
done
