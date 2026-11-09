"""E49: innkube client (chat, embeddings, rerank) with an on-disk response cache and usage counters.

- chat: temperature 0 by default, JSON answer parsed from the first {...} in the reply, retries.
- cache: datasets/E49/cache/<kind>/<sha256 of the request body>.json; a cache hit costs no call
  (counted as cached; tokens of the original call are still reported so that cost per strategy
  does not depend on the cache state).
- never prints the endpoint or the key.
Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ENV = "/home/dinzinger/GitLab/fim/imprints-collection/.env"
DEFAULT_CACHE = "/home/dinzinger/GitLab/fim/imprints-collection/datasets/E49/cache"


def load_env(path: str | Path) -> dict:
    env = {}
    for line in Path(path).read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Z_]+)\s*=\s*(.*)", line)
        if m:
            env[m.group(1)] = m.group(2).strip().strip("'\"")
    return {k: re.sub(r"\$\{(\w+)\}", lambda m: env.get(m.group(1), ""), v) for k, v in env.items()}


def parse_json(txt: str):
    """First JSON object in a reply (code fences, leading reasoning text and repeats allowed)."""
    txt = txt or ""
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S)
    dec = json.JSONDecoder(strict=False)
    for m in re.finditer(r"\{", txt):
        try:
            obj, _ = dec.raw_decode(txt[m.start():])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON object in reply: " + txt[:200].replace("\n", " "))


class Usage:
    """Per-prediction counters (one instance per host x strategy run)."""

    def __init__(self):
        self.calls = 0
        self.cached = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.embed_tokens = 0
        self.rerank_tokens = 0
        self.latency_s = 0.0

    def as_dict(self) -> dict:
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in self.__dict__.items()}


class Client:
    def __init__(self, env_path: str = DEFAULT_ENV, cache_dir: str = DEFAULT_CACHE, max_parallel: int = 8):
        env = load_env(env_path)
        self.base = env["MODEL_API_ENDPOINT"].rstrip("/")
        self._key = env["MODEL_API_KEY"]
        self.cache = Path(cache_dir)
        self.sem = threading.Semaphore(max_parallel)

    # -- transport ---------------------------------------------------------------------------------
    def _post(self, path: str, body: dict, kind: str, timeout: int = 300) -> tuple[dict, float, bool]:
        key = hashlib.sha256(json.dumps([path, body], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        f = self.cache / kind / key[:2] / f"{key}.json"
        if f.is_file():
            rec = json.loads(f.read_text())
            return rec["response"], rec.get("latency_s", 0.0), True
        req = urllib.request.Request(
            self.base + path, data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + self._key, "Content-Type": "application/json"})
        last = None
        for attempt in range(5):
            try:
                with self.sem:
                    t0 = time.time()
                    with urllib.request.urlopen(req, timeout=timeout) as r:
                        resp = json.load(r)
                    lat = time.time() - t0
                break
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}"
                if e.code in (400, 401, 403, 404, 422):
                    raise RuntimeError(last) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                last = f"{type(e).__name__}: {e}"
            time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(last)
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp%d" % threading.get_ident())
        tmp.write_text(json.dumps({"request": body, "response": resp, "latency_s": lat}, ensure_ascii=False))
        tmp.replace(f)
        return resp, lat, False

    # -- API -----------------------------------------------------------------------------------------
    def chat(self, model: str, messages: list[dict], usage: Usage | None = None, *, max_tokens: int = 800,
             temperature: float = 0.0, seed: int | None = None, think: bool = False, want_json: bool = True):
        """Return (parsed JSON or text, raw text). think=False sends reasoning_effort none (Qwen reasoning off)."""
        body = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": messages}
        if not think:
            body["reasoning_effort"] = "none"
        else:
            body["max_tokens"] = max(max_tokens, 6000)
        if seed is not None:
            body["seed"] = seed
        resp, lat, cached = self._post("/chat/completions", body, "chat")
        if usage is not None:
            u = resp.get("usage") or {}
            usage.calls += 1
            usage.cached += cached
            usage.prompt_tokens += u.get("prompt_tokens") or 0
            usage.completion_tokens += u.get("completion_tokens") or 0
            usage.latency_s += lat
        msg = resp["choices"][0]["message"] if resp.get("choices") else {}
        txt = msg.get("content") or ""
        if not txt.strip() and not think:
            # some served models (soofi) return the whole answer as reasoning_content when reasoning is off
            txt = msg.get("reasoning_content") or msg.get("reasoning") or ""
        return (parse_json(txt) if want_json else txt), txt

    def embed(self, texts: list[str], usage: Usage | None = None, model: str = "octen-embedding-8b",
              batch: int = 32) -> list[list[float]]:
        out = []
        for i in range(0, len(texts), batch):
            resp, lat, cached = self._post("/embeddings", {"model": model, "input": texts[i:i + batch]}, "embed")
            out += [d["embedding"] for d in sorted(resp["data"], key=lambda d: d["index"])]
            if usage is not None:
                usage.embed_tokens += (resp.get("usage") or {}).get("prompt_tokens") or 0
                usage.latency_s += lat
        return out

    def rerank(self, query: str, docs: list[str], usage: Usage | None = None,
               model: str = "qwen3-reranker-4b") -> list[float]:
        resp, lat, cached = self._post("/rerank", {"model": model, "query": query, "documents": docs}, "rerank")
        scores = [0.0] * len(docs)
        for r in resp["results"]:
            scores[r["index"]] = r["relevance_score"]
        if usage is not None:
            usage.rerank_tokens += ((resp.get("meta") or {}).get("tokens") or {}).get("input_tokens") or 0
            usage.latency_s += lat
        return scores
