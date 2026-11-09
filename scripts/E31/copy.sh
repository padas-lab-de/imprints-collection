set -e
D=${D:-/home/dinzinger/GitHub/imprints-collection-e35/datasets/E31/r3}
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp}
mkdir -p $D/E31_out $D/E40_out $D/E40_scan_new $D/E31_in_new
cp $T/E31/r3/out/* $D/E31_out/
cp $T/E40/r3/out/* $T/E40/r3/targets_raw.tsv $D/E40_out/
cp $T/E40/r3/scan/lorbeer_E34r3_*.scan.tsv $D/E40_scan_new/
cp $T/E31/r3/in/lorbeer_E34r3_*.tsv $T/E31/r3/in/manifest.tsv $D/E31_in_new/
(cd $T/E31/r3/out && sha256sum *; cd $T/E40/r3/out && sha256sum *; cd $T/E40/r3 && sha256sum targets_raw.tsv) > /tmp/a.sha
(cd $D/E31_out && sha256sum *; cd $D/E40_out && sha256sum filter_by_source.tsv flagged_sites.tsv targets_raw.tsv) > /tmp/b.sha
diff /tmp/a.sha /tmp/b.sha && echo MATCH
cat /tmp/b.sha
