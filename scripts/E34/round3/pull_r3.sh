set -e
D=/home/dinzinger/GitHub/imprints-collection-e35/datasets/E34r3/pilot
mkdir -p $D
ssh mispel 'cat $HOME/GitHub/imprints-collection-e34r3/results/E34r3/logs/driver.log; ls -la $HOME/GitHub/imprints-collection-e34r3/datasets/E34r3/pilot; cd $HOME/GitHub/imprints-collection-e34r3/datasets/E34r3/pilot; sha256sum *; wc -l fetch_status_batch000000.tsv discovered_external_hosts.txt; zcat imprints_batch000000.jsonl.gz | wc -l' > /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round3/remote_listing.txt
cat /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round3/remote_listing.txt
scp -q "mispel:GitHub/imprints-collection-e34r3/datasets/E34r3/pilot/*" $D/
scp -q mispel:GitHub/imprints-collection-e34r3/datasets/E34r3/pilot_r3.txt $D/../
scp -q mispel:GitHub/imprints-collection-e34r3/results/E22/logs/fetch_0-0.log $D/../fetch_0-0.log
cd $D; sha256sum *; wc -l fetch_status_batch000000.tsv discovered_external_hosts.txt; zcat imprints_batch000000.jsonl.gz | wc -l
