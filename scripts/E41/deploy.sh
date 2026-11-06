#!/bin/bash
# deploy the tree on the VMs given as arguments (parallel); logs in E41/logs/setup_<vm>.log
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp
for vm in "$@"; do
  (
    scp -q $T/E34/round3/e34r3_tree.tgz $vm:e41_tree.tgz &&
    scp -q $T/E41/setup_e41.sh $vm:setup_e41.sh &&
    ssh $vm 'bash setup_e41.sh' > $T/E41/logs/setup_$vm.log 2>&1
    echo "exit $?" >> $T/E41/logs/setup_$vm.log
  ) &
done
wait
