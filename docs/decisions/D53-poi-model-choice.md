# D53-poi-model-choice

Issued 2026-11-10. Blocks: the POI setup for the full-corpus run.

## Question
D51 B chose qwen38-27b (flat, think, input both) for POI at level 2. Later runs (POI v3, --node-lang both; results/E49/poi3c/summary.md) compare it with gemma4-31b-it (flat, reason, input both) and with their level-majority ens2. Which POI setup for the full run?

## Evidence (P@2 / acc@2 / cov@2)
| config | dev (199) | held-out (97) | out tokens/host |
|---|---|---|---|
| qwen b | .852 / .784 / .979 | .854 / .794 / .989 | ~600 |
| gemma b | .855 / .799 / .995 | .867 / .814 / 1.000 | ~67 |
| ens2 qwen+gemma | .914 / .759 / .872 | .914 / .784 / .900 | sum |
gemma vs qwen: no significant difference (CI half-width ~.04-.05), gemma abstains less (3 vs 10 on dev), no failed replies. ens2: P@2 +.05-.06 (CI > 0), acc@2 -2 to -5 pts, 10-13% of hosts unlabelled at L2, 2x cost.

## Options
- **A (recommended)** gemma b single model; qwen b as fallback. Same quality, fewer abstentions, 8-10x fewer output tokens.
- **B** Keep qwen b (D51 B as answered).
- **C** ens2 like WZ: higher precision subset, lower coverage, 2x cost.

## Answer
(open)
