#!/bin/bash
# Lead watcher for E46: every 10 min; D43 C stop rule (>5% 429 after 20+ requests); 4 h cap; exit when the run ended.
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E46
LOG=$T/watch.log
PIDS="1860354 1860363"
CAP=$(date -u -d "2026-11-07 03:41:30" +%s)
while true; do
  out=$(bash $T/chk.sh mispel imprints-collection-e34r3 pilot_e46 2>&1)
  echo "$(date -u +%FT%TZ) $(echo "$out" | grep -E 'hosts_done|STOP_RULE' | tr '\n' ' ')" >> $LOG
  if echo "$out" | grep -q STOP_RULE; then
    ssh mispel "kill $PIDS" >> $LOG 2>&1
    echo "$(date -u +%FT%TZ) STOP RULE FIRED, killed $PIDS" >> $LOG; tail -3 $LOG; exit 0
  fi
  if [ $(date -u +%s) -ge $CAP ]; then
    ssh mispel "kill $PIDS" >> $LOG 2>&1
    echo "$(date -u +%FT%TZ) 4 h CAP, killed $PIDS" >> $LOG; tail -3 $LOG; exit 0
  fi
  if ! ssh mispel "kill -0 1860363" 2>/dev/null; then
    echo "$(date -u +%FT%TZ) ENDED" >> $LOG; tail -3 $LOG; exit 0
  fi
  sleep 600
done
