echo "== $(hostname)"
for f in $HOME/GitHub/imprints-collection*/datasets/E22/snap2/*rest*; do [ -e "$f" ] && { echo "$f"; sha256sum "$f" | cut -c1-16; wc -l < "$f"; }; done
for d in $HOME/GitHub/imprints-collection*/datasets/E22/depth2P; do [ -e "$d" ] && { du -sh "$d"; ls "$d" | head -5; }; done
df -h $HOME | tail -1; free -g | sed -n 2p
ps -u $USER -o pid,args | grep -E "run.sh|main\(\) fetch" | grep -v grep | cut -c1-100
