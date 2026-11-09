D=$HOME/GitHub/imprints-collection-e35
cd $D/results/E34r2
nohup setsid bash $D/results/E34r2/e34r2_run.sh > $D/results/E34r2/logs/driver.log 2>&1 < /dev/null &
sleep 60
date -u +%FT%TZ
pgrep -f "run.sh .*E34r2/pilot_r2.txt" | while read p; do echo "DRIVER PID $p"; done
pgrep -f "fetch .*E34r2/pilot_r2.txt" | while read p; do echo "FETCH PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-500)"; done
cat $D/results/E34r2/logs/driver.log
ls $D/datasets/E34r2/pilot 2>&1 | head
free -g | sed -n 2p
