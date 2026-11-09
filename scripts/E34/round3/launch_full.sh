D=$HOME/GitHub/imprints-collection-e34r3
echo "other fetch processes:"; pgrep -af "ic.ic import main|fetch " | grep -v pgrep | cut -c1-150
rm -f $HOME/e34r3_tree.tgz
mv $HOME/e34r3_rest.txt $D/datasets/E34r3/e34r3_rest.txt
mv $HOME/e34r3_full_run.sh $D/results/E34r3/e34r3_full_run.sh
sha256sum $D/datasets/E34r3/e34r3_rest.txt; wc -l $D/datasets/E34r3/e34r3_rest.txt
avail=$(free -g | awk 'NR==2{print $7}'); echo "avail GB $avail"
if [ "$avail" -lt 8 ]; then echo ABORT; exit 1; fi
cd $D
nohup setsid bash $D/results/E34r3/e34r3_full_run.sh > $D/results/E34r3/logs/driver_full.log 2>&1 < /dev/null &
sleep 45
date -u +%FT%TZ
pgrep -f "e34r3_full_run.sh" | while read p; do echo "DRIVER PID $p"; done
pgrep -f "fetch .*e34r3_rest.txt" | while read p; do echo "FETCH PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-400)"; done
cat $D/results/E34r3/logs/driver_full.log
