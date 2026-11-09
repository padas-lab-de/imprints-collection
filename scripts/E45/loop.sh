#!/bin/bash
D=${D:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E45}
for i in 1 2 3; do
  sleep 600
  echo "=== $(date -u +%FT%TZ) A mispel (10 s)"; bash $D/chk.sh mispel imprints-collection-e34r3 pilot_e45a 2>&1 || true
  echo "=== B apfel (60 s)"; bash $D/chk.sh apfel imprints-collection-e41 pilot_e45b 2>&1 || true
done
