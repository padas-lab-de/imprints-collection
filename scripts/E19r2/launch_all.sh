D=${D:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d31}
T=${T:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d30/d30.tar}
PYDEF=${PYDEF:-/home/dinzinger/GitHub/imprints-collection/.venv/bin/python}
PYE22=${PYE22:-/home/dinzinger/GitHub/imprints-collection-e22/.venv/bin/python}
PYASPE=${PYASPE:-/home/dinzinger/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
sha() { grep " $1\$" $D/sha.txt | cut -d' ' -f1; }
go() { # vm python fresh(1/0)
  v=$1; echo "== $v"
  [ "$3" = 1 ] && scp -q $T $v:stage_d30.tar
  scp -q $D/round2d_$v.txt $v:stage_round2d_$v.txt
  ssh $v bash -s $v $(sha round2d_$v.txt) $2 < $D/deploy.sh
}
go aspe $PYASPE 1
go apfel $PYDEF 0
go mispel $PYDEF 1
go akazie $PYE22 1
go aralie $PYE22 1
go abelie $PYDEF 0
echo "== lorbeer"
cp $T ~/stage_d30.tar && cp $D/round2d_lorbeer.txt ~/stage_round2d_lorbeer.txt
bash $D/deploy.sh lorbeer $(sha round2d_lorbeer.txt) $PYDEF
echo "== mispel pilot"
scp -q $D/shopify_pilot.txt mispel:stage_shopify_pilot.txt
ssh mispel bash -s $(sha shopify_pilot.txt) $PYDEF < $D/pilot.sh
