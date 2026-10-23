#!/bin/bash
# E10: fetch all new candidate hosts with the current fetcher (E9 settings: 64 workers, UA Mozilla/5.0).
# Run from the worktree root; datasets/ must point to datasets/E10/expansion, results/ to the shared results dir.
set -e
PY=${PY:-python}
export PYTHONPATH=$PWD/src
mkdir -p results/logs
$PY -c "from ic.ic import main; main()" fetch /home/dinzinger/GitHub/imprints-collection/datasets/E10/candidate_hosts.txt > results/logs/E10-fetch-expansion.log 2>&1
