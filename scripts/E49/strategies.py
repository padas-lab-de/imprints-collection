"""E49: prompting strategies for classifying a website into a hierarchical topic schema.

Strategies (cfg["strategy"]):
  flat      all candidate nodes up to depth D in one prompt; pick one (or rank 3); inner nodes are
            listed too, so the model can stop at a higher level; "KEINE" = nothing fits.
  hier      top-down: root, then child, ... ; at each step "STOP" keeps the current node; single-child
            chains are followed without a call; beam=2 explores the top-2 roots and a last call picks
            between the two finished paths (backtracking).
  retrieve  embed node texts (octen-embedding-8b), top-k for the site text (optionally reranked with
            qwen3-reranker-4b from a pool of max(2k, 40)), the LLM chooses among the k plus their ancestors.
  describe  the LLM first writes a short description of what the operator does; that description is
            the retrieval query; the chooser sees the description (chooser=desc) or description + text.

Options (cfg keys, with defaults in DEFAULTS): input home|imprint|both; depth D; node_text name|path|kw|desc|incl;
output one|top3; reason none|short; think off|on; shots 0..4; lang de|en; k; rerank; temperature; seed;
rules (text of a rules block appended to the system prompt of every choice call; None = off, prompt unchanged);
keep_outside (keep an answer that names a valid node outside the offered candidates; default: drop it);
rules_cands (list of node ids added to the retrieve candidates, e.g. the codes cited in the rules; None = off).
Every strategy returns a dict with main (node id or None), ranked (ids, best first), trace, error.
"""

from __future__ import annotations

import json
import math
import threading
from pathlib import Path

from client import Client, Usage
from tree import Tree


def load_rules(path) -> str:
    """Rules block from a text/markdown file; lines starting with '#' are comments (not sent to the model)."""
    lines = [l.rstrip() for l in Path(path).read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#")]
    return "\n".join(lines).strip()

def rules_code_ids(tree: Tree, rules_text: str) -> list[str]:
    """Node ids of WZ codes cited in a rules text (e.g. 58.29.0, 62.10, 47), in order of first citation.
    Rule numbering at line start ("1. ") is skipped; codes that are not nodes of the tree are dropped."""
    import re

    ids: list[str] = []
    for line in rules_text.splitlines():
        line = re.sub(r"^\s*\d+\.\s+", "", line)
        for m in re.finditer(r"(?<![\d.])\d{2}(?:\.\d{1,2}(?:\.\d)?)?(?![\d])", line):
            c = m.group(0)
            if c in tree and c not in ids:
                ids.append(c)
    return ids


DEFAULTS = {
    "strategy": "flat", "input": "home", "depth": 99, "node_text": "path", "output": "one", "reason": "none",
    "think": "off", "shots": 0, "lang": "de", "k": 30, "rerank": False, "beam": 1, "chooser": "desc",
    "emb_text": "kw", "temperature": 0.0, "seed": None, "max_kw": 12, "allow_none": True, "rules": None,
    "keep_outside": False, "rules_cands": None,
}
SITE_CHARS = 6_000  # per text field (dev_inputs are already cut to 6k)
QUERY_CHARS = 4_000  # embedding query
RERANK_CHARS = 1_500  # rerank query (the reranker scores query + doc per pair: keep it short)
FEWSHOT = Path(__file__).resolve().parents[2] / "results" / "E49" / "fewshot.jsonl"

# --------------------------------------------------------------------------------------------- prompts
T = {
    "de": {
        "system": ("Du ordnest Websites einem hierarchischen Kategorienschema zu. Maßgeblich ist, was der Betreiber "
                   "der Website hauptsächlich tut oder anbietet (nicht, worüber die Seite nebenbei berichtet; nicht "
                   "Webdesigner, Hoster oder Datenschutzhinweise). Wähle die spezifischste Kategorie, die eindeutig passt (z. B. „Italienisches Restaurant“ "
                   "statt „Restaurant“, wenn die Küche klar ist); ist eine spezifischere Kategorie unsicher, wähle die allgemeinere. Antworte nur mit einem JSON-Objekt."),
        "schema_poi": "Schema: Themen- und Ortskategorien (POI).",
        "schema_wz": ("Schema: Klassifikation der Wirtschaftszweige WZ 2025. Ordne die wirtschaftliche Haupttätigkeit "
                      "des Betreibers zu (auch Vereine, Behörden, Privatpersonen haben eine Tätigkeit)."),
        "schema_other": "Schema: {name}.",
        "list": "Kategorien (Kennung in eckigen Klammern):",
        "none": "[KEINE] keine Kategorie passt",
        "stop": "[STOP] bei „{cur}“ bleiben, weil keine Unterkategorie eindeutig passt",
        "ans_one": 'Antwortformat: {{{reason}"id": "<Kennung>", "konfidenz": <0 bis 1>}}',
        "ans_top3": 'Antwortformat: {{{reason}"ranking": ["<beste Kennung>", "<zweite>", "<dritte>"], "konfidenz": <0 bis 1 für die erste>}}',
        "reason": '"begruendung": "<höchstens 2 kurze Sätze>", ',
        "site": "Website", "home": "STARTSEITE", "imprint": "IMPRESSUM", "no_imprint": "(kein Impressum erfasst)",
        "title": "Titel", "descr": "Beschreibung", "path_so_far": "Bisher gewählt: {path}. Wähle die passende Unterkategorie.",
        "choose_root": "Wähle die passende Hauptkategorie.",
        "final": "Zwei mögliche Zuordnungen wurden ermittelt. Wähle die passendere.",
        "describe": ('Beschreibe in 1–2 Sätzen auf Deutsch, was der Betreiber dieser Website hauptsächlich tut oder anbietet '
                     '(Art der Organisation, Branche, Angebot). Antwortformat: {"beschreibung": "<Text>"}'),
        "desc_label": "Beschreibung des Betreibers",
        "examples": "Beispiele (Text → Zuordnung):",
    },
    "en": {
        "system": ("You assign websites to a hierarchical category schema. What counts is what the website operator "
                   "primarily does or offers (not what the site mentions in passing; not the web designer, host or privacy notes). "
                   "Choose the most specific category that clearly fits (e.g. \"Italienisches Restaurant\" rather than \"Restaurant\" "
                   "if the cuisine is clear); if a more specific category is uncertain, choose the more general one. "
                   "Answer with one JSON object only. The category names are German."),
        "schema_poi": "Schema: topic and place categories (POI).",
        "schema_wz": ("Schema: German classification of economic activities WZ 2025. Classify the operator's main economic "
                      "activity (associations, authorities and private persons have an activity too)."),
        "schema_other": "Schema: {name}.",
        "list": "Categories (identifier in square brackets):",
        "none": "[KEINE] no category fits",
        "stop": "[STOP] stay at “{cur}” because no subcategory clearly fits",
        "ans_one": 'Answer format: {{{reason}"id": "<identifier>", "konfidenz": <0 to 1>}}',
        "ans_top3": 'Answer format: {{{reason}"ranking": ["<best identifier>", "<second>", "<third>"], "konfidenz": <0 to 1 for the first>}}',
        "reason": '"begruendung": "<at most 2 short sentences>", ',
        "site": "Website", "home": "HOMEPAGE", "imprint": "IMPRINT", "no_imprint": "(no imprint captured)",
        "title": "Title", "descr": "Description", "path_so_far": "Chosen so far: {path}. Choose the matching subcategory.",
        "choose_root": "Choose the matching top-level category.",
        "final": "Two possible assignments were found. Choose the better one.",
        "describe": ('Describe in 1-2 sentences in German what the operator of this website primarily does or offers '
                     '(type of organisation, industry, offer). Answer format: {"beschreibung": "<text>"}'),
        "desc_label": "Description of the operator",
        "examples": "Examples (text → assignment):",
    },
}


def tx(cfg, key, **kw) -> str:
    s = T[cfg["lang"]][key]
    return s.format(**kw) if kw else s


def schema_line(cfg, tree: Tree) -> str:
    key = "schema_" + tree.name if tree.name in ("poi", "wz") else "schema_other"
    return tx(cfg, key, name=tree.name)


def site_text(rec: dict, cfg) -> str | None:
    """User-side text for the chosen input; None if the input is empty (imprint-only without imprint)."""
    m = rec.get("meta") or {}
    home = (rec.get("homepage_text") or "")[:SITE_CHARS]
    imp = (rec.get("imprint_text") or "")[:SITE_CHARS]
    if cfg["input"] == "imprint" and not imp:
        return None
    parts = [f"{tx(cfg, 'site')}: {rec['host']}"]
    if cfg["input"] in ("home", "both"):
        if m.get("title"):
            parts.append(f"{tx(cfg, 'title')}: {m['title']}")
        if m.get("description"):
            parts.append(f"{tx(cfg, 'descr')}: {m['description']}")
        parts.append(f"=== {tx(cfg, 'home')} ===\n{home}")
    if cfg["input"] in ("imprint", "both"):
        if cfg["input"] == "both" and imp:  # drop navigation lines the homepage already shows
            seen = set(home.lower().splitlines())
            imp = "\n".join(l for l in imp.splitlines() if l.lower() not in seen)
        parts.append(f"=== {tx(cfg, 'imprint')} ===\n{imp or tx(cfg, 'no_imprint')}")
    return "\n".join(parts)


def answer_spec(cfg, top3: bool | None = None) -> str:
    top3 = cfg["output"] == "top3" if top3 is None else top3
    reason = tx(cfg, "reason") if cfg["reason"] == "short" else ""
    return tx(cfg, "ans_top3" if top3 else "ans_one", reason=reason)


def cand_line(tree: Tree, i: str, cfg) -> str:
    return f"[{i}] {tree.text(i, cfg['node_text'], max_kw=cfg['max_kw'])}"


_FEW: dict = {}


def fewshot_block(tree: Tree, cfg) -> str:
    n = int(cfg.get("shots") or 0)
    if not n or not FEWSHOT.is_file():
        return ""
    if "rows" not in _FEW:
        _FEW["rows"] = [json.loads(l) for l in FEWSHOT.read_text(encoding="utf-8").splitlines() if l.strip()]
    lines = [tx(cfg, "examples")]
    k = 0
    for r in _FEW["rows"]:
        lab = (r.get("labels") or {}).get(tree.name)
        if lab not in tree:
            continue
        lines.append(f"- „{r['text']}“ → [{lab}] {tree.path_titles(lab)}")
        k += 1
        if k >= n:
            break
    return "\n".join(lines) if k else ""


def system_prompt(tree: Tree, cfg) -> str:
    s = tx(cfg, "system") + "\n" + schema_line(cfg, tree)
    if cfg.get("rules"):
        s += "\n\n" + cfg["rules"].strip()
    fs = fewshot_block(tree, cfg)
    return s + ("\n\n" + fs if fs else "")


def _ids(ans: dict, tree: Tree, extra_ok=("KEINE", "STOP")) -> tuple[list, list[str]]:
    """Resolved ids from an answer (id or ranking). Returns (ids incl. KEINE/STOP markers, resolve how)."""
    raw = ans.get("ranking") if isinstance(ans.get("ranking"), list) else [ans.get("id")]
    out, how = [], []
    for a in raw:
        if isinstance(a, str) and a.strip().strip("[]").upper() in extra_ok:
            out.append(a.strip().strip("[]").upper())
            how.append("marker")
            continue
        i, h = tree.resolve(a)
        how.append(h)
        if i is not None and i not in out:
            out.append(i)
    return out, how


def _conf(ans: dict):
    try:
        return max(0.0, min(1.0, float(ans.get("konfidenz"))))
    except (TypeError, ValueError):
        return None


def choose(client: Client, model: str, tree: Tree, cfg, usage: Usage, user_head: str, cands: list[str],
           extra_lines: list[str] = (), top3: bool | None = None, restrict: bool = True) -> dict:
    """One choice call among candidate nodes. Returns {ids, how, conf, reason}; ids filtered to cands + markers."""
    lines = [cand_line(tree, i, cfg) for i in cands] + list(extra_lines)
    if cfg["allow_none"]:
        lines.append(tx(cfg, "none"))
    user = f"{user_head}\n\n{tx(cfg, 'list')}\n" + "\n".join(lines) + "\n\n" + answer_spec(cfg, top3)
    msgs = [{"role": "system", "content": system_prompt(tree, cfg)}, {"role": "user", "content": user}]
    ans, _ = client.chat(model, msgs, usage, max_tokens=400 if cfg["reason"] == "none" else 700,
                         temperature=cfg["temperature"], seed=cfg["seed"], think=cfg["think"] == "on")
    ids, how = _ids(ans, tree)
    allowed = set(cands)
    if restrict and cfg.get("keep_outside") and any(i not in allowed and i not in ("KEINE", "STOP") for i in ids):
        how.append("outside_kept")  # answer names a real node that was not offered (e.g. a code from the rules)
    elif restrict:
        kept = [i for i in ids if i in allowed or i in ("KEINE", "STOP")]
        if len(kept) < len(ids):
            how.append("outside_candidates")
        ids = kept
    return {"ids": ids, "how": how, "conf": _conf(ans), "reason": str(ans.get("begruendung") or "")[:300]}


# --------------------------------------------------------------------------------------------- strategies
def _result(ids: list, conf=None, trace=None, **kw) -> dict:
    real = [i for i in ids if i not in ("KEINE", "STOP")]
    main = None if (not ids or ids[0] == "KEINE") else real[0] if real else None
    return {"main": main, "ranked": real[:3], "confidence": conf, "trace": trace or [], **kw}


def flat(client, model, tree: Tree, rec, cfg, usage) -> dict:
    site = site_text(rec, cfg)
    if site is None:
        return _result([], error="no_input")
    cands = tree.candidates_up_to(cfg["depth"])
    r = choose(client, model, tree, cfg, usage, site, cands)
    return _result(r["ids"], r["conf"], [{"step": "flat", "n_cands": len(cands), **r}])


def hier(client, model, tree: Tree, rec, cfg, usage) -> dict:
    site = site_text(rec, cfg)
    if site is None:
        return _result([], error="no_input")
    trace = []

    def descend(cur: str | None, first_ids: list | None = None) -> tuple[str | None, list, float | None]:
        """Greedy descent from cur (None = above the roots). Returns (node, ranked siblings at the last step, conf)."""
        ranked, conf = [], None
        while True:
            if cur is not None:
                cur = tree.extend(cur) if tree[cur].level < cfg["depth"] else cur
                while tree[cur].level > cfg["depth"]:
                    cur = tree[cur].parent
                if tree[cur].level >= cfg["depth"] or not tree[cur].children:
                    return cur, ranked, conf
            opts = tree.roots if cur is None else tree[cur].children
            if first_ids is not None:
                ids, first_ids = first_ids, None
            else:
                head = site + "\n\n" + (tx(cfg, "choose_root") if cur is None else
                                        tx(cfg, "path_so_far", path=tree.path_titles(cur)))
                extra = [] if cur is None else [tx(cfg, "stop", cur=tree[cur].title)]
                saved = cfg["allow_none"]
                cfg2 = dict(cfg, allow_none=saved and cur is None)
                r = choose(client, model, tree, cfg2, usage, head, opts, extra)
                trace.append({"step": "hier", "at": cur, **r})
                ids = r["ids"]
                conf = r["conf"]
            real = [i for i in ids if i in tree]
            if not ids or ids[0] in ("STOP", "KEINE") or not real:
                if cur is None and ids and ids[0] == "KEINE":
                    return None, [], conf
                return cur, ranked or ([cur] if cur else []), conf
            ranked = real
            cur = real[0]

    if cfg["beam"] <= 1:
        node, ranked, conf = descend(None)
        ids = ([node] if node else ["KEINE"]) + [i for i in ranked if i != node]
        return _result(ids, conf, trace)
    # backtracking: rank the roots, finish the best two, then compare the two paths
    head = site + "\n\n" + tx(cfg, "choose_root")
    r = choose(client, model, tree, cfg, usage, head, tree.roots, top3=True)
    trace.append({"step": "hier_roots", **r})
    roots = [i for i in r["ids"] if i in tree][:2]
    if not roots:
        return _result(["KEINE"] if r["ids"][:1] == ["KEINE"] else [], r["conf"], trace)
    ends = []
    for root in roots:
        node, _, c = descend(None, first_ids=[root])
        if node and node not in ends:
            ends.append(node)
    if len(ends) == 1:
        return _result(ends, r["conf"], trace)
    cfg2 = dict(cfg, allow_none=False, output="one", node_text="path")
    f = choose(client, model, tree, cfg2, usage, site + "\n\n" + tx(cfg, "final"), ends)
    trace.append({"step": "hier_final", **f})
    ids = f["ids"] or ends
    return _result(ids + [e for e in ends if e not in ids], f["conf"], trace)


# ----- retrieval
_EMB: dict = {}
_EMB_LOCK = threading.Lock()


def _norm(v):
    s = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / s for x in v]


def node_matrix(client: Client, tree: Tree, mode: str, ids: list[str]):
    key = (tree.name, len(tree), mode, tuple(ids))
    with _EMB_LOCK:
        if key not in _EMB:
            vecs = client.embed([tree.text(i, mode) for i in ids], Usage())
            try:
                import numpy as np

                m = np.array(vecs, dtype="float32")
                m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-9
            except ImportError:
                m = [_norm(v) for v in vecs]
            _EMB[key] = m
        return _EMB[key]


QUERY_INSTRUCT = {
    "de": "Instruct: Finde die Kategorie, die beschreibt, was der Betreiber dieser Website hauptsächlich tut oder anbietet.\nQuery: ",
    "en": "Instruct: Find the category that describes what the operator of this website primarily does or offers.\nQuery: ",
}


def retrieve_ids(client, tree: Tree, query: str, cfg, usage) -> list[str]:
    pool = tree.candidates_up_to(cfg["depth"])
    m = node_matrix(client, tree, cfg["emb_text"], pool)
    q = _norm(client.embed([QUERY_INSTRUCT[cfg["lang"]] + query[:QUERY_CHARS]], usage)[0])
    try:
        import numpy as np

        sims = (m @ np.array(q, dtype="float32")).tolist()
    except (ImportError, TypeError):
        sims = [sum(a * b for a, b in zip(row, q)) for row in m]
    order = sorted(range(len(pool)), key=lambda j: -sims[j])
    k = cfg["k"]
    if not cfg["rerank"]:
        return [pool[j] for j in order[:k]]
    cand = [pool[j] for j in order[: max(2 * k, 40)]]
    scores = client.rerank(query[:RERANK_CHARS], [tree.text(i, cfg["emb_text"]) for i in cand], usage)
    return [c for _, c in sorted(zip(scores, cand), key=lambda t: -t[0])[:k]]


def with_ancestors(tree: Tree, ids: list[str]) -> list[str]:
    """Candidates plus their ancestors (so the model can stop higher), in tree file order."""
    want = set()
    for i in ids:
        want.update(tree.path(i))
    return [i for i in tree.nodes if i in want and not (tree.redundant(i) and tree.nodes[i].children[0] in want)]


def retrieve(client, model, tree: Tree, rec, cfg, usage, query: str | None = None, head: str | None = None,
             trace=None) -> dict:
    site = site_text(rec, cfg)
    if site is None:
        return _result([], error="no_input")
    trace = trace or []
    top = retrieve_ids(client, tree, query or site, cfg, usage)
    if cfg.get("rules_cands"):
        top = top + [i for i in cfg["rules_cands"] if i in tree and i not in top]
    cands = with_ancestors(tree, top)
    r = choose(client, model, tree, cfg, usage, head or site, cands)
    trace.append({"step": "retrieve", "topk": top, "n_cands": len(cands), **r})
    return _result(r["ids"], r["conf"], trace, retrieved=top)


def describe(client, model, tree: Tree, rec, cfg, usage) -> dict:
    site = site_text(rec, cfg)
    if site is None:
        return _result([], error="no_input")
    msgs = [{"role": "user", "content": site + "\n\n" + tx(cfg, "describe")}]
    ans, _ = client.chat(model, msgs, usage, max_tokens=300, temperature=cfg["temperature"], seed=cfg["seed"],
                         think=cfg["think"] == "on")
    desc = str(ans.get("beschreibung") or "").strip()
    if not desc:
        return _result([], error="empty_description")
    head = f"{tx(cfg, 'desc_label')}: {desc}"
    if cfg["chooser"] == "both":
        head = site + "\n\n" + head
    else:
        head = f"{tx(cfg, 'site')}: {rec['host']}\n{head}"
    out = retrieve(client, model, tree, rec, cfg, usage, query=desc, head=head, trace=[{"step": "describe", "desc": desc}])
    out["description"] = desc
    return out


STRATEGIES = {"flat": flat, "hier": hier, "retrieve": retrieve, "describe": describe}


def predict(client, model, tree, rec, cfg) -> dict:
    usage = Usage()
    try:
        out = STRATEGIES[cfg["strategy"]](client, model, tree, rec, cfg, usage)
    except Exception as e:  # keep going; the scorer counts it as abstain
        out = _result([], error=f"{type(e).__name__}: {e}"[:300])
    out["usage"] = usage.as_dict()
    out["path"] = tree.path(out["main"]) if out["main"] else []
    return out
