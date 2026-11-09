#!/usr/bin/env bash
# E34 round 4 snapshots: copy each finished crawl dir's discovered_external_hosts.txt (outlink host list, written by ic fetch)
# into round4/snap/<name>.txt. Same method as round2/snap.sh and round3/snap3.sh (cp of that file), here from local e35 copies.
set -u
R=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round4
S=$R/snap
mkdir -p $S
E=/home/dinzinger/GitHub/imprints-collection-e35/datasets
cp_one() { # name path
  if test -f "$2"; then cp "$2" "$S/$1.txt"; echo "$(date -u +%FT%TZ) $1 $(wc -l < "$S/$1.txt")"; else echo "MISSING $1 $2"; fi
}
cp_one E34r3_pilot $E/E34r3/pilot/discovered_external_hosts.txt
cp_one E34r3_full $E/E34r3/full/discovered_external_hosts.txt
for vm in apfel aspe abelie mispel; do
  for L in L1 L2 L3 L4; do
    cp_one E41_${vm}_${L} $E/E41/$vm/${L}_${vm}/discovered_external_hosts.txt
  done
done
cp_one E43_pilot $E/E43/pilot/discovered_external_hosts.txt
cp_one E43_full $E/E43/full/discovered_external_hosts.txt
cp_one E44_pilot $E/E44/pilot/discovered_external_hosts.txt
cp_one E44_full $E/E44/full/discovered_external_hosts.txt
cp_one E45_A $E/E45/A/datasets/E45/out/discovered_external_hosts.txt
cp_one E45_B $E/E45/B/datasets/E45/out/discovered_external_hosts.txt
cp_one E46 $E/E46/datasets/E46/out/discovered_external_hosts.txt
cp_one E47 $E/E47/datasets/E47/out/discovered_external_hosts.txt
# E42: no crawl dir with outlinks on this host (pilot ran on mispel, 100 Shopify hosts) -> not a source
ls -la $S
