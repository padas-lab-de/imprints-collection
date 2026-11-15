"""Gold-set build: shared helpers (host normalisation, frame permutation, paths). Stdlib only.

Host key (docs/gold_set_design.md, frame): lower case, no scheme/path/port, no trailing dot, no leading "www.".
Both variants (x.de, www.x.de) map to the same key, so excluding a key excludes both.

Frame order: every frame site gets the rank key sha256(f"{seed}:{key}"). Sorting by this key is a seeded random
permutation of the frame. S1 = the first n1 sites. Any prefix of a uniform random permutation is a simple random
sample, so a longer prefix extends S1 and stays an SRS. The key of a site does not depend on the other sites, so
removing sites (sites dropped by a later site list) does not move the others.

Data folder: $IC_GOLD_DATA, default <repo root>/datasets/goldset.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("IC_GOLD_DATA") or ROOT / "datasets" / "goldset")
SEED = 20261112
N1 = 20_000


def norm_host(h: str) -> str:
    """Host or URL -> match key."""
    h = (h or "").strip().lower()
    if not h:
        return ""
    if "://" in h:
        h = urlsplit(h).netloc
    else:
        h = h.split("/", 1)[0]
    h = h.rsplit("@", 1)[-1].split(":", 1)[0].rstrip(".")
    return h[4:] if h.startswith("www.") else h


def keys(hosts: Iterable[str]) -> set[str]:
    return {k for k in (norm_host(h) for h in hosts) if k}


def rank_key(host: str, seed: int = SEED) -> str:
    return hashlib.sha256(f"{seed}:{norm_host(host)}".encode()).hexdigest()


def permute(hosts: Iterable[str], seed: int = SEED) -> list[str]:
    """Seeded random permutation (sort by rank key; host as tie-break, never needed in practice)."""
    return sorted(hosts, key=lambda h: (rank_key(h, seed), h))


def exclude(frame: Iterable[str], excl_keys: set[str]) -> list[str]:
    return [h for h in frame if norm_host(h) not in excl_keys]


def sha256_file(p: Path) -> str:
    d = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            d.update(b)
    return d.hexdigest()
