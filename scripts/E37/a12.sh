set -e
D=${D:-/home/dinzinger/GitHub/imprints-collection-d29}
DRV=2400802; FET=408845
tr '\0' ' ' < /proc/$DRV/cmdline | grep -q "E30/e30_rest.txt.*0 54" || { echo DRV_MISMATCH; exit 1; }
tr '\0' ' ' < /proc/$FET/cmdline | grep -q "E30/e30_rest.txt 25000 8 8" || { echo FET_MISMATCH; exit 1; }
kill -TERM $DRV
sleep 3
kill -0 $DRV 2>/dev/null && { echo DRV_STILL_ALIVE; exit 1; }
kill -0 $FET || { echo FETCH_GONE; exit 1; }
n=$(pgrep -f "E30/e30_rest.txt 25000" | wc -l)
[ "$n" = 1 ] || { echo "UNEXPECTED_FETCH_COUNT $n"; pgrep -af "E30/e30_rest.txt 25000"; exit 1; }
W=$D/results/E30/logs/wait_9-27.sh
cat > $W <<EOF
while kill -0 $FET 2>/dev/null; do sleep 60; done
echo "\$(date -u +%FT%TZ) batch-8 fetch $FET gone, starting 9-27"
export ROOT=$D/results/E30/root PY=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python STEP=1 SKIPGROUPS="v4:23.227.38"
exec bash $D/scripts/E22/run.sh $D/datasets/E30/e30_rest.txt $D/datasets/E30/full 9 27
EOF
nohup setsid bash $W > $D/results/E30/logs/driver_9-27.log 2>&1 < /dev/null &
echo "driver $DRV stopped; fetch $FET alive; waiter $! queued at $(date -u +%FT%TZ)"
