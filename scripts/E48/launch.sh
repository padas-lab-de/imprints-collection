# Run on a VM: bash -s with TREE, STAGE (list in ~), RATE. Data in ~/GitHub/$TREE/shopify_e48.
set -e
R=${R:-$HOME/GitHub/$TREE}
P=$R/shopify_e48
[ -e $P ] && { echo "$P exists"; exit 1; }
avail=$(free -m | awk '/^Mem:/{print $7}')
[ "$avail" -ge 4000 ] || { echo MEM SHORT $avail; exit 1; }
cd $R && .venv/bin/python -c "from ic.cli.fetch import HEADERS; print(HEADERS['User-Agent'])" | grep -q "ImprintsCollectionBot/1.0; +https://www.fim.uni-passau.de/data-science" || { echo UA WRONG; exit 1; }
mkdir -p $P/datasets/E48
mv $HOME/$STAGE $P/datasets/E48/list.txt
sha256sum $P/datasets/E48/list.txt
ROOT=$R DATA=$P PY=$R/.venv/bin/python OUT=$P/datasets/E48/out WORKERS=4 PCONC=1 PDELAY=$RATE PCOOL=$RATE BACKOFF=300 RESTARTS=5 \
  setsid nohup bash $R/scripts/E19/run.sh $P/datasets/E48/list.txt >> $P/driver.log 2>&1 < /dev/null &
echo "PGID $(hostname) $!"
sleep 5
ps -o pid,pgid,etime,args -g $! | cut -c1-140
