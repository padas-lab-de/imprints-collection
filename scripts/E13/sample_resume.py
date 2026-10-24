"""E13 resume test: 3,000 random seeds outside the E4 random 20k and the E13 100k."""

import gzip
import random

ROOT = "/home/dinzinger/GitHub/imprints-collection"
with gzip.open(f"{ROOT}/seed_hosts.txt.gz", "rt") as f:
    seeds = sorted({line.strip() for line in f if line.strip()})
used = set()
for p in ("datasets/E4/random20k_seed_hosts.txt", "datasets/E13/random100k_seed_hosts.txt"):
    with open(f"{ROOT}/{p}") as f:
        used |= {line.strip() for line in f}
pool = [s for s in seeds if s not in used]
random.seed(20261024 + 1)
sample = random.sample(pool, 3000)
with open(f"{ROOT}/datasets/E13/resume3k_seed_hosts.txt", "w") as f:
    f.write("\n".join(sample) + "\n")
print(len(seeds), len(pool), len(sample))
