# Extraction strategy (topics; addresses after E50)

Status 2026-11-10. Decided in D51, D52, D54 from E49-topic-schema-strategy. Model-independent; the model is chosen in the model evaluation (E52) after gold labelling.

Order of work: strategy (this file) -> prompt study E50 (fixes the prompts) -> gold labelling -> model evaluation E52 (efficiency vs effectiveness; picks model, and single vs ensemble) -> full run (topics + addresses) on all imprints.

## Topics
| | POI (topics/poi_v3.jsonl, 2 levels) | WZ 2025 (topics/wz2025.jsonl, 5 levels) |
|---|---|---|
| Prompt form | flat: all leaves in one prompt | retrieve: 30 candidates by embedding similarity (emb text: keywords), model picks one |
| Node text | "English (Deutsch)" (`--node-lang both`) | full path |
| Reasoning | on | on |
| Input | landing page + imprint | landing page + imprint |
| Not used | hierarchical top-down, self-consistency | hint rules (D52), hierarchical, self-consistency |
| Default | one model | one model |
| Depth | predict to the leaf; publish down to the deepest level with P >= 0.8 on the gold set for the chosen model | same |
| Variants for E52 | ens2 level majority of two models (descends while they agree) | same |

Gold labels: finest level the annotator can decide (D51), so every variant can be scored.

## Open until E50
Prompt wording, output format, joint vs separate calls for POI / WZ / address, input length. E50 fixes them before labelling ends.
