#!/bin/bash
# Exit when the round-4 pilot driver is done, or when no driver process runs any more.
L=GitHub/imprints-collection-e34r3/results/E34r4/logs/driver.log
while true; do
  out=$(ssh -o BatchMode=yes mispel "tail -1 $L; ps -u \$USER -o pid,args | grep -c '[e]34r4_run.sh'" 2>&1)
  last=$(echo "$out" | head -1); n=$(echo "$out" | tail -1)
  if echo "$last" | grep -q "driver done"; then echo "DONE: $last"; exit 0; fi
  if [ "$n" = "0" ]; then echo "DRIVER GONE without done: $out"; exit 1; fi
  sleep 300
done
