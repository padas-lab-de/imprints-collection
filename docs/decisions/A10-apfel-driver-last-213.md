# A10-apfel-driver-last-213 (issued 2026-10-26, data-collection lead)

**Action:** lower the apfel E16 driver from `run.sh 157 262` (pid 56441) to stop at batch 213, because mispel crawls 214-262 since 2026-10-26 17:33 UTC. Needed before apfel reaches 214 (~50 batches at ~1 h: around 2026-10-28 evening UTC; do it by 2026-10-28 12:00 UTC).

Context: same as A9-aspe-driver-last-106; auto mode denied the lead ("Interfere With Workloads"); A9's approval covered aspe only. E19 round 1 (run.sh pid 133338) on apfel is not touched.

Commands (on apfel, in ~/GitHub/imprints-collection; the running fetch child finishes its range):
```
kill 56441
C=$(pgrep -f "fetch .*seed_hosts_shuffled.txt 25000" | head -1)   # child; range in `pgrep -af fetch`
echo "$(date -u +%FT%TZ) re-split: stopped driver 157-262; mispel has 214-262" >> results/E16/logs/driver.log
setsid nohup bash -c "while kill -0 $C 2>/dev/null; do sleep 60; done; PY=$PWD/.venv/bin/python exec bash scripts/E16/run.sh <next> 213" >> results/E16/logs/driver.log 2>&1 < /dev/null &
```
`<next>` = first batch after the child's range (child 163-165 -> 166).

**Answer:** "A10 go" (user, 2026-10-26); done by the lead 20:08 UTC (child was on 166-168, so the new driver runs 169-213).
