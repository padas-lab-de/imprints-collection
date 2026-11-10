# D51-topic-schema-depth · Topic study (E49): which level and setup per schema, and how deep do gold labels go?
Issued 2026-11-10. Blocks: gold labelling tool/guideline topic fields; pipeline topic step.

Evidence: results/E49/stage3/summary.md (200 dev hosts, agent references; WZ rule gains optimistic, check on gold).

**Recommend B:** the adaptive WZ setup is the only one with precision >= 0.8 down to the unterklasse, and labels at the finest decidable level let the gold set check every level later.
- **A** fixed levels: POI level 2 (qwen38-27b, reason first, homepage+imprint; P .87, acc .80). WZ level 3 Gruppe (qwen38-27b, 30 retrieved candidates + rules; P .82, acc .80, 2 s/host). Gold labels: POI leaf, WZ to Gruppe (287 options). Cheapest for annotators.
- **B** POI as A. WZ adaptive: gemma4-31b + qwen38-27b both predict, keep the deepest level they agree on (P >= .83 at every level; 79% reach unterklasse, 12% no code; 7 s/host). Gold labels: both schemas at the finest level the annotator can decide (may stop higher, rule R6).
- **C** coarse only: POI level 1 (8 roots), WZ Abschnitt (22). Precision .94/.87, low information.

Answer (user, 2026-11-10): "D51 B." POI level 2 (qwen think, homepage+imprint); WZ adaptive ens2 (gemma + qwen, rules, keepout, deepest agreed level); gold labels both schemas at the finest level the annotator can decide.
