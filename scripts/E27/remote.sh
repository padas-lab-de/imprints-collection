D=${D:-$HOME/GitHub/imprints-collection-d29}
tail -4 $D/results/E27/logs/driver.log
for p in p1 p2 p3; do echo "$p found $(tail -q -n +2 $D/datasets/E27/$p/fetch_status_batch*.tsv | awk -F'\t' '$2=="imprint_found"' | wc -l)"; done
