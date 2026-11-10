"""E50: joint calls. parts = ("poi", "wz") (topics joint) or ("poi", "wz", "address") (one call per host).

Layout (static prefix first, for the server prefix cache):
  system = topic instructions (topic.system_text wording, without a schema line) + part A: POI schema line and the
           full POI candidate list + (address part: the address rules)
  user   = site text (landing page + imprint) + part B: WZ schema line and the 30 retrieved WZ candidates with
           ancestors + the joint answer format
Answer: {["begruendung"], "poi": "<id>", "wz": "<code>", ["addresses": [...], "no_address_reason": ...]}.
predict() returns {"poi": <topic result>, "wz": <topic result>, ["address": <address result>], "usage", "error"}.
The usage of the joint call is reported once (top level), not per part.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import address as AD  # noqa: E402
import topic as TP  # noqa: E402
from llm import Usage2  # noqa: E402

S = TP.S
TXT = {
    "de": {"intro": "Bearbeite drei Teile: A) POI-Kategorie, B) WZ-2025-Kategorie, C) Postadressen aus dem Impressum.",
           "intro2": "Bearbeite zwei Teile: A) POI-Kategorie, B) WZ-2025-Kategorie.",
           "a": "Teil A", "b": "Teil B", "c": "Teil C – Adressen",
           "ans": 'Antwortformat: {{{reason}"poi": "<Kennung aus Teil A>", "wz": "<Kennung aus Teil B>"{addr}}}'},
    "en": {"intro": "Do three parts: A) POI category, B) WZ 2025 category, C) postal addresses from the imprint.",
           "intro2": "Do two parts: A) POI category, B) WZ 2025 category.",
           "a": "Part A", "b": "Part B", "c": "Part C – addresses",
           "ans": 'Answer format: {{{reason}"poi": "<identifier from part A>", "wz": "<identifier from part B>"{addr}}}'},
}


def _cand_block(tree, cfg, cands) -> str:
    lines = [S.cand_line(tree, i, cfg) for i in cands] + [S.tx(cfg, "none")]
    return f"{S.tx(cfg, 'list')}\n" + "\n".join(lines)


def answer_spec(cfg, parts) -> str:
    t = TXT[cfg["lang"]]
    addr = ""
    if "address" in parts:
        spec = AD.answer_spec(dict(cfg, reasoning="none", reason="none"))
        body = spec[spec.index("{") + 1: spec.rindex("}")]  # the address keys of the address answer format
        addr = ", " + body
    reason = S.tx(cfg, "reason") if cfg["reason"] == "short" else ""
    return t["ans"].format(reason=reason, addr=addr)


def messages(trees: dict, cfg, site: str, poi_cands: list[str], wz_cands: list[str], parts) -> list[dict]:
    t = TXT[cfg["lang"]]
    poi, wz = trees["poi3"], trees["wz"]
    base = TP.system_text(poi, cfg)
    head = base.split("\n" + S.schema_line(cfg, poi))[0] if cfg["wording"] != "minimal" else base.split("\n")[0]
    sys_ = [head, t["intro"] if "address" in parts else t["intro2"], "",
            f"=== {t['a']} ===", S.schema_line(cfg, poi), _cand_block(poi, cfg, poi_cands)]
    if "address" in parts:
        sys_ += ["", f"=== {t['c']} ===", AD.rules_text(cfg)]
    user = [site, "", f"=== {t['b']} ===", S.schema_line(cfg, wz), _cand_block(wz, cfg, wz_cands), "",
            answer_spec(cfg, parts)]
    return [{"role": "system", "content": "\n".join(sys_)}, {"role": "user", "content": "\n".join(user)}]


def response_format(cfg, poi_cands, wz_cands, parts) -> dict | None:
    if cfg["fmt"] != "schema":
        return TP.response_format(cfg, [])
    props: dict = {"begruendung": {"type": "string"}} if cfg["reason"] == "short" else {}
    props["poi"] = {"type": "string", "enum": list(poi_cands) + ["KEINE"]}
    props["wz"] = {"type": "string", "enum": list(wz_cands) + ["KEINE"]}
    if "address" in parts:
        props.update(AD.schema_props(cfg))
    return {"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": {
        "type": "object", "properties": props, "required": list(props), "additionalProperties": False}}}


def _topic(tree, ans_id, cands) -> dict:
    ids, how = S._ids({"id": ans_id}, tree)
    kept = [i for i in ids if i in set(cands) or i in ("KEINE", "STOP")]
    if len(kept) < len(ids):
        how.append("outside_candidates")
    r = S._result(kept, None, [{"step": "joint", "ids": kept, "how": how}])
    r["path"] = tree.path(r["main"]) if r["main"] else []
    return r


def predict(llm, model: str, trees: dict, rec: dict, cfg, parts=("poi", "wz", "address")) -> dict:
    usage = Usage2()
    out: dict = {"error": None}
    try:
        site = TP.site_text(rec, dict(cfg, input="both"))
        poi_cands = trees["poi3"].candidates_up_to(cfg["depth"])
        top, wz_cands = TP.retrieve_cands(llm, trees["wz"], site, cfg, usage)
        msgs = messages(trees, cfg, site, poi_cands, wz_cands, parts)
        mt = 400 if "address" not in parts else 1100
        ans, _ = llm.chat2(model, msgs, usage, max_tokens=mt + (300 if cfg["reason"] == "short" else 0),
                           reasoning=cfg["reasoning"], response_format=response_format(cfg, poi_cands, wz_cands, parts),
                           temperature=cfg["temperature"], seed=cfg["seed"])
        out["poi"] = _topic(trees["poi3"], ans.get("poi"), poi_cands)
        out["wz"] = dict(_topic(trees["wz"], ans.get("wz"), wz_cands), retrieved=top)
        if "address" in parts:
            out["address"] = AD.parse(ans, cfg["mode"])
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"[:300]
    out["usage"] = usage.as_dict()
    return out
