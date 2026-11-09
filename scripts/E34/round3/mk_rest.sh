cd /home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round3
grep -vxFf pilot_r3.txt frontier_r3.txt > e34r3_rest.txt
wc -l e34r3_rest.txt
sha256sum e34r3_rest.txt | tee e34r3_rest.txt.sha256
cat pilot_r3.txt e34r3_rest.txt | sort | uniq -d | wc -l
cat pilot_r3.txt e34r3_rest.txt | sort -u | cmp - frontier_r3.txt && echo UNION_OK
