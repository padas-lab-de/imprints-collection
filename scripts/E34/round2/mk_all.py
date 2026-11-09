import collections, hashlib, random
from pathlib import Path

R = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2/"
pil = {l.strip() for l in open(R + "pilot_r2.txt") if l.strip()}
fr = {l.strip() for l in open(R + "frontier_r2.txt") if l.strip()}
rest = sorted(fr - pil)
random.seed(38)
random.shuffle(rest)
data = "".join(h + "\n" for h in rest).encode()
Path(R + "e34r2_rest.txt").write_bytes(data)
dg = hashlib.sha256(data).hexdigest()
Path(R + "e34r2_rest.txt.sha256").write_text(f"{dg}  e34r2_rest.txt\n")
print("frontier", len(fr), "pilot", len(pil), "rest", len(rest), "pilot overlap", len(set(rest) & pil), "batches", -(-len(rest) // 25000), "sha256", dg)
dach = {"de", "at", "ch", "li"}
for b in range(0, len(rest), 25000):
    c = collections.Counter("dach" if h.rsplit(".", 1)[-1] in dach else "other" for h in rest[b : b + 25000])
    print("batch", b // 25000, dict(c))
