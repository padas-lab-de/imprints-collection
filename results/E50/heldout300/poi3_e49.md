# E50 screening, poi3, heldout300 e49 (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 97 | 0.000 | 0.000 | 0.856 | 0.742 | 0.361 | 0.865 | 0.809 | 0.778 | 0.918 | 1.00 | 24043 | 0 | 76 | 0 | 24800 | 24800 | 3.2 |
| gemma | r-short | base | 97 | 0.000 | 0.000 | 0.948 | 0.804 | 0.433 | 0.948 | 0.867 | 0.894 | 0.928 | 1.00 | 24238 | 128 | 68 | 0 | 24793 | 24921 | 0.1 |
| qwen | r-low | base | 97 | 0.000 | 0.000 | 0.918 | 0.753 | 0.443 | 0.947 | 0.811 | 0.878 | 0.928 | 1.00 | 24052 | 0 | 467 | 444 | 28720 | 28720 | 14.2 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
