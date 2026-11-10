"""E49: vote over several predictions of the same host (self-consistency samples or several models).

level_majority: go down the tree while one child prefix has a strict majority of ALL voters (abstentions
count as voters), so disagreement on a deep level makes the vote stop higher.
plurality: the most frequent main node (ties: first voter's order).
Stdlib only.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tree import Tree  # noqa: E402


def level_majority(tree: Tree, mains: list[str | None]) -> str | None:
    paths = [tree.canonical_path(m) if m in tree else [] for m in mains]
    n = len(paths)
    node = None
    for L in range(1, tree.max_level + 1):
        c = Counter(p[L - 1] for p in paths if len(p) >= L and (node is None or p[L - 2] == node))
        if not c:
            break
        best, k = c.most_common(1)[0]
        if 2 * k <= n:
            break
        node = best
    return node


def plurality(tree: Tree, mains: list[str | None]) -> str | None:
    c = Counter(m for m in mains if m in tree)
    if not c:
        return None
    top = max(c.values())
    return next(m for m in mains if m in tree and c[m] == top)


VOTES = {"level_majority": level_majority, "plurality": plurality}
