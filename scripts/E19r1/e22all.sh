T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/e22chk.sh}
for h in aspe apfel abelie; do timeout 40 ssh $h 'bash -s GitHub/imprints-collection' < $T; echo ---; done
for h in akazie aralie; do timeout 40 ssh $h 'bash -s GitHub/imprints-collection-e22' < $T; echo ---; done
