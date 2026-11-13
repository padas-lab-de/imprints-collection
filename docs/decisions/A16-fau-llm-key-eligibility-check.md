# A16-fau-llm-key-eligibility-check (issued 2026-11-13)

User asked (2026-11-13): can we use the NHR@FAU LLM inference endpoint (https://hpc.fau.de/2026/10/25/almost-500-api-key-for-llms-as-a-service-at-nhrfau-issued/)?

Research (sonnet agent, read-only; hpc.fau.de is behind a JavaScript proof-of-work bot check, so only search snippets and a third-party README were read; not verified):
- OpenAI-compatible gateway, base URL https://hub.nhr.fau.de/api/llmgw/v1, key in LLMAPI_KEY (request page snippet).
- "Eligible users" section with three classes, not readable; ~70% of keys went to FAU members (2026-06-22 post), so some non-FAU users exist. Keys at NHR@FAU's discretion, revocable; yearly short usage report on request.
- Models (third-party README, 2026-10): DeepSeek-V4-Flash, gpt-oss-120b, Qwen3.6-35B-A3B-FP8, gemma-4-E4B-it; list changes with GPUs (~3 GPUs, unfunded, experimental).
- Unknown: rate limits, quotas, JSON-schema support, batch API, logging and bulk-use terms.
- Lead view: possible extra E52 candidates (DeepSeek-V4-Flash, gpt-oss-120b); not a path for the full run.

Action for the user: open https://hpc.fau.de/request-llm-api-key in a normal browser, read "Eligible users" and the terms (rate limits, bulk use, logging). If Uni Passau is eligible and you want the extra candidates, request a key and put it in .env as LLMAPI_KEY. Unblocks: FAU models as E52 candidates.

Answer: (open)
