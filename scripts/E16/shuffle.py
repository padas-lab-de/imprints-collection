"""Shuffle the full seed list (fixed seed) so every 25k batch is a random sample."""

import gzip
import random

ROOT = "/home/dinzinger/GitHub/imprints-collection"

with gzip.open(f"{ROOT}/seed_hosts.txt.gz", "rt", encoding="UTF-8") as f:
    hosts = sorted({l.strip() for l in f if l.strip()})
random.seed(20261024)
random.shuffle(hosts)
with open(f"{ROOT}/datasets/E16/seed_hosts_shuffled.txt", "w", encoding="UTF-8") as f:
    f.write("\n".join(hosts) + "\n")
print(len(hosts))
