#!/bin/bash
# Wait until the E43 rest crawl starts on lorbeer; fail if the driver dies. Max 60 min.
S=${S:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E43/st_full.sh}
for i in $(seq 1 60); do
  o=$(bash $S)
  if ! echo "$o" | grep -q "E43: not started"; then echo "$o"; exit 0; fi
  if ! echo "$o" | grep -q "alive: [0-9]"; then echo "DRIVER DEAD"; echo "$o"; exit 1; fi
  sleep 60
done
echo "E43 still not started after 60 min"; echo "$o"; exit 2
