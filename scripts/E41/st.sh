#!/bin/bash
# E41 status, read-only. Per VM and list shard: rows (status-file rows, header excluded; retries may repeat a host),
# imprint_found, skipped_provider (Shopify group, 0 requests), shard size, plus driver/fetch PIDs and the driver's last line.
# Usage: bash st.sh [vm ...]   (default apfel aspe abelie mispel)
VMS=${*:-apfel aspe abelie mispel}
for vm in $VMS; do
  ssh -o BatchMode=yes -o ConnectTimeout=15 $vm 'bash -s' <<'EOF' 2>&1 | sed "s/^/$vm /"
D=$HOME/GitHub/imprints-collection-e41
echo "$(date -u +%FT%TZ) avail_GB=$(free -g | awk 'NR==2{print $7}') disk=$(df -h ~ | awk 'NR==2{print $5}')"
for L in L4 L3 L1 L2; do
  F=$D/datasets/E41/${L}_$(hostname -s).txt
  O=$D/datasets/E41/${L}_$(hostname -s)
  [ -s "$F" ] || { echo "$L shard: not delivered yet"; continue; }
  n=$(wc -l < "$F")
  if ls $O/fetch_status_batch*.tsv >/dev/null 2>&1; then
    tail -q -n +2 $O/fetch_status_batch*.tsv | awk -F'\t' -v L=$L -v n=$n '{r++; s[$2]++} END{printf "%s shard=%d rows=%d (%.1f%%) imprint_found=%d (%.1f%%) host_not_found=%d skipped_provider=%d\n", L, n, r, 100*r/n, s["imprint_found"], (r?100*s["imprint_found"]/r:0), s["host_not_found"], s["skipped_provider"]}'
  else
    echo "$L shard=$n rows=0"
  fi
done
pgrep -f "run_e41_vm.sh" | while read p; do echo "driver pid $p"; done
pgrep -f "ic.ic import main" | while read p; do echo "fetch pid $p $(tr '\0' ' ' < /proc/$p/cmdline | grep -o 'fetch [^ ]*')"; done
tail -n 1 $D/results/E41/logs/driver.log
EOF
done
