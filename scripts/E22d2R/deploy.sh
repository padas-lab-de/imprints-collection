# run ON the VM: deploy.sh <vm> <list sha256> <fetch.py sha256> <python> <first> <last> <step>
# expects ~/stage_d29.tar (git archive of the skip-provider commit) and ~/stage_rest.txt
set -e
V=$1; SHA=$2; FSHA=$3; PY=$4; FIRST=$5; LAST=$6; STEP=$7
R=$HOME/GitHub/imprints-collection-d29
[ -x $PY ] || { echo "no python $PY"; exit 1; }
[ -e $R ] && { echo "$R exists"; exit 1; }
mkdir -p $R && tar -xf $HOME/stage_d29.tar -C $R && rm $HOME/stage_d29.tar
got=$(sha256sum $R/src/ic/cli/fetch.py | cut -d' ' -f1)
[ "$got" = "$FSHA" ] || { echo "fetch.py MISMATCH $got"; exit 1; }
mkdir -p $R/datasets/E22 $R/results/E22/logs
mv $HOME/stage_rest.txt $R/datasets/E22/round2_frontier_rest.txt
got=$(sha256sum $R/datasets/E22/round2_frontier_rest.txt | cut -d' ' -f1)
[ "$got" = "$SHA" ] || { echo "SHA MISMATCH $got"; exit 1; }
echo "sha ok, lines $(wc -l < $R/datasets/E22/round2_frontier_rest.txt)"
cd $R
PYTHONPATH=$R/src $PY -c "import ic.cli.fetch as f; print('cap', f.MAX_BODY_BYTES, f.__file__)"
ROOT=$R PY=$PY STEP=$STEP SKIPGROUPS="v4:23.227.38" \
  setsid nohup bash $R/scripts/E22/run.sh $R/datasets/E22/round2_frontier_rest.txt $R/datasets/E22/depth2R $FIRST $LAST \
  >> $R/results/E22/logs/driver_depth2R.log 2>&1 < /dev/null &
sleep 8
echo "$(hostname) batches $FIRST-$LAST step $STEP launched $(date -u +%FT%TZ)"
ps -u $USER -o pid,ppid,rss,etime,args | grep -E "run.sh|ic.ic" | grep -v grep | cut -c1-170
ps -u $USER -o args | grep "main() fetch" | grep -o -- "--skip-provider-group [^ ]*" | head -1
