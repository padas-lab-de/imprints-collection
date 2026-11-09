cd "$HOME/GitHub/imprints-collection" || exit 1
R=${R:-$HOME/GitHub/imprints-collection}
LOG=results/E19/logs/driver_round1.log
ps -o pid=,args= -p 133338,133348 | cut -c1-90
kill 133338 133348
for i in $(seq 30); do kill -0 133348 2>/dev/null || break; sleep 2; done
kill -0 133348 2>/dev/null && { echo "still alive"; exit 1; }
echo "$(date -u +%FT%TZ) D25 B: stopped round 1 (run.sh 133338, fetch 133348); rest resharded to 4 VMs" >> $LOG
mkdir -p datasets/E19/reshard
python3 /tmp/e19dry/scripts/E19/reshard.py --input datasets/E19/round1/recovery_input.txt --status-dir datasets/E19/round1 --shards 4 --out-dir datasets/E19/reshard | tee datasets/E19/reshard/summary.txt
sha256sum datasets/E19/reshard/remaining_shard*.txt | tee datasets/E19/reshard/sha256.txt
cp /tmp/e19dry/scripts/E19/reshard.py datasets/E19/reshard/reshard.py.used
# shard 0 runs on apfel now (E19 already ran beside E16 here)
setsid nohup env OUT=$R/datasets/E19/round1_s0 PY=$R/.venv/bin/python bash scripts/E19/run.sh $R/datasets/E19/reshard/remaining_shard0.txt >> results/E19/logs/driver_round1_s0.log 2>&1 < /dev/null &
sleep 5
pgrep -af "round1_s0" | cut -c1-120
tail -2 results/E19/logs/driver_round1_s0.log
