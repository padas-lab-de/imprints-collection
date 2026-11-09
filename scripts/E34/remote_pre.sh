D=$HOME/GitHub/imprints-collection-d29
free -g | head -2
sha256sum $D/src/ic/cli/fetch.py
for pid in $(pgrep -f "ic.*fetch|ic.py.*fetch|-m ic"); do echo "PID $pid: $(tr '\0' ' ' < /proc/$pid/cmdline | cut -c1-300)"; done
ls $D/results/E34 $D/datasets/E34 2>&1 | head
for dd in E26/full E29/full E25/pilot E27/p1 E27/p2 E27/p3; do
  if test -d $D/datasets/$dd; then echo "$dd rows $(tail -q -n +2 $D/datasets/$dd/fetch_status_batch*.tsv 2>/dev/null | wc -l)"; fi
done
