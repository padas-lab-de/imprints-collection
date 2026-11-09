"""E49: generate a short German description per schema node (node_text / emb_text mode "desc").

One call per node: path, sibling titles (for the boundary), child titles, and for WZ the start of the
'includes' text. Writes results/E49/node_desc/<schema>.jsonl: {id, desc, model, schema_sha256}.
Resumable (ids already in the file are skipped; responses are cached).

    python3 scripts/E49/gen_node_desc.py --schema poi --model qwen38-27b
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import DEFAULT_CACHE, DEFAULT_ENV, Client, Usage  # noqa: E402
from tree import SCHEMAS, load_schema  # noqa: E402

PROMPT = """Kategorienschema: {schema}. Kategorie: {path}
Geschwisterkategorien: {sibs}
Unterkategorien: {kids}{incl}

Schreibe eine kurze Beschreibung dieser Kategorie (ein Satz, höchstens 30 Wörter) für die Zuordnung von Websites:
welche Betreiber, Einrichtungen oder Angebote gehören dazu, und worin unterscheidet sie sich von den Geschwisterkategorien?
Antwortformat: {{"beschreibung": "<Text>"}}"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="poi")
    ap.add_argument("--model", default="qwen38-27b")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None)
    ap.add_argument("--env", default=DEFAULT_ENV)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    a = ap.parse_args()
    tree = load_schema(a.schema)
    src = Path(SCHEMAS.get(a.schema, a.schema))
    sha = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
    out = Path(a.out or f"results/E49/node_desc/{tree.name}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in out.open()} if out.exists() else set()
    todo = [i for i in tree.nodes if i not in done]
    client = Client(a.env, a.cache, a.workers)
    name = {"poi": "Themen- und Ortskategorien (POI)", "wz": "Klassifikation der Wirtschaftszweige WZ 2025"}.get(tree.name, tree.name)

    def one(i):
        n = tree[i]
        sibs = [tree[s].title for s in (tree[n.parent].children if n.parent else tree.roots) if s != i]
        incl = f"\nOffizielle Erläuterung (Anfang): {n.includes[:600]}" if n.includes else ""
        if n.keywords:
            incl += "\nStichwörter: " + ", ".join(n.keywords[:20])
        p = PROMPT.format(schema=name, path=tree.path_titles(i), sibs=", ".join(sibs[:25]) or "-",
                          kids=", ".join(tree[c].title for c in n.children[:25]) or "-", incl=incl)
        try:
            ans, _ = client.chat(a.model, [{"role": "user", "content": p}], Usage(), max_tokens=200)
            d = str(ans.get("beschreibung") or "").strip()
        except Exception as e:  # noqa: BLE001
            print(f"{i}: {e}", file=sys.stderr)
            d = ""
        return {"id": i, "desc": d, "model": a.model, "schema_sha256": sha}

    n_ok = 0
    with out.open("a", encoding="utf-8") as f, ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(one, todo):
            if r["desc"]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                n_ok += 1
    print(f"{n_ok}/{len(todo)} descriptions written -> {out}")


if __name__ == "__main__":
    main()
