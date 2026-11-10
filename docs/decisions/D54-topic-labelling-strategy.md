# D54-topic-labelling-strategy

Issued 2026-11-10. Replaces D53 (model choice moves to the model evaluation after gold labelling).
Blocks: the strategy that the model evaluation measures and the full run uses.

## Order of work (user, 2026-11-10)
1. Strategy (this card) -> 2. gold labelling -> 3. model evaluation (efficiency vs effectiveness) -> 4. full run (topics + addresses) with strategy (1) and model (3).

## Already settled by E49 evidence (model-independent; same result for gemma and qwen)
- Prompt form: POI flat (all leaves in one prompt; beat hierarchical top-down in stage 1). WZ retrieve k30 (embedding shortlist of 30 codes with path text; beat flat and hierarchical in stage 1).
- Reasoning on; input landing + imprint; POI node names English + German (+2.4 to +4.2 P@2).
- No WZ hint rules (D52), no self-consistency (no gain in stage 3).
- Gold labels at the finest level the annotator can decide (D51) work for every option below, so labelling does not wait for this card.

## Open: how many models, and how deep
Evidence (held-out 100 hosts unless marked; P@L = precision of hosts labelled at L; acc@L strict):
| schema | setup | P@2 | P@3 | acc@2 | cov@2 | calls |
|---|---|---|---|---|---|---|
| POI | gemma single | .867 | - | .814 | 1.00 | 1 |
| POI | qwen single | .854 | - | .794 | .99 | 1 |
| POI | ens2 | .914 | - | .784 | .90 | 2 |
| WZ | gemma single | .827 | .806 | .818 | .99 | 1 |
| WZ | qwen single | .794 | .753 | .778 | .98 | 1 |
| WZ | ens2 | .854 | .828 | .768 | .90 | 2 |
Dev agrees: WZ gemma single acc@2 .774 vs ens2 .719; POI ens2 P@2 .914, cov@2 .87.
Reading: ens2 buys about +5 pts precision on 87-90% of hosts and labels the rest shallower; strict accuracy is the same or lower than the best single model; it costs 2x calls.

## Options
- **A (recommended) Single model, full depth, fixed cut-off.** One call per schema per host. The model predicts down to the leaf; the dataset publishes each path down to the deepest level with P >= 0.8 on the gold set for the chosen model (set in the model evaluation; today POI L2, WZ L3 for gemma). Optional: keep the full path with a flag beyond the cut-off.
- **B Adaptive ens2 for both schemas.** Two models, keep the path while they agree. Highest precision, depth varies per host (10-20% shallower), 2x cost; model evaluation picks a pair.
- **C Mixed (stand of D51 B / D52).** POI single model; WZ ens2.
- **D Top level only.** POI 8 roots, WZ 21 sections. Cheapest prompts, but drops the detail the schemas were built for; A can still cut at L1 if a model is weak.

## Answer
(open)
