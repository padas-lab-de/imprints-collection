#!/bin/bash
# Lead watcher for E45: every 10 min check A and B; apply the D42 A stop rule; exit when both runs ended.
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E45}
LOG=$T/watch.log
declare -A VM=([A]=mispel [B]=apfel)
declare -A TREE=([A]=imprints-collection-e34r3 [B]=imprints-collection-e41)
declare -A DIR=([A]=pilot_e45a [B]=pilot_e45b)
declare -A PIDS=([A]="1152947 1152955" [B]="3296865 3296874")
declare -A DONE=([A]=0 [B]=0)
while true; do
  for r in A B; do
    [ "${DONE[$r]}" = 1 ] && continue
    out=$(bash $T/chk.sh ${VM[$r]} ${TREE[$r]} ${DIR[$r]} 2>&1)
    echo "$(date -u +%FT%TZ) run $r: $(echo "$out" | grep -E 'hosts_done|STOP_RULE' | tr '\n' ' ')" >> $LOG
    if echo "$out" | grep -q STOP_RULE; then
      ssh ${VM[$r]} "kill ${PIDS[$r]}" 2>&1 >> $LOG
      echo "$(date -u +%FT%TZ) run $r: STOP RULE FIRED, killed ${PIDS[$r]}" >> $LOG
      DONE[$r]=1; continue
    fi
    if [ $(date -u +%s) -ge $(date -u -d "2026-11-06 20:52:30" +%s) ]; then
      ssh ${VM[$r]} "kill ${PIDS[$r]}" >> $LOG 2>&1
      echo "$(date -u +%FT%TZ) run $r: 4 h CAP, killed ${PIDS[$r]}" >> $LOG
      DONE[$r]=1; continue
    fi
    py=${PIDS[$r]##* }
    if ! ssh ${VM[$r]} "kill -0 $py" 2>/dev/null; then
      echo "$(date -u +%FT%TZ) run $r: ENDED" >> $LOG; DONE[$r]=1
    fi
  done
  [ "${DONE[A]}" = 1 ] && [ "${DONE[B]}" = 1 ] && { echo "$(date -u +%FT%TZ) both ended" >> $LOG; tail -6 $LOG; exit 0; }
  sleep 600
done
