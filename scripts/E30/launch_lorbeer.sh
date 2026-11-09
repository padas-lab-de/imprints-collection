set -e
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp
D=$HOME/GitHub/imprints-collection-d29
FIRST=0; LAST=54
[ "$(sha256sum $D/src/ic/cli/fetch.py | cut -d' ' -f1)" = c34d09b29442e39bb7e956a0024bb769bcefbe816f53e9b9c30e4f32bf5a0ebc ] || { echo FETCH_SHA_MISMATCH; exit 1; }
echo "avail before: $(free -g | sed -n 2p)"
df -h /home | tail -1
mkdir -p $D/datasets/E30 $D/results/E30/root/results $D/results/E30/logs
cp $T/E30/e30_rest.txt $D/datasets/E30/e30_rest.txt
[ "$(sha256sum $D/datasets/E30/e30_rest.txt | cut -d' ' -f1)" = 438aba2cf8f7bf8b26b0da19b1f12544cc195a1de363b12efd79ba428dcf5452 ] || { echo LIST_SHA_MISMATCH; exit 1; }
cd $D/results/E30/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E30 results/E22
export ROOT=$D/results/E30/root
export PY=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
nohup setsid bash $D/scripts/E22/run.sh $D/datasets/E30/e30_rest.txt $D/datasets/E30/full $FIRST $LAST > $D/results/E30/logs/driver_$FIRST-$LAST.log 2>&1 < /dev/null &
echo launched $! at $(date -u +%FT%TZ)
