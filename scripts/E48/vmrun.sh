#!/bin/bash
# usage: vmrun.sh VM  (reads commands on stdin; lorbeer is this host, so it runs locally)
VM=$1; shift
if [ "$VM" = "$(hostname)" ]; then bash -s "$@"; else ssh -o BatchMode=yes -o ConnectTimeout=20 "$VM" bash -s "$@"; fi
