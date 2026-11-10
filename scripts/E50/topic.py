"""E50: topic classification (POI flat, WZ retrieve) with prompt variants on top of the E49 strategies.

cfg = E49 DEFAULTS + the E50 keys below. With the base levels the messages and the request body are the same
as E49 (flat / retrieve, --reason short or --think on), so E49 responses come from the disk cache.

E50 keys (base level first):
  reasoning  none | short | low | medium | high | xhigh | default     (llm.py)
  wording    base (E49 text) | minimal (one task sentence) | guide (decision steps of the gold guideline 5.2/5.3)
  fmt        free | json_object | schema (json_schema strict; id = enum of the offered ids + KEINE)
  site_chars 6000 | <n>: characters per text field (landing page, imprint) sent to the model
  layout     site_first (user = site + list + answer format) | list_first (system = instructions + list +
             answer format, user = site: a static prefix for the server prefix cache) | list_first_q (system =
             instructions + list, user = site + a question line + answer format: static prefix, question last)
  lang       de | en (E49 key; the retrieval query instruction stays German, so the candidates do not change)
  shots      0 | 4 (E49 key; results/E49/fewshot.jsonl)
The retrieval query is the site text after the budget cut (as in a real run).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E49"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import strategies as S  # noqa: E402
from llm import LLM, Usage2  # noqa: E402
from tree import Tree  # noqa: E402

E50_DEFAULTS = dict(S.DEFAULTS, reasoning="none", wording="base", fmt="free", site_chars=S.SITE_CHARS,
                    layout="site_first")
BASE_LEVELS = {"wording": "base", "fmt": "free", "site_chars": S.SITE_CHARS, "layout": "site_first",
               "lang": "de", "shots": 0}

MINIMAL = {
    "de": "Ordne die Website einer Kategorie des Schemas zu. Antworte nur mit einem JSON-Objekt.",
    "en": "Assign the website to one category of the schema. Answer with one JSON object only.",
}
MINIMAL_SCHEMA = {
    "de": {"poi3": "Schema: POI-Kategorien.", "wz": "Schema: WZ 2025.", "other": "Schema: {name}."},
    "en": {"poi3": "Schema: POI categories.", "wz": "Schema: WZ 2025.", "other": "Schema: {name}."},
}
GUIDE = {
    "de": ("Du ordnest Websites einem hierarchischen Kategorienschema zu. Gehe so vor:\n"
           "1. Frage: Was bietet der Betreiber auf dieser Website an? Der Zweck der Website entscheidet.\n"
           "2. Nutze zuerst die Startseite. Nutze das Impressum nur, um zu verstehen, wer die Website betreibt.\n"
           "3. Ordne kein Thema zu, das die Website nur nebenbei erwähnt. Ordne nicht den Webdesigner, den Hoster "
           "oder den Rechtstext des Impressums zu.\n"
           "4. Firma: ihr Hauptgeschäft. Shop: was er verkauft. Verein: sein Zweck. Behörde: die Behörde.\n"
           "5. Mehrere Tätigkeiten: Nimm die Tätigkeit, die die Startseite zuerst oder am meisten zeigt.\n"
           "6. Nimm die tiefste Kategorie, die eindeutig passt. Entscheidet der Text nicht zwischen den "
           "Unterkategorien, nimm die übergeordnete Kategorie. Rate keine Unterkategorie: Eine richtige allgemeine "
           "Kategorie ist besser als eine falsche spezielle.\n"
           "7. Passt keine Kategorie oder hat die Website keinen verwertbaren Inhalt (geparkte Domain, Fehlerseite), "
           "antworte KEINE.\n"
           "Antworte nur mit einem JSON-Objekt."),
    "en": ("You assign websites to a hierarchical category schema. Do these steps:\n"
           "1. Ask: what does the operator offer on this website? The purpose of the website decides.\n"
           "2. Use the homepage first. Use the imprint only to understand who runs the website.\n"
           "3. Do not assign a topic that the website mentions only in passing. Do not assign the web designer, "
           "the host or the legal text of the imprint.\n"
           "4. A company: its main business. A shop: what it sells. An association: its purpose. A public body: "
           "the public body.\n"
           "5. Several activities: take the activity that the homepage shows first or shows most.\n"
           "6. Take the deepest category that clearly fits. If the text does not decide between the subcategories, "
           "take the parent category. Do not guess a subcategory: a correct general category is better than a "
           "wrong specific one.\n"
           "7. If no category fits or the website has no usable content (parked domain, error page), answer KEINE.\n"
           "Answer with one JSON object only."),
}
GERMAN_NAMES = " The category names are German."


def full_cfg(**kw) -> dict:
    cfg = dict(E50_DEFAULTS, **kw)
    cfg["reason"] = "short" if cfg["reasoning"] == "short" else "none"  # E49 keys used by the shared prompt code
    cfg["think"] = "on" if cfg["reasoning"] == "default" else "off"
    return cfg


def site_text(rec: dict, cfg) -> str | None:
    """E49 site_text with a character budget per field (identical to E49 for 6000)."""
    n = int(cfg.get("site_chars") or S.SITE_CHARS)
    rec2 = dict(rec, homepage_text=(rec.get("homepage_text") or "")[:n], imprint_text=(rec.get("imprint_text") or "")[:n])
    return S.site_text(rec2, cfg)


def system_text(tree: Tree, cfg) -> str:
    w = cfg["wording"]
    if w == "base":
        return S.system_prompt(tree, cfg)
    lang = cfg["lang"]
    if w == "minimal":
        sch = MINIMAL_SCHEMA[lang]
        s = MINIMAL[lang] + "\n" + sch.get(tree.name, sch["other"]).format(name=tree.name)
    elif w == "guide":
        s = GUIDE[lang]
        if lang == "en" and not tree.bilingual and tree.coded:
            s += GERMAN_NAMES
        s += "\n" + S.schema_line(cfg, tree)
    else:
        raise ValueError(f"unknown wording {w!r}")
    fs = S.fewshot_block(tree, cfg)
    return s + ("\n\n" + fs if fs else "")


def response_format(cfg, cands: list[str], top3: bool = False) -> dict | None:
    f = cfg["fmt"]
    if f == "free":
        return None
    if f == "json_object":
        return {"type": "json_object"}
    if f != "schema":
        raise ValueError(f"unknown fmt {f!r}")
    ids = list(cands) + (["KEINE"] if cfg["allow_none"] else [])
    props: dict = {}
    if cfg["reason"] == "short":
        props["begruendung"] = {"type": "string"}
    if top3:
        props["ranking"] = {"type": "array", "items": {"type": "string", "enum": ids}, "minItems": 1, "maxItems": 3}
    else:
        props["id"] = {"type": "string", "enum": ids}
    props["konfidenz"] = {"type": "number"}
    return {"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": {
        "type": "object", "properties": props, "required": list(props), "additionalProperties": False}}}


QUESTION = {
    "de": "Welche Kategorie aus der Liste im Systemprompt passt zu dieser Website?",
    "en": "Which category from the list in the system prompt fits this website?",
}


def messages(tree: Tree, cfg, head: str, cands: list[str]) -> list[dict]:
    lines = [S.cand_line(tree, i, cfg) for i in cands]
    if cfg["allow_none"]:
        lines.append(S.tx(cfg, "none"))
    lst = f"{S.tx(cfg, 'list')}\n" + "\n".join(lines)
    ans = S.answer_spec(cfg)
    sys_ = system_text(tree, cfg)
    if cfg["layout"] == "site_first":
        return [{"role": "system", "content": sys_}, {"role": "user", "content": f"{head}\n\n{lst}\n\n{ans}"}]
    if cfg["layout"] == "list_first":
        return [{"role": "system", "content": f"{sys_}\n\n{lst}\n\n{ans}"}, {"role": "user", "content": head}]
    if cfg["layout"] == "list_first_q":
        q = QUESTION[cfg["lang"]]
        return [{"role": "system", "content": f"{sys_}\n\n{lst}"}, {"role": "user", "content": f"{head}\n\n{q}\n{ans}"}]
    raise ValueError(f"unknown layout {cfg['layout']!r}")


def max_tokens(cfg) -> int:
    return 400 if cfg["reason"] == "none" else 700


def choose(llm: LLM, model: str, tree: Tree, cfg, usage, head: str, cands: list[str]) -> dict:
    msgs = messages(tree, cfg, head, cands)
    ans, _ = llm.chat2(model, msgs, usage, max_tokens=max_tokens(cfg), reasoning=cfg["reasoning"],
                       response_format=response_format(cfg, cands), temperature=cfg["temperature"], seed=cfg["seed"])
    ids, how = S._ids(ans, tree)
    allowed = set(cands)
    kept = [i for i in ids if i in allowed or i in ("KEINE", "STOP")]
    if len(kept) < len(ids):
        how.append("outside_candidates")
    return {"ids": kept, "how": how, "conf": S._conf(ans), "reason": str(ans.get("begruendung") or "")[:300]}


def flat(llm, model, tree: Tree, rec, cfg, usage) -> dict:
    site = site_text(rec, cfg)
    if site is None:
        return S._result([], error="no_input")
    cands = tree.candidates_up_to(cfg["depth"])
    r = choose(llm, model, tree, cfg, usage, site, cands)
    return S._result(r["ids"], r["conf"], [{"step": "flat", "n_cands": len(cands), **r}])


def retrieve_cands(llm, tree: Tree, site: str, cfg, usage) -> tuple[list[str], list[str]]:
    """(top-k retrieved ids, candidates with ancestors). German query instruction for every prompt language."""
    top = S.retrieve_ids(llm, tree, site, dict(cfg, lang="de"), usage)
    return top, S.with_ancestors(tree, top)


def retrieve(llm, model, tree: Tree, rec, cfg, usage) -> dict:
    site = site_text(rec, cfg)
    if site is None:
        return S._result([], error="no_input")
    top, cands = retrieve_cands(llm, tree, site, cfg, usage)
    r = choose(llm, model, tree, cfg, usage, site, cands)
    return S._result(r["ids"], r["conf"], [{"step": "retrieve", "topk": top, "n_cands": len(cands), **r}],
                     retrieved=top)


STRATEGIES = {"flat": flat, "retrieve": retrieve}


def predict(llm, model, tree, rec, cfg) -> dict:
    usage = Usage2()
    try:
        out = STRATEGIES[cfg["strategy"]](llm, model, tree, rec, cfg, usage)
    except Exception as e:  # the scorer counts it as a failed reply (abstention)
        out = S._result([], error=f"{type(e).__name__}: {e}"[:300])
    out["usage"] = usage.as_dict()
    out["path"] = tree.path(out["main"]) if out["main"] else []
    return out


def tag(cfg, model_short: str, task: str = "topic") -> str:
    """Run name: base levels are left out, so the base run of a model is <strategy>__<model>__r-<reasoning>."""
    parts = [cfg["strategy"] if task == "topic" else task, model_short, "r-" + cfg["reasoning"]]
    if cfg["lang"] != "de":
        parts.append(cfg["lang"])
    if cfg["wording"] != "base":
        parts.append("w-" + cfg["wording"])
    if cfg["fmt"] != "free":
        parts.append("f-" + cfg["fmt"])
    if cfg["shots"]:
        parts.append(f"s{cfg['shots']}")
    if int(cfg["site_chars"]) != S.SITE_CHARS:
        parts.append(f"c{cfg['site_chars']}")
    if cfg["layout"] != "site_first":
        parts.append(cfg["layout"])
    if task == "topic" and cfg["strategy"] == "retrieve" and int(cfg.get("k", 30)) != 30:
        parts.append(f"k{cfg['k']}")
    for k, base in (("mode", "list"), ("addr_input", "imprint")):
        if cfg.get(k) and cfg[k] != base:
            parts.append(f"{k}-{cfg[k]}")
    return "__".join(parts)


