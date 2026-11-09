#!/bin/bash
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp
for X in E43 E44; do
  cd "$T/$X" || exit 1
  grep -vxFf "pilot_$X.txt" "pool_$X.txt" > "rest_$X.txt"
  echo "$X rest=$(wc -l < "rest_$X.txt") pool=$(wc -l < "pool_$X.txt") uniq=$(sort -u "rest_$X.txt" | wc -l) overlap=$(grep -cxFf "pilot_$X.txt" "rest_$X.txt") pilot_in_pool=$(grep -cxFf "pool_$X.txt" "pilot_$X.txt")"
  sha256sum "rest_$X.txt" | tee "rest_$X.txt.sha256"
done
