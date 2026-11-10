"""E49: generic topic-schema tree, loaded from either schema format (a schema is a plug-in).

Formats (one JSON object per line):
- POI  (topics/poi_v2.jsonl):  {"name", "parent"}; a root has parent == name (or empty parent).
- POI3 (topics/poi_v3.jsonl):  {"id", "name", "parent", "fsq_ids", "de"}; a root has parent == id. Any file
  whose rows carry "id" is read this way: node id = "id", title = "name" (English), keywords = German name(s).
- WZ   (topics/wz2025.jsonl):  {"code", "level", "title", "parent", "keywords", ...}; a root has an empty parent.
  Any file whose rows carry "code" is read this way.

Node id: POI uses the name; a name that occurs under two different parents gets "name (parent)"
(Karaoke-Bar, Rettungsdienst); exact duplicate rows (Rathaus) are merged. WZ uses the code.
Level: 1 = root, computed from the parent chain (the "level" field of WZ is kept as level_name).
Stdlib only.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

SCHEMAS = {"poi": "topics/poi_v2.jsonl", "poi3": "topics/poi_v3.jsonl", "wz": "topics/wz2025.jsonl"}


@dataclass
class Node:
    id: str
    title: str
    parent: str | None
    keywords: list[str] = field(default_factory=list)
    level_name: str = ""
    includes: str = ""
    desc: str = ""  # optional generated description (results/E49/node_desc/<schema>.jsonl)
    children: list[str] = field(default_factory=list)
    level: int = 0
    path: list[str] = field(default_factory=list)  # ids root..self


class Tree:
    def __init__(self, nodes: list[Node], name: str = "", coded: bool = False, bilingual: bool = False):
        self.name = name
        self.bilingual = bilingual  # keywords hold the German node names (id-format schemas, poi3)
        self.coded = coded  # ids are codes (WZ), not names (POI)
        self.nodes: dict[str, Node] = {}
        for n in nodes:
            if n.id in self.nodes:
                raise ValueError(f"duplicate node id {n.id!r}")
            self.nodes[n.id] = n
        for n in nodes:
            if n.parent is not None:
                if n.parent not in self.nodes:
                    raise ValueError(f"node {n.id!r}: unknown parent {n.parent!r}")
                self.nodes[n.parent].children.append(n.id)
        self.roots = [n.id for n in nodes if n.parent is None]
        for n in nodes:
            p, seen = [], set()
            cur: str | None = n.id
            while cur is not None:
                if cur in seen:
                    raise ValueError(f"cycle at {cur!r}")
                seen.add(cur)
                p.append(cur)
                cur = self.nodes[cur].parent
            n.path = p[::-1]
            n.level = len(n.path)
        self.max_level = max(n.level for n in nodes)
        # lookup by id, by title and case-insensitive (for parsing model answers)
        self._lookup: dict[str, str] = {}
        titles = Counter(n.title.lower() for n in nodes)
        for n in nodes:
            if titles[n.title.lower()] == 1:
                self._lookup.setdefault(n.title.lower(), n.id)
        for n in nodes:
            self._lookup[n.id.lower()] = n.id

    def __len__(self) -> int:
        return len(self.nodes)

    def __getitem__(self, i: str) -> Node:
        return self.nodes[i]

    def __contains__(self, i) -> bool:
        return i in self.nodes

    def at_level(self, level: int) -> list[str]:
        return [i for i, n in self.nodes.items() if n.level == level]

    def up_to(self, depth: int) -> list[str]:
        """Nodes with level <= depth, in file order."""
        return [i for i, n in self.nodes.items() if n.level <= depth]

    def path(self, i: str | None) -> list[str]:
        return list(self.nodes[i].path) if i in self.nodes else []

    def truncate(self, i: str, depth: int) -> str:
        p = self.nodes[i].path
        return p[min(depth, len(p)) - 1]

    def title_of(self, i: str, lang: str = "en") -> str:
        """Node title; lang "both" gives "English (Deutsch)" for nodes of a schema with German names in
        `keywords` (poi3; merged nodes show the first two German names); unchanged for other nodes."""
        n = self.nodes[i]
        if lang != "both" or not n.keywords or not self.bilingual:
            return n.title
        de = [d for d in n.keywords[:2] if d and d.lower() != n.title.lower()]
        return f"{n.title} ({' / '.join(de)})" if de else n.title

    def path_titles(self, i: str, sep: str = " > ", lang: str = "en") -> str:
        return sep.join(self.title_of(j, lang) for j in self.nodes[i].path)

    def resolve(self, answer) -> tuple[str | None, str]:
        """Map a model answer to a node id. Returns (id or None, how): exact, ci, title, fuzzy, none."""
        if not isinstance(answer, str) or not answer.strip():
            return None, "none"
        a = answer.strip()
        # "[id] title" (the model copied the whole candidate line): take the bracketed id
        if a.startswith("[") and "]" in a:
            inner = a[1:a.index("]")].strip()
            if inner in self.nodes:
                return inner, "exact"
            if inner.lower() in self._lookup:
                return self._lookup[inner.lower()], "ci"
        a = a.strip("[]\"'").strip()
        if a in self.nodes:
            return a, "exact"
        if a.lower() in self._lookup:
            return self._lookup[a.lower()], "ci"
        # "Parent > Child" or "code title"
        last = a.split(">")[-1].strip()
        if last.lower() in self._lookup:
            return self._lookup[last.lower()], "title"
        first = a.split()[0] if a.split() else ""
        if first in self.nodes:
            return first, "title"
        import difflib

        m = difflib.get_close_matches(a.lower(), list(self._lookup), n=1, cutoff=0.88)
        if m:
            return self._lookup[m[0]], "fuzzy"
        return None, "none"

    def extend(self, i: str | None) -> str | None:
        """Walk down single-child chains (WZ 56.1 -> 56.11 -> 56.11.0): choosing the parent fixes the
        child, so the scorer compares these extended (canonical) nodes."""
        if i not in self.nodes:
            return None
        while len(self.nodes[i].children) == 1:
            i = self.nodes[i].children[0]
        return i

    def canonical_path(self, i: str | None) -> list[str]:
        return self.path(self.extend(i))

    def redundant(self, i: str) -> bool:
        """True if the node has exactly one child (the child stands for it in candidate lists)."""
        return len(self.nodes[i].children) == 1

    def candidates_up_to(self, depth: int) -> list[str]:
        """Nodes with level <= depth, without single-child nodes whose child is also listed."""
        return [i for i in self.up_to(depth) if not (self.redundant(i) and self.nodes[i].level < depth)]

    def label(self, i: str) -> str:
        """Label shown in candidate lists: 'code title' for coded schemas, else the id (= the name)."""
        return f"{i} {self.nodes[i].title}" if self.coded else i

    def text(self, i: str, mode: str = "path", max_kw: int = 12, max_chars: int = 300, lang: str = "en") -> str:
        """Node text for prompts and embeddings.
        mode: name (title only) | path (path titles) | kw (path + keywords; for nodes without keywords the
        child titles as hints) | desc (path + generated description) | incl (path + 'includes' text, WZ)."""
        n = self.nodes[i]
        if mode == "name":
            return self.title_of(i, lang)
        s = self.path_titles(i, lang=lang)
        if mode == "kw":
            kw = n.keywords[:max_kw] or [self.nodes[c].title for c in n.children[:max_kw]]
            if kw:
                s += " (" + ("Stichwörter: " if n.keywords else "umfasst u. a.: ") + ", ".join(kw) + ")"
        elif mode == "desc":
            if n.desc:
                s += " – " + n.desc[:max_chars]
        elif mode == "incl":
            if n.includes:
                s += " – " + n.includes[:max_chars].rsplit(" ", 1)[0] + ("…" if len(n.includes) > max_chars else "")
        elif mode != "path":
            raise ValueError(f"unknown node text mode {mode!r}")
        return s

    def attach_descriptions(self, path: str | Path) -> int:
        """Read {id, desc} lines; return how many nodes got one."""
        k = 0
        p = Path(path)
        if not p.is_file():
            return 0
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("id") in self.nodes and r.get("desc"):
                    self.nodes[r["id"]].desc = r["desc"]
                    k += 1
        return k


def _kw(v) -> list[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        return [x.strip() for x in v.replace(";", ",").split(",") if x.strip()]
    return []


def load_tree(path: str | Path, name: str = "") -> Tree:
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows:
        raise ValueError(f"empty schema {path}")
    if "code" in rows[0]:
        nodes = [
            Node(id=str(r["code"]).strip(), title=str(r.get("title") or r["code"]).strip(),
                 parent=(str(r["parent"]).strip() or None) if r.get("parent") not in (None, "", r["code"]) else None,
                 keywords=_kw(r.get("keywords")), level_name=str(r.get("level") or ""),
                 includes=str(r.get("includes") or "").strip())
            for r in rows
        ]
        return Tree(nodes, name or Path(path).stem, coded=True)
    if "id" in rows[0]:
        nodes = []
        for r in rows:
            i = str(r["id"]).strip()
            par = str(r.get("parent") or "").strip()
            de = r.get("de")
            nodes.append(Node(id=i, title=str(r["name"]).strip(), parent=None if par in ("", i) else par,
                              keywords=[de] if isinstance(de, str) else _kw(de)))
        return Tree(nodes, name or Path(path).stem, bilingual=True)
    # POI format
    pairs, seen = [], set()
    for r in rows:
        nm, par = r["name"].strip(), (r.get("parent") or "").strip()
        par = None if par in ("", nm) else par
        if (nm, par) in seen:
            continue  # exact duplicate row
        seen.add((nm, par))
        pairs.append((nm, par))
    cnt = Counter(nm for nm, _ in pairs)
    ids = {(nm, par): (nm if cnt[nm] == 1 else f"{nm} ({par})") for nm, par in pairs}
    names_unique = {nm: ids[(nm, par)] for nm, par in pairs if cnt[nm] == 1}
    nodes = []
    for nm, par in pairs:
        pid = None
        if par is not None:
            if par not in names_unique:
                raise ValueError(f"parent {par!r} of {nm!r} is missing or ambiguous")
            pid = names_unique[par]
        nodes.append(Node(id=ids[(nm, par)], title=nm, parent=pid))
    return Tree(nodes, name or Path(path).stem)


def load_schema(schema: str, root: str | Path = ".") -> Tree:
    p = Path(schema)
    if schema in SCHEMAS:
        p = Path(root) / SCHEMAS[schema]
    return load_tree(p, name=schema if schema in SCHEMAS else p.stem)


if __name__ == "__main__":
    import sys

    t = load_schema(sys.argv[1] if len(sys.argv) > 1 else "poi")
    by = Counter(n.level for n in t.nodes.values())
    leaves = Counter(n.level for n in t.nodes.values() if not n.children)
    print(json.dumps({"schema": t.name, "nodes": len(t), "roots": len(t.roots), "per_level": dict(sorted(by.items())),
                      "leaves_per_level": dict(sorted(leaves.items()))}, ensure_ascii=False))
