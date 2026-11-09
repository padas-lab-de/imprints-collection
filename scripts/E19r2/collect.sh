D=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d31/status
mkdir -p $D/aralie $D/aspe $D/lorbeer $D/abelie $D/apfel
scp -q 'aralie:GitHub/imprints-collection-e22/datasets/E19/round2b_aralie/fetch_status_batch*.tsv' $D/aralie/
scp -q 'aspe:GitHub/imprints-collection/datasets/E19/round2b_aspe/fetch_status_batch*.tsv' $D/aspe/
cp ~/GitHub/imprints-collection/datasets/E19/round2b_lorbeer/fetch_status_batch*.tsv $D/lorbeer/
scp -q 'abelie:GitHub/imprints-collection-d30/datasets/E19/round2c_abelie/fetch_status_batch*.tsv' $D/abelie/
scp -q 'apfel:GitHub/imprints-collection-d30/datasets/E19/round2c_apfel/fetch_status_batch*.tsv' $D/apfel/
ls -l $D/*/
