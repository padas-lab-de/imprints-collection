"""Draw the E15 sample: 25,000 random seed hosts, disjoint from E4/E9, E13 and E12 samples."""

import gzip
import os
import random

ROOT = "/home/dinzinger/GitHub/imprints-collection"
SEED = 20261025

with gzip.open(f"{ROOT}/seed_hosts.txt.gz", "rt", encoding="UTF-8") as f:
    hosts = sorted({l.strip() for l in f if l.strip()})
exclude = set()
for p in [
    "datasets/E4/random20k_seed_hosts.txt",
    "datasets/E13/random100k_seed_hosts.txt",
    "datasets/E13/resume3k_seed_hosts.txt",
    "datasets/E12/hosts.txt",
]:
    if os.path.exists(f"{ROOT}/{p}"):
        with open(f"{ROOT}/{p}", encoding="UTF-8") as f:
            exclude |= {l.strip() for l in f if l.strip()}
pool = [h for h in hosts if h not in exclude]
random.seed(SEED)
sample = random.sample(pool, 25_000)
os.makedirs(f"{ROOT}/datasets/E15", exist_ok=True)
with open(f"{ROOT}/datasets/E15/random25k_seed_hosts.txt", "w", encoding="UTF-8") as f:
    f.write("\n".join(sample) + "\n")
print(len(hosts), len(exclude), len(pool), len(sample))
