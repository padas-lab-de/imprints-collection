# runs on the VM: bash -s FIRST LAST
D=${D:-$HOME/GitHub/imprints-collection-e35}
F=$1; L=$2
avail=$(free -g | awk 'NR==2{print $7}')
if [ "$avail" -lt 8 ]; then echo "ABORT: only ${avail} GB available"; exit 1; fi
sha256sum $D/datasets/E34r2/e34r2_rest.txt
cd $D/results/E34r2
nohup setsid bash $D/results/E34r2/e34r2_full_run.sh $F $L > $D/results/E34r2/logs/driver_full_$F-$L.log 2>&1 < /dev/null &
sleep 60
date -u +%FT%TZ
pgrep -f "e34r2_full_run.sh $F $L" | while read p; do echo "DRIVER PID $p"; done
pgrep -f "fetch .*E34r2/e34r2_rest.txt 25000 $F $F" | while read p; do echo "FETCH PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | grep -o -e '--skip-provider-group [^ ]*' -e 'E34r2/full')"; done
cat $D/results/E34r2/logs/driver_full_$F-$L.log
tail -q -n +2 $D/datasets/E34r2/full/fetch_status_batch*.tsv 2>/dev/null | wc -l
free -g | sed -n 2p
