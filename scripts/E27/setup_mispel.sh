set -e
D=${D:-$HOME/GitHub/imprints-collection-d29}
mkdir -p $D/datasets/E27 $D/results/E27/root/results $D/results/E27/logs
cd $D/results/E27/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E27 results/E22
ls -la . results
sha256sum $D/src/ic/cli/fetch.py
