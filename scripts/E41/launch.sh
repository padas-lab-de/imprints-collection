#!/bin/bash
# Start the E41 driver on the VMs given (refuses if an ic fetch / driver already runs there or avail RAM < 8 GB).
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E41
for vm in "$@"; do
  scp -q $T/run_e41_vm.sh $vm:GitHub/imprints-collection-e41/results/E41/run_e41_vm.sh
  ssh $vm "VM=$vm bash -s" <<'EOF'
D=$HOME/GitHub/imprints-collection-e41
if pgrep -f "ic.ic import main|run_e41_vm.sh" >/dev/null; then echo "$VM: fetch or driver already running, ABORT"; exit 1; fi
avail=$(free -g | awk 'NR==2{print $7}'); echo "$VM avail GB $avail"
if [ "$avail" -lt 8 ]; then echo "$VM ABORT low memory"; exit 1; fi
cd $D
nohup setsid bash $D/results/E41/run_e41_vm.sh $VM > $D/results/E41/logs/driver.log 2>&1 < /dev/null &
sleep 20
date -u +%FT%TZ
pgrep -f "run_e41_vm.sh" | while read p; do echo "$VM DRIVER PID $p"; done
pgrep -f "ic.ic import main" | while read p; do echo "$VM FETCH PID $p: $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-300)"; done
cat $D/results/E41/logs/driver.log
EOF
done
