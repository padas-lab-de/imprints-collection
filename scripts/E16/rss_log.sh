#!/usr/bin/env bash
# E20 production check: log the RSS (KiB) of the running E16 fetch process every INTERVAL seconds.
# Usage: nohup bash scripts/E16/rss_log.sh >> results/E16/logs/rss.log 2>&1 < /dev/null &
INTERVAL=${INTERVAL:-600}
while true; do
  for p in $(pgrep -f 'import main; main\(\) fetch'); do
    echo "$(date -u +%FT%TZ) pid=$p rss_kib=$(ps -o rss= -p "$p" | tr -d ' ') range=$(ps -o args= -p "$p" | grep -oE '25000 [0-9]+ [0-9]+' | cut -d' ' -f2-)"
  done
  sleep "$INTERVAL"
done
