#!/bin/bash
set -e
mkdir -p /home/dinzinger/GitHub/imprints-collection-e35/datasets/E44/full
rsync -a /home/dinzinger/GitHub/imprints-collection-e43/datasets/E44/full/ /home/dinzinger/GitHub/imprints-collection-e35/datasets/E44/full/
cp /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E44/rest_E44.txt* /home/dinzinger/GitHub/imprints-collection-e35/datasets/E44/
ls -la /home/dinzinger/GitHub/imprints-collection-e35/datasets/E44/full | head
