set -e
R=${R:-$HOME/GitHub/$TREE}
P=$R/$PD
[ -e $P ] && { echo "$P exists"; exit 1; }
avail=$(free -m | awk '/^Mem:/{print $7}')
[ "$avail" -ge 4000 ] || { echo MEM SHORT $avail; exit 1; }
mkdir -p $P/datasets/E47
mv $HOME/$STAGE $P/datasets/E47/list.txt
sha256sum $P/datasets/E47/list.txt
ROOT=$R DATA=$P PY=$R/.venv/bin/python OUT=$P/datasets/E47/out WORKERS=4 PCONC=1 PDELAY=$RATE PCOOL=$RATE BACKOFF=300 RESTARTS=0 \
  setsid nohup bash $R/scripts/E19/run.sh $P/datasets/E47/list.txt >> $P/driver.log 2>&1 < /dev/null &
sleep 5
echo "launched $(date -u +%FT%TZ)"
ps -u $USER -o pid,ppid,etime,args | grep -E "pilot_e47" | grep -v grep | cut -c1-160
