# run ON mispel after deploy.sh: pilot.sh <list sha256> <python>
# Shopify pilot: 1 request at a time to the Shopify /24, 10 s apart; own DATA dir so its log is separate
set -e
SHA=$1; PY=$2
R=$HOME/GitHub/imprints-collection-d30
P=$R/pilot_d31
[ -e $P ] && { echo "$P exists"; exit 1; }
mkdir -p $P/datasets/E19 $P/results/E19/logs
mv $HOME/stage_shopify_pilot.txt $P/datasets/E19/shopify_pilot.txt
got=$(sha256sum $P/datasets/E19/shopify_pilot.txt | cut -d' ' -f1)
[ "$got" = "$SHA" ] || { echo "SHA MISMATCH $got"; exit 1; }
echo "pilot sha ok, lines $(wc -l < $P/datasets/E19/shopify_pilot.txt)"
ROOT=$R DATA=$P PY=$PY OUT=$P/datasets/E19/shopify_pilot WORKERS=4 PCONC=1 PDELAY=10 RESTARTS=5 \
  setsid nohup bash $R/scripts/E19/run.sh $P/datasets/E19/shopify_pilot.txt \
  >> $P/results/E19/logs/driver_pilot.log 2>&1 < /dev/null &
sleep 5
echo "$(hostname) pilot launched $(date -u +%FT%TZ)"; ps -u $USER -o pid,ppid,rss,etime,args | grep -E "run.sh|ic.ic" | grep -v grep | cut -c1-170
