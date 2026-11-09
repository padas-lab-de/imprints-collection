L=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E37
PYD=/home/dinzinger/GitHub/imprints-collection/.venv/bin/python
PYA='$HOME/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python'
go() { v=$1; d=$2; f=$3; l=$4; py=$5
  scp -q $L/e37_rest.txt $v:e37_rest.txt
  echo "== $v"; ssh $v "DPID=$d FIRST=$f LAST=$l PY=$py bash -s" < $L/launch_e37.sh
}
go apfel 3341673 0 4 $PYD
go mispel 1840522 5 9 $PYD
go abelie 2752797 10 14 $PYD
go aspe 3604697 15 19 "$PYA"
