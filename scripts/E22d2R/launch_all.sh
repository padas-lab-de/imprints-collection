D=${D:-/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d29}
SHA=e67ee0b9e48cede9ba88edcc0395e47f94835e5bb37f9e56a083993eee7e8417
FSHA=c34d09b29442e39bb7e956a0024bb769bcefbe816f53e9b9c30e4f32bf5a0ebc
PYDEF=${PYDEF:-/home/dinzinger/GitHub/imprints-collection/.venv/bin/python}
PYE22=${PYE22:-/home/dinzinger/GitHub/imprints-collection-e22/.venv/bin/python}
PYASPE=${PYASPE:-/home/dinzinger/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/bin/python}
go() { # vm python first last step
  v=$1; echo "== $v"
  scp -q $D/d29.tar $v:stage_d29.tar && scp -q $D/round2_frontier_rest.txt $v:stage_rest.txt
  ssh $v bash -s $v $SHA $FSHA $2 $3 $4 $5 < $D/deploy.sh
}
go aspe $PYASPE 0 9 3
go apfel $PYDEF 10 19 3
go mispel $PYDEF 20 29 3
go abelie $PYDEF 40 49 3
go aralie $PYE22 50 59 1
go akazie $PYE22 60 68 1
echo "== lorbeer"
cp $D/d29.tar ~/stage_d29.tar && cp $D/round2_frontier_rest.txt ~/stage_rest.txt
bash $D/deploy.sh lorbeer $SHA $FSHA $PYDEF 30 39 3
