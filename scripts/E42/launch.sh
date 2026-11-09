#!/usr/bin/env bash
# waits until 11:03 UTC, then launches the E42 pilot on mispel
until [ $(date -u +%s) -ge $(date -u -d '2026-11-06 11:03' +%s) ]; do sleep 30; done
ssh -o BatchMode=yes mispel 'bash -s' <<'EOF'
set -e
R=$HOME/GitHub/imprints-collection-e34r3
P=$R/pilot_e42
[ -e $P ] && { echo "$P exists"; exit 1; }
avail=$(free -m | awk '/^Mem:/{print $7}')
[ "$avail" -ge 8000 ] || { echo "MEM SHORT $avail"; exit 1; }
mkdir -p $P/datasets/E42
mv $HOME/stage_e42_pilot100.txt $P/datasets/E42/pilot100.txt
sha256sum $P/datasets/E42/pilot100.txt
ROOT=$R DATA=$P PY=$R/.venv/bin/python OUT=$P/datasets/E42/pilot WORKERS=4 PCONC=1 PDELAY=60 PCOOL=60 BACKOFF=300 RESTARTS=0 \
  setsid nohup bash $R/scripts/E19/run.sh $P/datasets/E42/pilot100.txt >> $P/driver_pilot.log 2>&1 < /dev/null &
sleep 5
echo "launched $(date -u +%FT%TZ)"
ps -u $USER -o pid,ppid,rss,etime,args | grep -E "run.sh|ic.ic" | grep -v grep | cut -c1-200
EOF
