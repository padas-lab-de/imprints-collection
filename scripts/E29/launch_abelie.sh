set -e
D=$HOME/GitHub/imprints-collection-d29
FIRST=14; LAST=28
[ "$(sha256sum $D/src/ic/cli/fetch.py | cut -d' ' -f1)" = c34d09b29442e39bb7e956a0024bb769bcefbe816f53e9b9c30e4f32bf5a0ebc ] || { echo FETCH_SHA_MISMATCH; exit 1; }
mkdir -p $D/datasets/E29 $D/results/E29/root/results $D/results/E29/logs
mv /tmp/e29_rest.txt $D/datasets/E29/e29_rest.txt
[ "$(sha256sum $D/datasets/E29/e29_rest.txt | cut -d' ' -f1)" = c99935b12224af2410260c299225df297dc7135368d4c15377f49ea9e92ed806 ] || { echo LIST_SHA_MISMATCH; exit 1; }
cd $D/results/E29/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E29 results/E22
export ROOT=$D/results/E29/root
export PY=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python
export STEP=1 SKIPGROUPS="v4:23.227.38"
nohup setsid bash $D/scripts/E22/run.sh $D/datasets/E29/e29_rest.txt $D/datasets/E29/full $FIRST $LAST > $D/results/E29/logs/driver_$FIRST-$LAST.log 2>&1 < /dev/null &
echo launched $! at $(date -u +%FT%TZ)
free -g | sed -n 2p
