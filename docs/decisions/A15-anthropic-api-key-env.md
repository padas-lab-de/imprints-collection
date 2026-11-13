# A15-anthropic-api-key-env

Issued 2026-11-13 (E53, after D61 A). Blocks: the address-suggestion prefill (not the draw or the capture).

No Anthropic credential is on this machine (.env has no ANTHROPIC_API_KEY; no `ant` profile). Add a line `ANTHROPIC_API_KEY=...` to `.env` in the repository root (never committed). Spend: claude-haiku-5-5, at most about $10 for all suggestion generation (D61), inside the $20/run and $30/day limits; every run is logged in docs/cost_ledger.csv.

## Outcome
(open)
