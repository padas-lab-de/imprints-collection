cd ~/GitHub/imprints-collection/datasets/E19 || exit 1
head -3 recovery_all.txt recovery_hosts.txt deferred_strato_hosts.txt round1/*.txt
wc -l recovery_all.txt recovery_hosts.txt deferred_strato_hosts.txt round1/*.txt
ls round1 pilot
