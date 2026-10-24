"""Draw the E13 dry-run sample: 100,000 random seed hosts, excluding the E4/E9 random 20k."""

import gzip
import os
import random

ROOT = "/home/dinzinger/GitHub/imprints-collection"
SEED = 20261024

with gzip.open(f"{ROOT}/seed_hosts.txt.gz", "rt", encoding="UTF-8") as f:
    hosts = sorted({l.strip() for l in f if l.strip()})
with open(f"{ROOT}/datasets/E4/random20k_seed_hosts.txt", encoding="UTF-8") as f:
    exclude = {l.strip() for l in f if l.strip()}
pool = [h for h in hosts if h not in exclude]
random.seed(SEED)
sample = random.sample(pool, 100_000)
os.makedirs(f"{ROOT}/datasets/E13", exist_ok=True)
with open(f"{ROOT}/datasets/E13/random100k_seed_hosts.txt", "w", encoding="UTF-8") as f:
    f.write("\n".join(sample) + "\n")
print(len(hosts), len(exclude), len(pool), len(sample))
