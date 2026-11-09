# run ON the VM: deploy.sh <vm> <list sha256> <python>
# fresh VM: expects ~/stage_d30.tar; VM with D30 tree: reuses it (round2c log renamed). Always ~/stage_round2d_<vm>.txt
set -e
V=$1; SHA=$2; PY=$3
R=${R:-$HOME/GitHub/imprints-collection-d30}
FSHA=9ef3536c36daa01cc190813517130a8515d55ecd87fde1f9351303b65f4ee873
[ -x $PY ] || { echo "no python $PY"; exit 1; }
if [ -e $R ]; then
  echo "reuse $R"
  L=$R/results/E19/logs
  [ -e $L/fetch_recovery.log ] && [ ! -e $L/fetch_recovery_round2c.log ] && mv $L/fetch_recovery.log $L/fetch_recovery_round2c.log
  [ -e $L/fetch_recovery.log ] && { echo "fetch_recovery.log still there"; exit 1; }
  rm -f $HOME/stage_d30.tar
else
  mkdir -p $R && tar -xf $HOME/stage_d30.tar -C $R && rm $HOME/stage_d30.tar
fi
got=$(sha256sum $R/src/ic/cli/fetch.py | cut -d' ' -f1)
[ "$got" = "$FSHA" ] || { echo "fetch.py MISMATCH $got"; exit 1; }
mkdir -p $R/datasets/E19 $R/results/E19/logs
[ -e $R/datasets/E19/round2d_$V ] && { echo "round2d_$V exists"; exit 1; }
mv $HOME/stage_round2d_$V.txt $R/datasets/E19/round2d_$V.txt
got=$(sha256sum $R/datasets/E19/round2d_$V.txt | cut -d' ' -f1)
[ "$got" = "$SHA" ] || { echo "SHA MISMATCH $got"; exit 1; }
echo "sha ok, lines $(wc -l < $R/datasets/E19/round2d_$V.txt)"
cd $R
PYTHONPATH=$R/src $PY -c "import ic.cli.fetch as f; print('cap', f.MAX_BODY_BYTES, f.__file__)"
ROOT=$R DATA=$R PY=$PY OUT=$R/datasets/E19/round2d_$V WORKERS=16 PCONC=2 PDELAY=2.0 RESTARTS=5 \
  setsid nohup bash $R/scripts/E19/run.sh $R/datasets/E19/round2d_$V.txt \
  >> $R/results/E19/logs/driver_round2d.log 2>&1 < /dev/null &
sleep 5
echo "$(hostname) launched $(date -u +%FT%TZ)"; ps -u $USER -o pid,ppid,rss,etime,args | grep -E "run.sh|ic.ic" | grep -v grep | cut -c1-170
