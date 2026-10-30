#!/usr/bin/env bash
# Read-only crawl check of one VM. Usage: bash check_vm.sh REPO   (REPO = repo checkout, relative to ~ or absolute)
# Output lines (tab-separated after the tag):
#   VM       host  utc_time  mem_available_GB  disk_free  disk_use%
#   CRAWL    host  dir  status_files  hosts(unique)  imprint_found  last_write_age_min
#   FETCH    host  pid  elapsed  list  first-last  progress (last tqdm line of its log)
#   DRIVER   host  log  last_line            (logs written in the last 3 days)
#   ERROR    host  log                       (Traceback in a log written in the last 24 h)
R=$1; [ "${R#/}" = "$R" ] && R=$HOME/$R
cd "$R" 2>/dev/null || { printf 'VM\t%s\tNO_REPO %s\n' "$(hostname)" "$R"; exit 1; }
H=$(hostname); T=$'\t'
m=$(free -g | awk '/^Mem:/ {print $7}')
d=$(df -h . | awk 'NR==2 {print $4 "\t" $5}')
echo "VM$T$H$T$(date -u +%FT%TZ)$T$m$T$d"

# Crawl output dirs: datasets/<E>/<dir>/fetch_status_batch*.tsv (depth 2 only; deeper copies are inputs, not crawls)
# Finished tests are skipped (SKIP, extended regex on the dir).
SKIP=${SKIP:-'^datasets/(E1[0-5]|E[0-9])/|/pilot$'}
find datasets -mindepth 3 -maxdepth 3 -name 'fetch_status_batch*.tsv' -printf '%h\n' 2>/dev/null | sort -u | grep -Ev "$SKIP" |
  while read -r dir; do
    n=$(ls "$dir"/fetch_status_batch*.tsv | wc -l)
    age=$(( ($(date +%s) - $(stat -c %Y "$(ls -t "$dir"/fetch_status_batch*.tsv | head -1)")) / 60 ))
    # last complete 9-column row per host is final (ic fetch resume rule)
    awk -F'\t' 'NF==9 && $1!="host" {s[$1]=$2} END {n=0; f=0; for (h in s) {n++; if (s[h]=="imprint_found") f++}; printf "%d\t%d", n, f}' \
      "$dir"/fetch_status_batch*.tsv | { read -r rows found; echo "CRAWL$T$H$T$dir$T$n$T$rows$T$found$T$age"; }
  done

# Running fetch processes and their progress bar (read from the log the process writes its stderr to)
for pid in $(pgrep -u "$USER" -f 'main\(\) fetch'); do
  a=$(ps -o etime= -o args= -p "$pid") || continue
  et=$(echo "$a" | awk '{print $1}')
  set -- $(echo "$a" | sed 's/.*main() fetch //')
  lg=$(readlink "/proc/$pid/fd/2")   # drivers send the fetch's stderr (tqdm) to its log
  # tqdm lines are interleaved with INFO lines; take the last bar in the last 20 KB, cut before any glued INFO text
  p=$(tail -c 20000 "$lg" 2>/dev/null | tr '\r' '\n' | grep -a 'Processing' | tail -1 | sed 's/\] *20[0-9][0-9]-.*/]/')
  echo "FETCH$T$H$T$pid$T$et$T$1$T$3-$4$T${p:-no progress line in $lg}"
done
for lg in $(find results -path '*/logs/driver*.log' -mtime -3 2>/dev/null); do
  echo "DRIVER$T$H$T$lg$T$(tail -1 "$lg")"
done
for lg in $(find results -path '*/logs/*.log' -mtime -1 2>/dev/null); do
  grep -q Traceback "$lg" && echo "ERROR$T$H$T$lg"
done
exit 0
