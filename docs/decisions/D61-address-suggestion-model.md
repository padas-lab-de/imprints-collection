# D61-address-suggestion-model

Issued 2026-11-13 (E53-gold-set-redraw). Blocks: the prefill step (after the draw and capture), not the draw.

Question: annotators see a model's address suggestion (D24 B). That model's address score is then biased upward, because annotators tend to accept suggestions. All innkube models (qwen38-27b, gemma4-31b-it, qwen3-next-80b, qwen-agentworld-35b-a3b) are E52 candidates. Which model makes the suggestions?

- **A (recommended)** A paid API model that is not an E52 candidate (e.g. a Claude model). About 1,500 imprint texts, address task only; dry-run cost estimate first, must stay under $20 per run (ledger docs/cost_ledger.csv). All candidates are then scored without this bias. The paid model is not reported as a candidate.
- **B** An innkube candidate makes the suggestions; its address score is reported as "suggestion model, upward-biased". Free; one candidate is compromised for the address comparison.
- **C** No address suggestions (reverses D24 B). No bias; labelling is slower.

## Outcome
(open)
