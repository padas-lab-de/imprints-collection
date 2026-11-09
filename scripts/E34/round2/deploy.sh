set -e
R=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2
ssh mispel 'bash -s' < $R/setup_r2.sh
scp $R/pilot_r2.txt mispel:GitHub/imprints-collection-e35/datasets/E34r2/pilot_r2.txt
scp $R/e34r2_run.sh mispel:GitHub/imprints-collection-e35/results/E34r2/e34r2_run.sh
ssh mispel 'sha256sum ~/GitHub/imprints-collection-e35/datasets/E34r2/pilot_r2.txt; wc -l ~/GitHub/imprints-collection-e35/datasets/E34r2/pilot_r2.txt; free -m | sed -n 2p'
sha256sum $R/pilot_r2.txt
