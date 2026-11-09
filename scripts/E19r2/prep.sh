D=${D:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d30}
mkdir -p $D/akazie $D/mispel
scp -q akazie:GitHub/imprints-collection-e22/datasets/E19/round2b_akazie/fetch_status_batch\*.tsv $D/akazie/
scp -q mispel:GitHub/imprints-collection/datasets/E19/round2b_mispel/fetch_status_batch\*.tsv $D/mispel/
ls -la $D/akazie $D/mispel
for v in abelie apfel; do
  echo "== $v"
  ssh $v 'free -g | sed -n 2p; df -h ~ | tail -1; pgrep -u $USER -fa "ic.ic|run.sh" | cut -c1-120; ls ~/GitHub; ls ~/GitHub/imprints-collection/results/E19/logs 2>/dev/null; ls ~/GitHub/imprints-collection/datasets/E19 2>/dev/null; cd ~/GitHub/imprints-collection && git log --oneline -1 && git remote -v | head -1; ls .venv/bin/python'
done
