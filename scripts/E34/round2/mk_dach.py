import hashlib, random
from pathlib import Path

import os  # D47: path constants below can be overridden by env
R = os.environ.get("R", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34/round2/")
DACH = {"de", "at", "ch", "li"}
pil = {l.strip() for l in open(R + "pilot_r2.txt") if l.strip()}
rest = sorted({l.strip() for l in open(R + "frontier_r2.txt") if l.strip()} - pil)
dach = [h for h in rest if h.rsplit(".", 1)[-1] in DACH]
random.seed(38)
random.shuffle(dach)
data = "".join(h + "\n" for h in dach).encode()
Path(R + "e34r2_dach_rest.txt").write_bytes(data)
dg = hashlib.sha256(data).hexdigest()
Path(R + "e34r2_dach_rest.txt.sha256").write_text(f"{dg}  e34r2_dach_rest.txt\n")
print("rest", len(rest), "dach", len(dach), "pilot overlap", len(set(dach) & pil), "sha256", dg)
