set -e
D=$HOME/GitHub/imprints-collection-d29
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33
mkdir -p $D/datasets/E33 $D/results/E33/root/results $D/results/E33/logs
cd $D/results/E33/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E33 results/E22
ls -la . results
sha256sum $D/src/ic/cli/fetch.py
