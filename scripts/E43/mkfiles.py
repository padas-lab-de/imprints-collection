T = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp"
used = {l.strip() for l in open(T + "/E41/hplt_files_all.txt")}
allf = [f"deu_Latn/train-{i:05d}-of-04279.parquet" for i in range(4279)]
rest = [f for f in allf if f not in used]
print(len(used), len(rest))
open(T + "/E43/hplt_files_rest.txt", "w").write("\n".join(rest) + "\n")
