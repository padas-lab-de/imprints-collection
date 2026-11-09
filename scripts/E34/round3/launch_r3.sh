D=$HOME/GitHub/imprints-collection-e34r3
mkdir -p $D/datasets/E34r3 $D/results/E34r3/logs
mv $HOME/pilot_r3.txt $D/datasets/E34r3/pilot_r3.txt
mv $HOME/e34r3_run.sh $D/results/E34r3/e34r3_run.sh
sha256sum $D/datasets/E34r3/pilot_r3.txt; wc -l $D/datasets/E34r3/pilot_r3.txt
avail=$(free -g | awk 'NR==2{print $7}'); echo "avail GB $avail"
if [ "$avail" -lt 8 ]; then echo ABORT; exit 1; fi
cd $D
nohup setsid bash $D/results/E34r3/e34r3_run.sh > $D/results/E34r3/logs/driver.log 2>&1 < /dev/null &
sleep 45
date -u +%FT%TZ
pgrep -f "e34r3_run.sh" | while read p; do echo "DRIVER PID $p"; done
pgrep -f "fetch .*E34r3/pilot_r3.txt" | while read p; do echo "FETCH PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-400)"; done
cat $D/results/E34r3/logs/driver.log
