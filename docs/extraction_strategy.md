# Extraction strategy (topics and addresses)

Status 2026-11-10. Decided in D51, D52, D54 from E49-topic-schema-strategy. Model-independent; the model is chosen in the model evaluation (E52) after gold labelling.

Order of work: strategy (this file) -> prompt study E50 (fixes the prompts) -> gold labelling -> model evaluation E52 (efficiency vs effectiveness; picks model, and single vs ensemble) -> full run (topics + addresses) on all imprints.

## Topics
| | POI (topics/poi_v3.jsonl, 2 levels) | WZ 2025 (topics/wz2025.jsonl, 5 levels) |
|---|---|---|
| Prompt form | retrieve: 30 candidates by embedding similarity, model picks one (user 2026-11-12: cheaper form accepted; flat is -0.027 better on dev and stays a variant for E52) | retrieve: 30 candidates by embedding similarity (emb text: keywords), model picks one |
| Node text | "English (Deutsch)" (`--node-lang both`) | full path |
| Reasoning | on, short (or low, per model) | none (E50: reasoning gives no gain) |
| Input | landing page + imprint, 6000 chars | landing page + imprint, 1500 chars per field |
| Not used | hierarchical top-down, self-consistency | hint rules (D52), hierarchical, self-consistency |
| Default | one model | one model |
| Depth | predict to the leaf; publish down to the deepest level with P >= 0.8 on the gold set for the chosen model | same |
| Variants for E52 | ens2 level majority of two models (descends while they agree) | same |

Gold labels: finest level the annotator can decide (D51), so every variant can be scored.

## Prompt configuration (fixed by E50, 2026-11-10)
Frozen in `results/E50/final_config.md`; evidence in `results/E50/heldout300/final.md` (dev 500 and held-out 300, per part, 95% CIs). Scores are agreement with reference labels, not gold.

- One call per schema (POI, WZ, address). Joint calls lose 0.02 to 0.20.
- Base wording, German instructions, site text first. No variant of wording, language or output format won.
- POI: retrieve k30 (about 0.21 of the flat cost; -0.027 acc@2 [-0.049, -0.008] on dev 500). User 2026-11-12: "the cheaper one is okay if the loss is just so little". Flat (about 25k tokens per host) stays an E52 variant to measure the loss on gold. Schema first with question last: rejected (-0.053).
- WZ: retrieve k30, no reasoning, 1500 chars per field (non-inferior to 6000, 0.84 of the cost).
- Address: main address only (user 2026-11-12: "only main address is okay"). Mode main, JSON schema output, no reasoning, imprint text only. No imprint text -> no call. Mode main does not give the full address list (all-address recall about 0.80).

Held-out 300 (run once), best of three models: POI acc@2 0.760, WZ acc@3 0.765, address main_ok 0.983.
