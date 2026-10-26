# D24-gold-prefill-scope (issued 2026-10-26)

**Question:** Which gold labels start from a model suggestion (accept or correct) instead of from scratch?
**Context:** The user asked for the labelling tool to pre-fill the imprint address (and whatever else can be pre-filled) so that labellers only accept or correct it (2026-10-26). This reverses D15-gold-annotation-workforce ("no model pre-labels"), whose reason was that pre-labels can anchor labellers on a model's answers and bias the model comparison (docs/gold_set_design.md).
Mitigations already built (E21-gold-prefill, commit 4f71ad3): suggestions come from qwen-agentworld-35b-a3b, which the paper does not compare (compared: qwen38-27b, gemma4-31b-it; note it is the same Qwen family as qwen38-27b). Site status and imprint URL/location come from the capture, not the model. Address fields are re-checked against the text: fields not found verbatim are flagged orange. Saved labels record `prefilled_from`. The tool flag `--prefill primary|all|none` sets the scope.

**Suggestion quality** (results/E21/spotcheck.md, 40 random live hosts): main address or its correct absence exactly right 34/40; operator type 38/40; topic 36/40; site status 39/40. 17/40 had extra rows (duplicates, banks/BaFin/IHK, town-only "Sitz" rows), none missed an address; a rule filter for these is being added.

**Recommend A:** Saves the bulk of typing on 750 of the 1,000 items and still measures anchoring: on doubly labelled items (pre-filled primary label vs. second label from scratch), compared with calibration agreement (all from scratch).
- **A** Primary labels pre-filled; second (200) and calibration (50) labels from scratch. Cost: second and calibration labels stay slow; anchoring is measurable and reportable.
- **B** All labels pre-filled. Fastest; no unassisted reference, so the paper cannot show that the gold labels are not anchored on a model.
- **C** No pre-fill (keep D15). Slowest; the cleanest gold set.

**Answer:** "D24 B" (2026-10-26): suggestions on all 1,000 items. `ic`-gold CLI default `--prefill all`.
Consequence: second-labeller and calibration agreement includes anchoring on the shared suggestion; report it as agreement with suggestions shown.
