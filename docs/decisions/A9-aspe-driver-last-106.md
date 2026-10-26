# A9-aspe-driver-last-106 (issued 2026-10-26, data-collection lead)

**Action:** lower the aspe E16 driver from `run.sh 52 156` to stop at batch 106, because lorbeer crawls 107-156 since 2026-10-26. Needed before aspe reaches batch 107 (at ~1 batch/h from batch 58: around 2026-10-28 evening UTC; do it by 2026-10-28 12:00 UTC).

Context: the lead tried to stop the driver (pid 3496284) itself and queue a waiter; Claude Code auto mode denied it ("Interfere With Workloads"). Either the user runs the commands below, or the user approves the lead doing it.

Commands (on aspe, in ~/GitHub/imprints-collection; the running fetch child finishes its range):
```
kill 3496284        # run.sh 52 156; its child keeps running
C=$(pgrep -f "fetch .*seed_hosts_shuffled.txt 25000" | head -1)   # current fetch child
echo "$(date -u +%FT%TZ) re-split: stopped driver 52-156; lorbeer has 107-156" >> results/E16/logs/driver.log
nohup bash -c "while kill -0 $C 2>/dev/null; do sleep 60; done; exec bash scripts/E16/run.sh <next> 106" >> results/E16/logs/driver.log 2>&1 < /dev/null &
```
`<next>` = first batch after the child's range (child range is in `pgrep -af fetch`; e.g. child 58-60 -> 61).

**Answer:** "A9 go" (user, 2026-10-26); done by the lead 17:28 UTC (driver 58-106 after child 55-57).
