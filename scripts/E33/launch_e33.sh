set -e
# usage (on VM): FIRST=.. LAST=.. PY=.. bash -s < launch_e33.sh ; expects ~/e35_tree.tar.gz and ~/e33_rest.txt
E=${E:-$HOME/GitHub/imprints-collection-e35}
if [ ! -d $E ]; then mkdir -p $E && tar -xzf $HOME/e35_tree.tar.gz -C $E; fi
[ "$(sha256sum $E/src/ic/cli/fetch.py | cut -d' ' -f1)" = a9dc1dddce1af24adfeb30c451697695c60d2a23cbd144d7d567e9fd7692bbab ] || { echo FETCH_SHA_MISMATCH; exit 1; }
mkdir -p $E/datasets/E33
[ -f $E/datasets/E33/e33_rest.txt ] || cp $HOME/e33_rest.txt $E/datasets/E33/e33_rest.txt
[ "$(sha256sum $E/datasets/E33/e33_rest.txt | cut -d' ' -f1)" = c57938cd6456baf0e60ef55b119e61e0b70a07403ea678f6ceeee37268435ed4 ] || { echo LIST_SHA_MISMATCH; exit 1; }
[ -x "$PY" ] || { echo NO_PY; exit 1; }
cd $E && "$PY" -c "import sys; sys.path.insert(0, '$E/src'); import ic.cli.fetch as f; print('fetch module', f.__file__, f.IMPRINT_PROBE_PATHS)"
echo "avail before: $(free -g | sed -n 2p)"
df -h /home | tail -1
pgrep -f "datasets/E33/e33_rest.txt" && { echo E33_ALREADY_RUNNING; exit 1; }
mkdir -p $E/results/E33/root/results $E/results/E33/logs $E/datasets/E33/full
cd $E/results/E33/root
for x in src topics prompts scripts; do ln -sfn $E/$x $x; done
ln -sfn $E/results/E33 results/E22
export ROOT=$E/results/E33/root PY STEP=1 SKIPGROUPS="v4:23.227.38"
nohup setsid bash $E/scripts/E22/run.sh $E/datasets/E33/e33_rest.txt $E/datasets/E33/full $FIRST $LAST > $E/results/E33/logs/driver_$FIRST-$LAST.log 2>&1 < /dev/null &
echo launched $! at $(date -u +%FT%TZ)
sleep 20
pgrep -f "datasets/E33/e33_rest.txt" | while read p; do echo "PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-300)"; done
cat $E/results/E33/logs/driver_$FIRST-$LAST.log
