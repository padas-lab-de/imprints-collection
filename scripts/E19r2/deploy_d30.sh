# run ON the VM: deploy.sh <vm> <list sha256>
# expects staged ~/stage_d30.tar (git archive of the D30 commit) and ~/stage_round2c_<vm>.txt
set -e
V=$1; SHA=$2
R=$HOME/GitHub/imprints-collection-d30
PY=$HOME/GitHub/imprints-collection/.venv/bin/python
[ -e $R ] && { echo "$R exists"; exit 1; }
mkdir -p $R && tar -xf $HOME/stage_d30.tar -C $R && rm $HOME/stage_d30.tar
grep -n "^MAX_BODY_BYTES" $R/src/ic/cli/fetch.py
mkdir -p $R/datasets/E19 $R/results/E19/logs
mv $HOME/stage_round2c_$V.txt $R/datasets/E19/round2c_$V.txt
got=$(sha256sum $R/datasets/E19/round2c_$V.txt | cut -d' ' -f1)
[ "$got" = "$SHA" ] || { echo "SHA MISMATCH $got"; exit 1; }
echo "sha ok, lines $(wc -l < $R/datasets/E19/round2c_$V.txt)"
cd $R
PYTHONPATH=$R/src $PY -c "import ic.cli.fetch as f; print('cap', f.MAX_BODY_BYTES, f.__file__)"
ROOT=$R DATA=$R PY=$PY OUT=$R/datasets/E19/round2c_$V WORKERS=16 PCONC=2 PDELAY=2.0 RESTARTS=5 \
  setsid nohup bash $R/scripts/E19/run.sh $R/datasets/E19/round2c_$V.txt \
  >> $R/results/E19/logs/driver_round2c.log 2>&1 < /dev/null &
sleep 5
echo launched; ps -u $USER -o pid,ppid,rss,etime,args | grep -E "run.sh|ic.ic" | grep -v grep | cut -c1-170
