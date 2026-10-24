#!/usr/bin/env bash
# Sample CPU, RSS and threads of the E13 fetch process every 30 s.
# Usage: monitor.sh <out.tsv>   (finds the process by its command line)
out="$1"
[ -f "$out" ] || echo -e "time\tpid\tcpu_pct\trss_mb\tthreads\tload1\tmem_avail_mb" > "$out"
while true; do
  pid=$(pgrep -f "fetch /home/dinzinger/GitHub/imprints-collection/datasets/E13/random100k_seed_hosts.txt" | head -1)
  load=$(cut -d' ' -f1 /proc/loadavg)
  avail=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
  if [ -n "$pid" ]; then
    read -r cpu rss nlwp < <(ps -o %cpu=,rss=,nlwp= -p "$pid")
    # %cpu of ps is a lifetime average; use top for the current value
    cur=$(top -b -n 2 -d 5 -p "$pid" | awk -v p="$pid" '$1==p {c=$9} END {print c}')
    echo -e "$(date +%s)\t$pid\t$cur\t$((rss/1024))\t$nlwp\t$load\t$avail" >> "$out"
  else
    echo -e "$(date +%s)\t-\t0\t0\t0\t$load\t$avail" >> "$out"
  fi
  sleep 25
done
