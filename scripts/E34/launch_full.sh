D=$HOME/GitHub/imprints-collection-d29
free -g | grep Mem
sha256sum $D/src/ic/cli/fetch.py $D/datasets/E34/e34_rest.txt $D/results/E34/full_run.sh
mkdir -p $D/datasets/E34/full
cd $D/results/E34
nohup setsid bash $D/results/E34/full_run.sh > $D/results/E34/logs/driver_full.log 2>&1 < /dev/null &
sleep 20
date -u +%FT%TZ
pgrep -f "datasets/E34/e34_rest.txt" | while read p; do echo "PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-400)"; done
cat $D/results/E34/logs/driver_full.log
