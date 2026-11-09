# usage: bash -s <shard> <e16_driver_pid> <python>   (run in the VM's repo; shard file already copied)
S=$1; P=$2; PYB=$3
R=$HOME/GitHub/imprints-collection
cd "$R" || exit 1
sha256sum datasets/E19/reshard/remaining_shard$S.txt
grep "remaining_shard$S.txt" datasets/E19/reshard/sha256.txt
ps -o pid=,args= -p "$P" | cut -c1-60
mkdir -p results/E19/logs
L=results/E19/logs/driver_round1_s$S.log
echo "$(date -u +%FT%TZ) D25 B: shard $S waits for E16 driver pid $P" >> "$L"
setsid nohup bash -c "while kill -0 $P 2>/dev/null; do sleep 60; done; echo \"\$(date -u +%FT%TZ) handover: E16 done, start E19 shard $S\"; OUT=$R/datasets/E19/round1_s$S PY=$PYB exec bash scripts/E19/run.sh $R/datasets/E19/reshard/remaining_shard$S.txt" >> "$L" 2>&1 < /dev/null &
sleep 2
pgrep -af "kill -0 $P" | cut -c1-80
