#!/bin/bash
# read-only: running fetches, trees, memory, disk, load per VM
for v in "$@"; do
  echo "== $v"
  ssh -o BatchMode=yes "$v" 'pgrep -af "ic fetch|ic.ic import|fetch " | grep -v pgrep | cut -c1-160; ls -d ~/Git*/*; free -g | sed -n 2p; df -h ~ | tail -1; uptime; ps -eo user,pcpu,args --sort=-pcpu | head -4 | cut -c1-120' 2>&1
done
