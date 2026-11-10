# D52-wz-rules-after-heldout

Issued 2026-11-10. Blocks: the WZ setup for the gold set and the full run.

## Question
D51 B chose for WZ: ens2 (gemma4-31b-it + qwen38-27b, level majority) with retrieve k30, hint rules and keep-outside. Stage 3b added rules-candidates. The held-out check (100 new hosts, results/E49/heldout/summary.md) shows that the rules gain does not replicate. Keep the rules or drop them?

## Evidence
| ens2 | dev acc@2 | held-out acc@2 | held-out P@2 | held-out no code | tokens/host (held-out) |
|---|---|---|---|---|---|
| (a) no rules | .764* | .768 | .854 | 6 | 6.7k |
| (b) rules + keep-outside | .764 | .747 | .851 | 10 | 9.5k |
| (c) (b) + rules-candidates | .809 | .737 | .869 | 11 | 17.3k |
*dev (a) rebuilt from stage-2 preds; dev gains of (b)/(c) over (a) were +4.5/+9.0 pts at L2.
Held-out differences are not significant (sign tests p >= 0.23, bootstrap CIs include 0); dev gains lie at or above the held-out upper CI. Held-out refs: Sonnet passes, A=B 77/100 (dev 179/200).

## Options
- **A (recommended)** Drop rules and rules-candidates: ens2 of plain retrieve k30. Same or better on new hosts, fewest abstentions, cheapest. Keep wz_rules.md only as a labelling-guideline aid.
- **B** Keep D51 B as answered (rules + keep-outside, no rules-candidates). 1.4x tokens, no measured gain on new hosts.
- **C** Keep rules + rules-candidates (stage 3b). 2.6x tokens, best held-out P@2 by 1-2 hosts, more abstentions.

## Answer
(open)
