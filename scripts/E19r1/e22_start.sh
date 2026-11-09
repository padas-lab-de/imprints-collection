# usage: bash -s <repo dir under ~> <python (abs, or rel to repo)> <run.sh rel to repo> FIRST LAST STEP
R=$HOME/$1; P=$2; [ "${P#/}" = "$P" ] && P=$R/$P
RUNSH=$R/$3; FIRST=$4; LAST=$5; STEP=$6
LIST=$R/datasets/E22/round1_frontier_A.txt; OUT=$R/datasets/E22/depth1A
cd "$R" || exit 1
echo "dcd5f325be381bb7c3fdca897f1f067f4715f46e505c280fe93d65c719ca92b4  $LIST" | sha256sum -c - || exit 1
[ -x "$P" ] || { echo "no python $P"; exit 1; }
pgrep -af "round1_frontier_A" | grep -v pgrep && { echo "already running"; exit 1; }
mkdir -p results/E22/logs
echo "$(date -u +%FT%TZ) E22 depth-1 frontier A: batches $FIRST-$LAST STEP $STEP on $(hostname)" >> results/E22/logs/driver.log
setsid nohup env ROOT="$R" PY="$P" STEP="$STEP" bash "$RUNSH" "$LIST" "$OUT" "$FIRST" "$LAST" >> results/E22/logs/driver.log 2>&1 < /dev/null &
sleep 20
tail -2 results/E22/logs/driver.log
pgrep -af "fetch $LIST" | cut -c1-60
ls "$OUT"
