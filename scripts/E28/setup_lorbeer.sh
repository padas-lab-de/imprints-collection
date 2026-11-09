set -e
D=${D:-$HOME/GitHub/imprints-collection-d29}
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E28}
mkdir -p $D/datasets/E28 $D/results/E28/root/results $D/results/E28/logs
cp $T/p1_other_tld.txt $T/p2_old_dach.txt $D/datasets/E28/
sha256sum $D/datasets/E28/*.txt
cd $D/results/E28/root
for x in src topics prompts scripts; do ln -sfn $D/$x $x; done
ln -sfn $D/results/E28 results/E22
ls -la . results
