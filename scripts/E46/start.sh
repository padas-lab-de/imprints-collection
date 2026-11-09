#!/bin/bash
set -e
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E46}
sha256sum $T/list.txt > $T/list.txt.sha256
cat $T/list.txt.sha256
ssh mispel 'cd ~/GitHub/imprints-collection-e34r3 && .venv/bin/python -c "from ic.cli.fetch import HEADERS; print(HEADERS)"'
scp -q $T/list.txt mispel:e46_list.txt
ssh mispel "TREE=imprints-collection-e34r3 PD=pilot_e46 STAGE=e46_list.txt RATE=5 bash -s" < $T/launch.sh
