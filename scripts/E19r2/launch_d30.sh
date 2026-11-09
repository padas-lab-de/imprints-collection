D=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/d30
for v in abelie apfel; do
  echo "== $v"
  sha=$(grep " round2c_$v.txt" $D/sha.txt | cut -d' ' -f1)
  scp -q $D/d30.tar $v:stage_d30.tar && scp -q $D/round2c_$v.txt $v:stage_round2c_$v.txt
  ssh $v bash -s $v $sha < $D/deploy.sh
done
