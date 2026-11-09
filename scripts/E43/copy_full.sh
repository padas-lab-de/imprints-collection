#!/bin/bash
# Copy the finished E43 rest crawl to the durable e35 datasets folder and verify.
S=${S:-/home/dinzinger/GitHub/imprints-collection-e43/datasets/E43}
D=${D:-/home/dinzinger/GitHub/imprints-collection-e35/datasets/E43}
rsync -a $S/full $S/rest_E43.txt $D/ || exit 1
cd $D && sha256sum rest_E43.txt > rest_E43.txt.sha256 && cut -c1-16 rest_E43.txt.sha256
du -s --apparent-size $S/full $D/full
echo "files src $(ls $S/full | wc -l) dst $(ls $D/full | wc -l)"
