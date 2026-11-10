"""E50: run one configuration over the dev inputs and write predictions.

    python3 scripts/E50/e50_run.py --task topic --schema poi3 --model gemma4-31b-it --reasoning short
    python3 scripts/E50/e50_run.py --task topic --schema wz --model qwen38-27b --reasoning none --lang en
    python3 scripts/E50/e50_run.py --task address --model gemma4-31b-it --mode list --fmt schema
    python3 scripts/E50/e50_run.py --task joint --parts poi,wz,address --model qwen38-27b

Topic defaults follow docs/extraction_strategy.md: POI flat, node names "English (Deutsch)"; WZ retrieve k30,
node text path, embedding text kw; input landing page + imprint. Factor switches: --reasoning --lang --wording
--fmt --shots --site-chars --layout (topic.py), --mode --addr-input (address.py), --parts (joint.py).
Output: <out-dir>/<schema|address|joint>/<tag>.jsonl (topic lines have the E49 format; scripts/E49/score.py reads
them). A joint run also writes its POI, WZ (and address) parts to <out-dir>/poi3/, wz/, address/ (usage = the whole call).
Resumable. Refuses input files whose name contains "heldout" unless --allow-heldout (selection is on dev only).
Run from the repository root.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import address as AD  # noqa: E402
import joint as JT  # noqa: E402
import topic as TP  # noqa: E402
from llm import DEFAULT_CACHE, DEFAULT_ENV, LLM, REASONING  # noqa: E402

from tree import load_schema  # noqa: E402  (scripts/E49, put on sys.path by topic)

DEV = "/home/dinzinger/GitLab/fim/imprints-collection/datasets/E49/dev_inputs.jsonl"
SHORT = {"qwen38-27b": "qwen", "gemma4-31b-it": "gemma", "qwen-agentworld-35b-a3b": "agentworld",
         "soofi-s-isar-preview": "soofi"}
STRATEGY = {"poi3": "flat", "wz": "retrieve"}
NODE_LANG = {"poi3": "both", "wz": "en"}


def build_cfg(a) -> dict:
    kw = dict(reasoning=a.reasoning, lang=a.lang, wording=a.wording, fmt=a.fmt, shots=a.shots,
              site_chars=a.site_chars, layout=a.layout, input="both", k=a.k, node_text="path", emb_text="kw")
    if a.task == "topic":
        return TP.full_cfg(strategy=a.strategy or STRATEGY[a.schema], node_lang=NODE_LANG[a.schema], **kw)
    kw.update(mode=a.mode, addr_input=a.addr_input)
    if a.task == "joint":
        kw["node_lang"] = "both"  # POI part; WZ titles have no German/English pair, so "both" leaves them unchanged
    return AD.full_cfg(**kw)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="topic", choices=["topic", "address", "joint"])
    ap.add_argument("--schema", default="poi3", choices=["poi3", "wz"])
    ap.add_argument("--model", default="gemma4-31b-it")
    ap.add_argument("--reasoning", default="none", choices=REASONING)
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--wording", default="base", choices=["base", "minimal", "guide"])
    ap.add_argument("--fmt", default="free", choices=["free", "json_object", "schema"])
    ap.add_argument("--shots", type=int, default=0)
    ap.add_argument("--site-chars", type=int, default=6000)
    ap.add_argument("--layout", default="site_first", choices=["site_first", "list_first", "list_first_q"])
    ap.add_argument("--strategy", default=None, choices=["flat", "retrieve"],
                    help="topic strategy (default: poi3 flat, wz retrieve)")
    ap.add_argument("--k", type=int, default=30, help="retrieved candidates (strategy retrieve)")
    ap.add_argument("--mode", default="list", choices=["list", "main"])
    ap.add_argument("--addr-input", default="imprint", choices=["imprint", "both"])
    ap.add_argument("--parts", default="poi,wz,address")
    ap.add_argument("--dev", default=DEV)
    ap.add_argument("--allow-heldout", action="store_true")
    ap.add_argument("--hosts", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out-dir", default="results/E50/preds/dev")
    ap.add_argument("--env", default=DEFAULT_ENV)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    a = ap.parse_args()
    if "heldout" in Path(a.dev).name and not a.allow_heldout:
        sys.exit("refusing a held-out input file (selection is on dev only); use --allow-heldout for the final check")
    if a.task == "address" and a.wording == "guide":
        sys.exit("address wording: base | minimal")

    cfg = build_cfg(a)
    short = SHORT.get(a.model, a.model)
    parts = tuple(p for p in a.parts.split(",") if p)
    if a.task == "topic":
        tree = load_schema(a.schema)
        tag, sub = TP.tag(cfg, short), a.schema
    elif a.task == "address":
        tag, sub = TP.tag(cfg, short, task="address"), "address"
    else:
        trees = {"poi3": load_schema("poi3"), "wz": load_schema("wz")}
        tag, sub = TP.tag(cfg, short, task="joint-" + "-".join(parts)), "joint"
    recs = [json.loads(l) for l in open(a.dev, encoding="utf-8") if l.strip()]
    if a.hosts:
        want = {l.strip() for l in open(a.hosts) if l.strip()}
        recs = [r for r in recs if r["host"] in want]
    if a.limit:
        recs = recs[: a.limit]
    out = Path(a.out_dir) / sub / f"{tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["host"] for l in out.open()} if out.exists() else set()
    todo = [r for r in recs if r["host"] not in done]
    llm = LLM(a.env, a.cache, max_parallel=a.workers)
    print(f"{tag}: {len(todo)} hosts to do ({len(done)} done) -> {out}", flush=True)

    def one(rec):
        t0 = time.time()
        if a.task == "topic":
            p = TP.predict(llm, a.model, tree, rec, cfg)
        elif a.task == "address":
            p = AD.predict(llm, a.model, rec, cfg)
        else:
            p = JT.predict(llm, a.model, trees, rec, cfg, parts)
        p.setdefault("error", None)
        return {"host": rec["host"], "task": a.task, "schema": a.schema if a.task == "topic" else sub, "tag": tag,
                "model": a.model, "cfg": cfg, "latency_s": round(time.time() - t0, 2), **p}

    split = {}
    if a.task == "joint":
        for s in ("poi3", "wz") + (("address",) if "address" in parts else ()):
            q = Path(a.out_dir) / s / f"{tag}.jsonl"
            q.parent.mkdir(parents=True, exist_ok=True)
            split[s] = q.open("a", encoding="utf-8")
    lock = threading.Lock()
    st = {"n": 0, "err": 0, "calls": 0, "cached": 0, "prompt_tokens": 0, "cached_prompt_tokens": 0,
          "completion_tokens": 0, "reasoning_tokens": 0, "truncated": 0, "latency_s": 0.0}
    t0 = time.time()
    with out.open("a", encoding="utf-8") as f, ThreadPoolExecutor(a.workers) as ex:
        for rec in ex.map(one, todo):
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                for s, h in split.items():
                    if s == "address":
                        part = rec.get("address") or {"addresses": [], "main_index": None, "no_address_reason": None}
                    else:
                        part = rec.get("poi" if s == "poi3" else "wz") or {"main": None, "ranked": [], "path": []}
                    h.write(json.dumps({"host": rec["host"], "task": "joint", "schema": s, "tag": tag,
                                        "model": a.model, "cfg": cfg, "latency_s": rec["latency_s"], **part,
                                        "error": rec["error"], "usage": rec["usage"], "shared_usage": True},
                                       ensure_ascii=False) + "\n")
                    h.flush()
                st["n"] += 1
                st["err"] += bool(rec["error"])
                for k in st:
                    if k not in ("n", "err", "latency_s"):
                        st[k] += rec["usage"].get(k, 0)
                st["latency_s"] += rec["latency_s"]
    for h in split.values():
        h.close()
    n = max(st["n"], 1)
    print(json.dumps({"tag": tag, **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in st.items()},
                      "s_per_host": round(st["latency_s"] / n, 2),
                      "tok_in_per_host": round(st["prompt_tokens"] / n), "tok_out_per_host": round(st["completion_tokens"] / n),
                      "wall_s": round(time.time() - t0, 1)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
