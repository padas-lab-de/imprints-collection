#!/bin/bash
# E10: rerun the analysis. Run from the worktree root with PY=<python with ic deps>.
set -e
export PYTHONPATH=$PWD/src
mkdir -p results/E10
$PY scripts/E10/candidates.py results/E10 > results/E10/candidates.txt
$PY scripts/E10/analyze.py > results/E10/analysis.txt
$PY scripts/E10/seed_dach_yield.py > results/E10/seed_dach_yield.txt
