#!/bin/bash
# usage: chk.sh VM TREE ; one line per VM: totals + window of the last >=200 requests (by end_time).
# Prints WINDOW_STOP when that window has >5% throttled (429/503).
W=/home/dinzinger/E48-shopify
VM=$1; TREE=$2
bash $W/vmrun.sh $VM <<EOF
cd ~/GitHub/$TREE/shopify_e48/datasets/E48/out 2>/dev/null || { echo "$VM NO_DIR"; exit 0; }
cat fetch_status_batch*.tsv 2>/dev/null | awk -F'\t' 'NF==9 && \$1!="host"' | sort -t\$'\t' -k9,9n | awk -F'\t' -v vm=$VM '
 {h++; r+=\$6; t+=\$7; s[\$2]++; R[NR]=\$6; TH[NR]=\$7; if(\$2=="imprint_found") f++}
 END{wr=0; wt=0; for(i=NR;i>0 && wr<200;i--){wr+=R[i]; wt+=TH[i]}
  printf "%s hosts=%d requests=%d throttled=%d imprint_found=%d win_req=%d win_thr=%d", vm,h,r,t,f,wr,wt
  if(wr>=200 && wt*20>wr) printf " WINDOW_STOP"; print ""}'
EOF
