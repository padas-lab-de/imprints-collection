T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp}
PYD=${PYD:-/home/dinzinger/GitHub/imprints-collection/.venv/bin/python}
PYA=${PYA:-/home/dinzinger/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
go() { v=$1; f=$2; l=$3; py=$4
  echo "===== $v $f-$l"
  scp -q $T/E36/e35_tree.tar.gz $T/E33/e33_rest.txt $v:~/ || { echo SCP_FAIL; return; }
  ssh $v "FIRST=$f LAST=$l PY=$py bash -s" < $T/E36/launch_e33.sh
}
go apfel 0 24 $PYD
go mispel 25 48 $PYD
go abelie 49 72 $PYD
go aspe 73 97 $PYA
