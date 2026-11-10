"""E50: chat wrapper over the E49 innkube client (same disk cache, same request body for the E49 settings).

Reasoning setting (one per model and run):
  none     reasoning_effort "none"                        (E49 think off; body identical to E49)
  short    reasoning_effort "none" + a "begruendung" field in the answer format (E49 --reason short)
  low | medium | high | xhigh   reasoning_effort = level, max_tokens >= REASON_MAX_TOKENS
  default  no reasoning_effort, max_tokens >= 6000        (E49 --think on; body identical to E49)
Model notes (probes 2026-11-10): gemma4-31b-it reasons only with low/medium/high; qwen38-27b accepts
none/low/medium/xhigh (high = HTTP 400, default = xhigh); qwen-agentworld reasons fully at any level but none.

Output format: free (no response_format), json_object, schema (response_format json_schema, strict).
Usage2 adds cached prompt tokens (server prefix cache), reasoning tokens, cut replies (finish_reason length)
and proxy-fast calls (latency < 0.5 s: probably a LiteLLM cache hit; their latency is not a real cost).
Never prints the endpoint or the key. Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E49"))
from client import DEFAULT_CACHE, DEFAULT_ENV, Client, Usage, parse_json  # noqa: E402,F401

REASONING = ("none", "short", "low", "medium", "high", "xhigh", "default")
EFFORTS = ("low", "medium", "high", "xhigh")
REASON_MAX_TOKENS = 8000
E49_THINK_MAX_TOKENS = 6000
FAST_S = 0.5


class Usage2(Usage):
    def __init__(self):
        super().__init__()
        self.cached_prompt_tokens = 0
        self.reasoning_tokens = 0
        self.truncated = 0
        self.fast_calls = 0


def build_body(model: str, messages: list[dict], *, max_tokens: int, reasoning: str = "none",
               response_format: dict | None = None, temperature: float = 0.0, seed: int | None = None) -> dict:
    if reasoning not in REASONING:
        raise ValueError(f"unknown reasoning setting {reasoning!r}")
    body = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": messages}
    if reasoning in ("none", "short"):
        body["reasoning_effort"] = "none"
    elif reasoning == "default":
        body["max_tokens"] = max(max_tokens, E49_THINK_MAX_TOKENS)
    else:
        body["reasoning_effort"] = reasoning
        body["max_tokens"] = max(max_tokens, REASON_MAX_TOKENS)
    if seed is not None:
        body["seed"] = seed
    if response_format is not None:
        body["response_format"] = response_format
    return body


def add_usage(usage: Usage | None, resp: dict, lat: float, cached: bool) -> None:
    if usage is None:
        return
    u = resp.get("usage") or {}
    usage.calls += 1
    usage.cached += cached
    usage.prompt_tokens += u.get("prompt_tokens") or 0
    usage.completion_tokens += u.get("completion_tokens") or 0
    usage.latency_s += lat
    if isinstance(usage, Usage2):
        usage.cached_prompt_tokens += (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
        usage.reasoning_tokens += (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        ch = (resp.get("choices") or [{}])[0]
        usage.truncated += ch.get("finish_reason") == "length"
        usage.fast_calls += lat < FAST_S


class LLM(Client):
    def chat2(self, model: str, messages: list[dict], usage: Usage | None = None, *, max_tokens: int,
              reasoning: str = "none", response_format: dict | None = None, temperature: float = 0.0,
              seed: int | None = None) -> tuple[dict, str]:
        """Return (parsed JSON object, reply text). Raises ValueError if the reply has no JSON object
        ("cut" is added to the message when the reply stopped at max_tokens)."""
        body = build_body(model, messages, max_tokens=max_tokens, reasoning=reasoning,
                          response_format=response_format, temperature=temperature, seed=seed)
        resp, lat, cached = self._post("/chat/completions", body, "chat")
        add_usage(usage, resp, lat, cached)
        ch = (resp.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        txt = msg.get("content") or ""
        if not txt.strip() and reasoning in ("none", "short"):
            txt = msg.get("reasoning_content") or msg.get("reasoning") or ""
        try:
            return parse_json(txt), txt
        except ValueError as e:
            if ch.get("finish_reason") == "length":
                raise ValueError("cut at max_tokens; " + str(e)) from None
            raise
