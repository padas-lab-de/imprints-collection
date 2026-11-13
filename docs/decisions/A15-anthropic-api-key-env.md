# A15-anthropic-api-key-env

Issued 2026-11-13 (E53, after D61 A). Blocks: the address-suggestion prefill (not the draw or the capture).

No Anthropic credential is on this machine (.env has no ANTHROPIC_API_KEY; no `ant` profile). Add a line `ANTHROPIC_API_KEY=...` to `.env` in the repository root (never committed). Spend: claude-haiku-5-5, at most about $10 for all suggestion generation (D61), inside the $20/run and $30/day limits; every run is logged in docs/cost_ledger.csv.

## Outcome
User 2026-11-13: "could you use the Openrouter API key for that? Do you have it?" Yes, OpenRouter works (model anthropic/claude-haiku-5.5 via its OpenAI-compatible API; read usage.cost per call for the ledger). The repo .env holds only INNKUBE_API_KEY, so the key is not available here. Open: user adds OPENROUTER_API_KEY to .env.
