"""Topic trees for the labelling tool: POI v3 and WZ 2025 (D51 B, E49).

The tree logic is not copied. ``scripts/E49/tree.py`` is loaded by path (``scripts/`` is not a
package), so the annotators and the E49 scorer read the schemas the same way.
Node ids: POI v3 = the ``id`` slug, WZ = the ``code``.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unicodedata
from pathlib import Path

SCHEMAS = {"poi": "topics/poi_v3.jsonl", "wz": "topics/wz2025.jsonl"}
CONFIDENCE = ("high", "medium", "low")
MAX_EXTRA = 2

_REPO = Path(__file__).resolve().parents[4]
_trees: dict = {}
_index: dict = {}


def _tree_module():
    name = "_e49_tree"
    if name in sys.modules:
        return sys.modules[name]
    p = _REPO / "scripts" / "E49" / "tree.py"
    if not p.is_file():
        p = Path("scripts/E49/tree.py")
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


def _schema_path(schema: str) -> Path:
    p = _REPO / SCHEMAS[schema]
    return p if p.is_file() else Path(SCHEMAS[schema])


def get_tree(schema: str):
    if schema not in SCHEMAS:
        raise KeyError(schema)
    if schema not in _trees:
        _trees[schema] = _tree_module().load_tree(_schema_path(schema), name=schema)
    return _trees[schema]


def fold(s: str) -> str:
    """Lower-case, no diacritics, ss for sharp s, ae/oe/ue folded: 'Bäckerei' ~ 'baeckerei'."""
    s = unicodedata.normalize("NFKD", (s or "").casefold().replace("ß", "ss"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[aou]e", lambda m: m.group(0)[0], s)


def _entries(schema: str) -> list:
    if schema not in _index:
        t = get_tree(schema)
        rows = []
        for n in t.nodes.values():
            title, kws = fold(n.title), [fold(k) for k in n.keywords]
            rows.append((n, fold(n.id) if t.coded else "", title, " ".join(kws)))
        _index[schema] = rows
    return _index[schema]


def describe(schema: str, node_id: str) -> dict:
    t = get_tree(schema)
    n = t[node_id]
    return {
        "id": n.id,
        "title": n.title,
        "de": n.keywords[0] if (schema == "poi" and n.keywords) else "",
        "level": n.level,
        "leaf": not n.children,
        "path": [{"id": i, "title": t[i].title} for i in n.path],
    }


def search(schema: str, q: str, limit: int = 20) -> list[dict]:
    """Nodes whose name (POI: English + German; WZ: code + German title) matches ``q``,
    best first. Every word of the query must match. Each hit carries its full path."""
    words = fold(q).split()
    if not words:
        return []
    scored = []
    full = " ".join(words)
    for n, code, title, kw in _entries(schema):
        hay = f"{code} {title} {kw}"
        if not all(w in hay for w in words):
            continue
        if code and code.startswith(full):
            s = 0
        elif title == full or kw == full:
            s = 1
        elif title.startswith(full) or kw.startswith(full):
            s = 2
        elif all(re.search(r"\b" + re.escape(w), f"{title} {kw}") for w in words):
            s = 3
        else:
            s = 4
        scored.append((s, n.level, len(title), n.id, n))
    scored.sort(key=lambda r: r[:4])
    return [describe(schema, r[4].id) for r in scored[: max(1, min(limit, 50))]]


def _live(label: dict) -> bool:
    return label.get("site_status") in ("live", "redirect_other_domain")


def validate_schema_labels(label: dict) -> list[str]:
    """Check ``label['topic_labels']``: ids exist, at most 2 extras, no duplicates,
    R5 (an extra is not the main and not an ancestor of the main), confidence, online_only.
    Labels with ``schema_version`` 2 must carry both schemas when the site is live."""
    must = label.get("schema_version") == 2 and _live(label)
    tl = label.get("topic_labels")
    if tl is None:
        return ["topic_labels required (schema_version 2)"] if must else []
    if not isinstance(tl, dict):
        return ["topic_labels must be an object"]
    errs: list[str] = []
    for k in tl:
        if k not in SCHEMAS:
            errs.append(f"topic_labels: unknown schema {k!r}")
    for sch in SCHEMAS:
        pre = f"topic {sch}: "
        d = tl.get(sch)
        if d is None:
            if must:
                errs.append(pre + "missing")
            continue
        if not isinstance(d, dict):
            errs.append(pre + "not an object")
            continue
        tree = get_tree(sch)
        main, extra = d.get("main"), d.get("extra", [])
        if main is not None and main not in tree.nodes:
            errs.append(pre + f"unknown main id {main!r}")
        if not isinstance(extra, list):
            errs.append(pre + "extra must be a list")
            extra = []
        if len(extra) > MAX_EXTRA:
            errs.append(pre + f"at most {MAX_EXTRA} extra labels")
        if main is None and extra:
            errs.append(pre + "extra labels need a main label")
        if main is None and not str(d.get("note") or "").strip():
            errs.append(pre + "no main label: say why in the note")
        for i, x in enumerate(extra):
            if x not in tree.nodes:
                errs.append(pre + f"unknown extra id {x!r}")
            elif main in tree.nodes and x in tree[main].path:
                errs.append(pre + f"extra {x!r} is the main label or an ancestor of it (R5)")
            elif x in extra[:i]:
                errs.append(pre + f"extra {x!r} listed twice")
        if d.get("confidence") not in CONFIDENCE:
            errs.append(pre + f"confidence must be one of {CONFIDENCE}")
        if sch == "poi" and not isinstance(d.get("online_only"), bool):
            errs.append(pre + "online_only must be true or false")
    return errs


def normalise_schema_labels(tl):
    if not isinstance(tl, dict):
        return tl
    out = {}
    for sch, d in tl.items():
        if not isinstance(d, dict) or sch not in SCHEMAS:
            out[sch] = d
            continue
        main = d.get("main")
        main = main.strip() if isinstance(main, str) and main.strip() else None
        extra = []
        for x in d.get("extra") or []:
            x = x.strip() if isinstance(x, str) else x
            if x and x not in extra:
                extra.append(x)
        r = {"main": main, "extra": extra, "confidence": d.get("confidence"),
             "note": str(d.get("note") or "").strip()}
        if sch == "poi":
            r["online_only"] = d.get("online_only", False)
        out[sch] = r
    return out
