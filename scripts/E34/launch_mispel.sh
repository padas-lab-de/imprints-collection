D=$HOME/GitHub/imprints-collection-d29
cd $D/results/E34
nohup setsid bash $D/results/E34/e34_run.sh > $D/results/E34/logs/driver.log 2>&1 < /dev/null &
sleep 20
date -u +%FT%TZ
pgrep -f "datasets/E34/pilot.txt" | while read p; do echo "PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-400)"; done
cat $D/results/E34/logs/driver.log
