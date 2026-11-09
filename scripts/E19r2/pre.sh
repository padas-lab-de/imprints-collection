R=$HOME/GitHub/imprints-collection-d30
echo "== $(hostname)"
if [ -e $R ]; then echo "d30 exists"; sha256sum $R/src/ic/cli/fetch.py; ls $R/results/E19/logs/; else echo "no d30"; fi
free -g | sed -n 2p; df -h $HOME | tail -1
ps -u $USER -o pid,args | grep -E "run.sh|ic.ic|main\(\) fetch" | grep -v grep | cut -c1-120
