set -e
# usage (on VM): DPID=<E33 driver pid> FIRST=.. LAST=.. PY=.. bash -s < launch_e37.sh ; expects ~/e37_rest.txt
E=$HOME/GitHub/imprints-collection-e35
[ "$(sha256sum $E/src/ic/cli/fetch.py | cut -d' ' -f1)" = a9dc1dddce1af24adfeb30c451697695c60d2a23cbd144d7d567e9fd7692bbab ] || { echo FETCH_SHA_MISMATCH; exit 1; }
mkdir -p $E/datasets/E37
[ -f $E/datasets/E37/e37_rest.txt ] || cp $HOME/e37_rest.txt $E/datasets/E37/e37_rest.txt
[ "$(sha256sum $E/datasets/E37/e37_rest.txt | cut -d' ' -f1)" = 61c54c82d924c37ea0bf0df94b77afc6a13f41bd7fae21526b1cd9de5730c408 ] || { echo LIST_SHA_MISMATCH; exit 1; }
[ -x "$PY" ] || { echo NO_PY; exit 1; }
tr '\0' ' ' < /proc/$DPID/cmdline | grep -q "E33/e33_rest.txt" || { echo DPID_NOT_E33_DRIVER; exit 1; }
pgrep -f "E37/e37_rest.txt" && { echo E37_ALREADY_QUEUED; exit 1; }
mkdir -p $E/results/E37/root/results $E/results/E37/logs $E/datasets/E37/full
cd $E/results/E37/root
for x in src topics prompts scripts; do ln -sfn $E/$x $x; done
ln -sfn $E/results/E37 results/E22
W=$E/results/E37/logs/wait_$FIRST-$LAST.sh
cat > $W <<EOF
while kill -0 $DPID 2>/dev/null; do sleep 300; done
echo "\$(date -u +%FT%TZ) E33 driver $DPID gone, starting E37"
cd $E/results/E37/root
export ROOT=$E/results/E37/root PY=$PY STEP=1 SKIPGROUPS="v4:23.227.38"
exec bash $E/scripts/E22/run.sh $E/datasets/E37/e37_rest.txt $E/datasets/E37/full $FIRST $LAST
EOF
nohup setsid bash $W "E37/e37_rest.txt" > $E/results/E37/logs/driver_$FIRST-$LAST.log 2>&1 < /dev/null &
echo queued waiter $! behind E33 driver $DPID at $(date -u +%FT%TZ)
