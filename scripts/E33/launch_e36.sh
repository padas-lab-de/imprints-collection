set -e
E=${E:-$HOME/GitHub/imprints-collection-e35}
[ "$(sha256sum $E/src/ic/cli/fetch.py | cut -d' ' -f1)" = a9dc1dddce1af24adfeb30c451697695c60d2a23cbd144d7d567e9fd7692bbab ] || { echo FETCH_SHA_MISMATCH; exit 1; }
PY=${PY:-/home/dinzinger/GitHub/imprints-collection/.venv/bin/python}
mkdir -p $E/datasets/E36
cp $HOME/e36_pilot.txt $E/datasets/E36/pilot.txt
[ "$(sha256sum $E/datasets/E36/pilot.txt | cut -d' ' -f1)" = 9fe5c6ef6c74e29e3a1b51222d28819c6b4010127613d15b08cd87eafc91c452 ] || { echo LIST_SHA_MISMATCH; exit 1; }
[ -x "$PY" ] || { echo NO_PY; exit 1; }
cd $E && "$PY" -c "import sys; sys.path.insert(0, '$E/src'); import ic.cli.fetch as f; print('fetch module', f.__file__)"
echo "avail: $(free -g | sed -n 2p)"
AV=$(free -m | awk 'NR==2{print $7}'); [ "$AV" -ge 8192 ] || { echo LOW_MEM $AV; exit 1; }
mkdir -p $E/results/E36/root/results $E/results/E36/logs $E/datasets/E36/pilot
cd $E/results/E36/root
for x in src topics prompts scripts; do ln -sfn $E/$x $x; done
ln -sfn $E/results/E36 results/E22
export ROOT=$E/results/E36/root PY STEP=1 SKIPGROUPS="v4:23.227.38"
nohup setsid bash $E/scripts/E22/run.sh $E/datasets/E36/pilot.txt $E/datasets/E36/pilot 0 0 > $E/results/E36/logs/driver.log 2>&1 < /dev/null &
echo launched $! at $(date -u +%FT%TZ)
sleep 25
pgrep -f "datasets/E36/pilot.txt" | while read p; do echo "PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-400)"; echo "  PYTHONPATH: $(tr '\0' '\n' < /proc/$p/environ | grep ^PYTHONPATH)"; done
cat $E/results/E36/logs/driver.log
