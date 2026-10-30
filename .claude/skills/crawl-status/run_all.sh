#!/usr/bin/env bash
# Run check_vm.sh on every VM in vms.tsv (in parallel; locally for this host), then print totals per crawl dir.
# Usage: bash run_all.sh [OUT_DIR]   (raw per-VM output is kept in OUT_DIR, default a mktemp dir)
S=$(cd "$(dirname "$0")" && pwd)
O=${1:-$(mktemp -d)}; mkdir -p "$O"
me=$(hostname)
while read -r vm repo; do
  [ -z "$vm" ] || [ "${vm#\#}" != "$vm" ] && continue
  if [ "$vm" = "$me" ]; then bash "$S/check_vm.sh" "$repo" > "$O/$vm.tsv" 2>&1 &
  else timeout 240 ssh -o BatchMode=yes -o ConnectTimeout=15 "$vm" "bash -s $repo" < "$S/check_vm.sh" > "$O/$vm.tsv" 2>&1 &
  fi
done < "$S/vms.tsv"
wait
for f in "$O"/*.tsv; do
  grep -q '^VM' "$f" || echo "UNREACHABLE	$(basename "$f" .tsv)	$(tail -1 "$f")"
done
cat "$O"/*.tsv | grep -v '^UNREACHABLE' | sort -t$'\t' -k1,1 -k2,2
# Totals per crawl dir across VMs (dirs are disjoint batch ranges of one list, so sums are exact)
awk -F'\t' '$1=="CRAWL" {f[$3]+=$4; r[$3]+=$5; i[$3]+=$6; v[$3]=v[$3] " " $2}
  END {for (d in r) printf "TOTAL\t%s\tfiles %d\thosts %d\timprint_found %d\tvms%s\n", d, f[d], r[d], i[d], v[d]}' "$O"/*.tsv | sort
echo "RAW	$O"
