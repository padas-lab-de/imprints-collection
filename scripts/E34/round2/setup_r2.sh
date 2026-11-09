set -e
D=$HOME/GitHub/imprints-collection-e35
mkdir -p $D/datasets/E34r2 $D/results/E34r2/root/results $D/results/E34r2/logs
cd $D/results/E34r2/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E34r2 results/E22
ls -la . results
free -g | sed -n 2p
