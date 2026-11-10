"""E49: run one strategy configuration over the dev inputs and write predictions.

    python3 scripts/E49/run.py --schema poi --strategy flat --model qwen38-27b --input home --limit 20
    python3 scripts/E49/run.py --schema wz --strategy hier --depth 3 --beam 2 --node-text kw
    python3 scripts/E49/run.py --schema poi --strategy retrieve --k 30 --rerank
    python3 scripts/E49/run.py --schema poi --strategy describe --chooser both
    python3 scripts/E49/run.py --schema poi --strategy flat --samples 5 --temperature 0.7   # self-consistency
    python3 scripts/E49/run.py --schema wz --strategy retrieve --rules results/E49/wz_rules.md   # rules block in the prompt

--schema takes poi | wz | a path to any schema file (tree.py formats).
Output: <out-dir>/<schema>/<tag>.jsonl, one line per host:
  {host, schema, tag, cfg, model, main, ranked, path, confidence, error, usage, latency_s, trace, [samples]}
and a summary line on stdout (hosts, errors, abstentions, calls, tokens, mean latency).
Resumable: hosts already in the output file are skipped (delete the file to rerun; responses are cached).
Run from the repository root with python3 (numpy optional, speeds up retrieval).
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
from client import DEFAULT_CACHE, DEFAULT_ENV, Client  # noqa: E402
from strategies import DEFAULTS, load_rules, predict, rules_code_ids  # noqa: E402
from tree import load_schema  # noqa: E402
from vote import VOTES  # noqa: E402

DEV = "/home/dinzinger/GitLab/fim/imprints-collection/datasets/E49/dev_inputs.jsonl"
SHORT = {"qwen38-27b": "qwen", "gemma4-31b-it": "gemma", "qwen-agentworld-35b-a3b": "agentworld",
         "soofi-s-isar-preview": "soofi"}


def make_tag(cfg: dict, model: str, samples: int, rules_name: str | None = None) -> str:
    s = cfg["strategy"]
    parts = [s, SHORT.get(model, model), cfg["input"], f"d{cfg['depth']}" if cfg["depth"] < 99 else "dmax",
             f"nt-{cfg['node_text']}"]
    if cfg["output"] != "one":
        parts.append(cfg["output"])
    if cfg["reason"] != "none":
        parts.append("reason")
    if cfg["think"] == "on":
        parts.append("think")
    if cfg["shots"]:
        parts.append(f"shots{cfg['shots']}")
    if cfg["lang"] != "de":
        parts.append(cfg["lang"])
    if s in ("retrieve", "describe"):
        parts += [f"k{cfg['k']}", f"emb-{cfg['emb_text']}"] + (["rr"] if cfg["rerank"] else [])
    if s == "describe" and cfg["chooser"] != "desc":
        parts.append("chooser-" + cfg["chooser"])
    if s == "hier" and cfg["beam"] > 1:
        parts.append(f"beam{cfg['beam']}")
    if not cfg["allow_none"]:
        parts.append("nonone")
    if cfg.get("rules"):
        parts.append("rules-" + (rules_name or "x"))
    if cfg.get("keep_outside"):
        parts.append("keepout")
    if cfg.get("rules_cands"):
        parts.append("rulescand")
    if samples > 1:
        parts.append(f"sc{samples}-t{cfg['temperature']}")
    return "__".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="poi")
    ap.add_argument("--strategy", default="flat", choices=["flat", "hier", "retrieve", "describe"])
    ap.add_argument("--model", default="qwen38-27b")
    ap.add_argument("--input", default="home", choices=["home", "imprint", "both"])
    ap.add_argument("--depth", type=int, default=99, help="deepest level offered (1 = roots)")
    ap.add_argument("--node-text", default="path", choices=["name", "path", "kw", "desc", "incl"])
    ap.add_argument("--emb-text", default="kw", choices=["name", "path", "kw", "desc", "incl"])
    ap.add_argument("--output", default="one", choices=["one", "top3"])
    ap.add_argument("--reason", default="none", choices=["none", "short"])
    ap.add_argument("--think", default="off", choices=["off", "on"])
    ap.add_argument("--shots", type=int, default=0)
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--k", type=int, default=30)
    ap.add_argument("--rerank", action="store_true")
    ap.add_argument("--beam", type=int, default=1, choices=[1, 2])
    ap.add_argument("--chooser", default="desc", choices=["desc", "both"])
    ap.add_argument("--no-none", action="store_true", help="do not offer KEINE (nothing fits)")
    ap.add_argument("--samples", type=int, default=1, help="self-consistency samples (use --temperature > 0)")
    ap.add_argument("--vote", default="level_majority", choices=sorted(VOTES))
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--rules", default=None, help="rules file inserted into the system prompt ('#' lines dropped); default off")
    ap.add_argument("--keep-outside", action="store_true",
                    help="keep answers naming a valid node outside the offered candidates (default: drop -> abstain)")
    ap.add_argument("--rules-candidates", action="store_true",
                    help="retrieve: add the WZ codes cited in the --rules file to the candidates (default off)")
    ap.add_argument("--node-desc", default=None, help="node description file (default results/E49/node_desc/<schema>.jsonl)")
    ap.add_argument("--dev", default=DEV)
    ap.add_argument("--hosts", default=None, help="file with hosts to run (default: all dev hosts)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out-dir", default="results/E49/preds")
    ap.add_argument("--env", default=DEFAULT_ENV)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    a = ap.parse_args()

    tree = load_schema(a.schema)
    nd = Path(a.node_desc or f"results/E49/node_desc/{tree.name}.jsonl")
    n_desc = tree.attach_descriptions(nd)
    if "desc" in (a.node_text, a.emb_text) and n_desc < len(tree):
        sys.exit(f"node_text desc needs descriptions for all nodes: {n_desc}/{len(tree)} in {nd} (run gen_node_desc.py)")
    if a.rules_candidates and not a.rules:
        sys.exit("--rules-candidates needs --rules")
    cfg = dict(DEFAULTS, strategy=a.strategy, input=a.input, depth=a.depth, node_text=a.node_text, emb_text=a.emb_text,
               output=a.output, reason=a.reason, think=a.think, shots=a.shots, lang=a.lang, k=a.k, rerank=a.rerank,
               beam=a.beam, chooser=a.chooser, allow_none=not a.no_none, temperature=a.temperature,
               rules=load_rules(a.rules) if a.rules else None, keep_outside=a.keep_outside)
    if a.rules_candidates:
        cfg["rules_cands"] = rules_code_ids(tree, cfg["rules"])
    tag = make_tag(cfg, a.model, a.samples, Path(a.rules).stem if a.rules else None)
    recs = [json.loads(l) for l in open(a.dev, encoding="utf-8") if l.strip()]
    if a.hosts:
        want = {l.strip() for l in open(a.hosts) if l.strip()}
        recs = [r for r in recs if r["host"] in want]
    if a.limit:
        recs = recs[: a.limit]
    out = Path(a.out_dir) / tree.name / f"{tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["host"] for l in out.open()} if out.exists() else set()
    todo = [r for r in recs if r["host"] not in done]
    client = Client(a.env, a.cache, max_parallel=a.workers)
    print(f"{tag}: {len(todo)} hosts to do ({len(done)} done) -> {out}", flush=True)

    def one(rec):
        t0 = time.time()
        if a.samples <= 1:
            p = predict(client, a.model, tree, rec, cfg)
        else:
            runs = [predict(client, a.model, tree, rec, dict(cfg, seed=s)) for s in range(a.samples)]
            main = VOTES[a.vote](tree, [r["main"] for r in runs])
            usage = {k: sum(r["usage"][k] for r in runs) for k in runs[0]["usage"]}
            p = {"main": main, "ranked": [main] if main else [], "path": tree.path(main) if main else [],
                 "confidence": sum(r["main"] == main for r in runs) / len(runs),
                 "error": next((r.get("error") for r in runs if r.get("error")), None), "usage": usage,
                 "trace": [], "samples": [r["main"] for r in runs]}
        p.setdefault("error", None)
        return {"host": rec["host"], "schema": tree.name, "tag": tag, "model": a.model, "cfg": cfg,
                "latency_s": round(time.time() - t0, 2), **p}

    lock = threading.Lock()
    stats = {"n": 0, "err": 0, "abstain": 0, "calls": 0, "cached": 0, "prompt_tokens": 0, "completion_tokens": 0,
             "embed_tokens": 0, "rerank_tokens": 0, "latency_s": 0.0}
    t0 = time.time()
    with out.open("a", encoding="utf-8") as f, ThreadPoolExecutor(a.workers) as ex:
        for rec in ex.map(one, todo):
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                stats["n"] += 1
                stats["err"] += bool(rec["error"])
                stats["abstain"] += rec["main"] is None
                for k in ("calls", "cached", "prompt_tokens", "completion_tokens", "embed_tokens", "rerank_tokens"):
                    stats[k] += rec["usage"].get(k, 0)
                stats["latency_s"] += rec["latency_s"]
    n = max(stats["n"], 1)
    print(json.dumps({"tag": tag, **stats, "latency_s_per_host": round(stats["latency_s"] / n, 2),
                      "calls_per_host": round(stats["calls"] / n, 2),
                      "tokens_per_host": round((stats["prompt_tokens"] + stats["completion_tokens"]) / n),
                      "wall_s": round(time.time() - t0, 1)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
