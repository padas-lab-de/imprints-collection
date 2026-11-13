"""Load the frozen E49/E50 scorer modules by file path (``scripts/`` is not a package).

The topic tree, the level-majority vote and the address field matcher are reused, not copied:
- ``scripts/E49/tree.py`` (via ``ic.gold.annotate.topics``, module name ``_e49_tree``)
- ``scripts/E49/vote.py`` (``level_majority``)
- ``scripts/E50/addr_score.py`` (``to_record``, ``norm``, ``field_eq``)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ic.gold.annotate import topics as _topics

_REPO = Path(__file__).resolve().parents[3]


def _script(rel: str) -> Path:
    p = _REPO / rel
    return p if p.is_file() else Path(rel)


def _load(name: str, rel: str):
    if name in sys.modules:
        return sys.modules[name]
    path = list(sys.path)
    spec = importlib.util.spec_from_file_location(name, _script(rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = path  # vote.py inserts scripts/E49 into sys.path; undo that
    return mod


def tree_module():
    return _topics._tree_module()


def schema_key(schema: str) -> str:
    """'poi', 'poi3', 'poi_v3' -> 'poi'; 'wz', 'wz2025' -> 'wz'."""
    s = (schema or "").lower()
    if s.startswith("poi"):
        return "poi"
    if s.startswith("wz"):
        return "wz"
    raise KeyError(schema)


def get_tree(schema: str):
    return _topics.get_tree(schema_key(schema))


def vote():
    return _load("_e49_vote", "scripts/E49/vote.py")


def addr():
    return _load("_e50_addr_score", "scripts/E50/addr_score.py")
