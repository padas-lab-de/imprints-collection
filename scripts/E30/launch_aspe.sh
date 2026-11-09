set -e
D=$HOME/GitHub/imprints-collection-d29
FIRST=28; LAST=54
PY=$HOME/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python
[ "$(sha256sum $D/src/ic/cli/fetch.py | cut -d' ' -f1)" = c34d09b29442e39bb7e956a0024bb769bcefbe816f53e9b9c30e4f32bf5a0ebc ] || { echo FETCH_SHA_MISMATCH; exit 1; }
[ "$(sha256sum $D/datasets/E30/e30_rest.txt | cut -d' ' -f1)" = 438aba2cf8f7bf8b26b0da19b1f12544cc195a1de363b12efd79ba428dcf5452 ] || { echo LIST_SHA_MISMATCH; exit 1; }
[ -x $PY ] || { echo NO_PY; exit 1; }
echo "avail before: $(free -g | sed -n 2p)"
df -h /home | tail -1
pgrep -f "datasets/E30/e30_rest.txt" && { echo E30_ALREADY_RUNNING; exit 1; }
mkdir -p $D/results/E30/root/results $D/results/E30/logs $D/datasets/E30/full
cd $D/results/E30/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E30 results/E22
export ROOT=$D/results/E30/root PY STEP=1 SKIPGROUPS="v4:23.227.38"
nohup setsid bash $D/scripts/E22/run.sh $D/datasets/E30/e30_rest.txt $D/datasets/E30/full $FIRST $LAST > $D/results/E30/logs/driver_$FIRST-$LAST.log 2>&1 < /dev/null &
echo launched $! at $(date -u +%FT%TZ)
sleep 20
pgrep -f "datasets/E30/e30_rest.txt" | while read p; do echo "PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-300)"; done
cat $D/results/E30/logs/driver_$FIRST-$LAST.log
