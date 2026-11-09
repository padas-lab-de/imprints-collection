import glob
import os  # D47: path constants below can be overridden by env
M = os.environ.get("M", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/merge/in")
out = open("/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/e22_hosts.txt", "w")
n = 0
for d in ("E22d1A", "E22d1B", "E22d2P", "E22d2R"):
    for p in glob.glob(f"{M}/{d}/**/fetch_status_batch*.tsv", recursive=True):
        for line in open(p, encoding="utf-8", errors="replace"):
            h = line.split("\t", 1)[0].strip().lower()
            if h and h != "host":
                out.write(h + "\n"); n += 1
print(n)
