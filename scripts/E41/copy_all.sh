#!/bin/bash
# Copy E41 results from the 4 VMs to lorbeer e35 datasets/E41/<vm>/ and verify sizes and file counts.
D=/home/dinzinger/GitHub/imprints-collection-e35/datasets/E41
mkdir -p $D
for vm in apfel aspe abelie mispel; do
  ssh -o BatchMode=yes $vm 'pgrep -u $USER -f "datasets/E41/" >/dev/null && echo "'$vm' E41 FETCH STILL RUNNING"; cd ~/GitHub/imprints-collection-e41 && echo "'$vm' src $(du -s --apparent-size datasets/E41 | cut -f1) files $(find datasets/E41 -type f | wc -l)"'
  rsync -a $vm:GitHub/imprints-collection-e41/datasets/E41/ $D/$vm/ || echo "$vm RSYNC FAILED"
  rsync -a $vm:GitHub/imprints-collection-e41/results/E41/ $D/$vm/results_E41/ 2>/dev/null
  echo "$vm dst $(du -s --apparent-size --exclude=results_E41 $D/$vm | cut -f1) files $(find $D/$vm -type f -not -path '*results_E41*' | wc -l)"
done
