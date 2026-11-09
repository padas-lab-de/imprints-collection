D=${D:-$HOME/GitHub/imprints-collection-e34r3}
if [ -e $D/datasets/E34r4/pilot ]; then echo "ABORT pilot dir exists"; exit 1; fi
mkdir -p $D/datasets/E34r4 $D/results/E34r4/logs
mv $HOME/pilot_r4.txt $D/datasets/E34r4/pilot_r4.txt
mv $HOME/e34r4_run.sh $D/results/E34r4/e34r4_run.sh
sha256sum $D/datasets/E34r4/pilot_r4.txt; wc -l < $D/datasets/E34r4/pilot_r4.txt
cd $D && $D/.venv/bin/python -c "from ic.cli.fetch import HEADERS; print(HEADERS.get('User-Agent'))"
avail=$(free -g | awk 'NR==2{print $7}'); echo "avail GB $avail"
if [ "$avail" -lt 8 ]; then echo ABORT; exit 1; fi
nohup setsid bash $D/results/E34r4/e34r4_run.sh > $D/results/E34r4/logs/driver.log 2>&1 < /dev/null &
echo "DRIVER PGID $!"
sleep 45
date -u +%FT%TZ
ps -u $USER -o pid,args | grep "[E]34r4/pilot_r4" | cut -c1-200
cat $D/results/E34r4/logs/driver.log
