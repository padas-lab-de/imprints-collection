set -e
R=${R:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round3}
D=${D:-/home/dinzinger/GitHub/imprints-collection-e35/datasets/E34r3/full}
mkdir -p $D
ssh mispel 'cat $HOME/GitHub/imprints-collection-e34r3/results/E34r3/logs/driver_full.log; cd $HOME/GitHub/imprints-collection-e34r3/datasets/E34r3/full; ls; sha256sum *; wc -l fetch_status_batch*.tsv discovered_external_hosts.txt; for f in imprints_batch*.jsonl.gz; do echo $f $(zcat $f | wc -l); done; ls $HOME/e34r3_tree.tgz 2>&1' > $R/remote_listing_full.txt
cat $R/remote_listing_full.txt
scp -q "mispel:GitHub/imprints-collection-e34r3/datasets/E34r3/full/*" $D/
scp -q mispel:GitHub/imprints-collection-e34r3/datasets/E34r3/e34r3_rest.txt $D/../
scp -q mispel:GitHub/imprints-collection-e34r3/results/E22/logs/fetch_0-0.log $D/../fetch_full_0-0.log
scp -q mispel:GitHub/imprints-collection-e34r3/results/E22/logs/fetch_1-1.log $D/../fetch_full_1-1.log
cd $D; sha256sum *; wc -l fetch_status_batch*.tsv discovered_external_hosts.txt
for f in imprints_batch*.jsonl.gz; do echo $f $(zcat $f | wc -l); done
