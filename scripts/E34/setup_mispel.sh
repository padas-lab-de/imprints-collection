set -e
D=$HOME/GitHub/imprints-collection-d29
mkdir -p $D/datasets/E34 $D/results/E34/root/results $D/results/E34/logs
cd $D/results/E34/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E34 results/E22
ls -la . results
sha256sum $D/src/ic/cli/fetch.py
