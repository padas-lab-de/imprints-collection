#!/bin/bash
set -e
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E47
sha256sum $T/list.txt > $T/list.txt.sha256
cat $T/list.txt.sha256
ssh mispel 'cd ~/GitHub/imprints-collection-e34r3 && .venv/bin/python -c "from ic.cli.fetch import HEADERS; print(HEADERS)"'
scp -q $T/list.txt mispel:e47_list.txt
ssh mispel "TREE=imprints-collection-e34r3 PD=pilot_e47 STAGE=e47_list.txt RATE=2 bash -s" < $T/launch.sh
