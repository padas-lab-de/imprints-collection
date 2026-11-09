set -e
R=~/GitHub/imprints-collection
W=$R/datasets/E19/merge_work
mkdir -p $W/e16 $W/r1/round1 $W/r1/round1_s0 $W/r1/round1_s1 $W/r1/round1_s2 $W/r1/round1_s3
INC="--include=fetch_status_batch*.tsv --exclude=*"
# E16 status files
rsync -a $INC aspe:GitHub/imprints-collection/datasets/E16/seeds/ $W/e16/
rsync -a $INC apfel:GitHub/imprints-collection/datasets/E16/seeds/ $W/e16/
rsync -a $INC mispel:GitHub/imprints-collection/datasets/E16/seeds/ $W/e16/
rsync -a $INC $R/datasets/E16/seeds/ $W/e16/
# round 1
rsync -a $INC apfel:GitHub/imprints-collection/datasets/E19/round1/ $W/r1/round1/
rsync -a $INC apfel:GitHub/imprints-collection/datasets/E19/round1_s0/ $W/r1/round1_s0/
rsync -a $INC aspe:GitHub/imprints-collection/datasets/E19/round1_s1/ $W/r1/round1_s1/
rsync -a $INC $R/datasets/E19/round1_s2/ $W/r1/round1_s2/
rsync -a $INC mispel:GitHub/imprints-collection/datasets/E19/round1_s3/ $W/r1/round1_s3/
# frozen round-1 list
scp -q apfel:GitHub/imprints-collection/datasets/E19/round1/recovery_input.txt $W/round1_recovery_input.txt
scp -q aspe:GitHub/imprints-collection/datasets/E16/seed_hosts_shuffled.txt $W/seed_hosts_shuffled.txt
ls $W/e16 | wc -l
for d in $W/r1/*; do echo $d $(ls $d | wc -l); done
wc -l $W/round1_recovery_input.txt $W/seed_hosts_shuffled.txt
