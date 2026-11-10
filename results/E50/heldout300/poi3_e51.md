# E50 screening, poi3, heldout300 e51 (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 195 | 0.000 | 0.000 | 0.877 | 0.697 | 0.338 | 0.881 | 0.760 | 0.815 | 0.918 | 1.00 | 24084 | 0 | 76 | 0 | 24840 | 24840 | 3.2 |
| gemma | r-short | base | 195 | 0.000 | 0.000 | 0.846 | 0.738 | 0.395 | 0.855 | 0.783 | 0.856 | 0.944 | 1.00 | 24301 | 127 | 70 | 0 | 24878 | 25004 | 11.2 |
| qwen | r-low | base | 195 | 0.000 | 0.000 | 0.867 | 0.754 | 0.405 | 0.889 | 0.817 | 0.888 | 0.923 | 1.00 | 24093 | 0 | 476 | 453 | 28854 | 28854 | 14.3 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
