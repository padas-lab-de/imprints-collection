cd /home/dinzinger/GitHub/imprints-collection-e35/datasets/E34r3
scp -q mispel:GitHub/imprints-collection-e34r3/datasets/E34r3/e34r3_rest.txt .
scp -q mispel:GitHub/imprints-collection-e34r3/results/E22/logs/fetch_0-0.log fetch_full_0-0.log
scp -q mispel:GitHub/imprints-collection-e34r3/results/E22/logs/fetch_1-1.log fetch_full_1-1.log
sha256sum e34r3_rest.txt
cd full
sha256sum *
wc -l fetch_status_batch*.tsv discovered_external_hosts.txt
for f in imprints_batch*.jsonl.gz; do echo $f $(zcat $f | wc -l); done
