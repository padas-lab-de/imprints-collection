# run on VM: stop.sh <run.sh pid> <fetch pid>
R=$1; F=$2
ps -o args= -p $R | grep -q 'scripts/E19/run.sh' || { echo "pid $R is not E19 run.sh"; exit 1; }
ps -o args= -p $F | grep -q 'main() fetch' || { echo "pid $F is not ic fetch"; exit 1; }
kill $R; sleep 1; kill $F
for i in 1 2 3 4 5 6; do ps -p $F >/dev/null || break; sleep 5; done
ps -p $R,$F -o pid=,args= | cut -c1-80
echo "$(hostname) stopped $(date -u +%FT%TZ)"
