# E50 screening, poi3, heldout300 all (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 292 | 0.000 | 0.000 | 0.870 | 0.712 | 0.346 | 0.876 | 0.776 | 0.802 | 0.918 | 1.00 | 24070 | 0 | 76 | 0 | 24827 | 24827 | 3.2 |
| gemma | r-short | base | 292 | 0.000 | 0.000 | 0.880 | 0.760 | 0.408 | 0.886 | 0.810 | 0.869 | 0.938 | 1.00 | 24280 | 127 | 70 | 0 | 24850 | 24977 | 7.5 |
| qwen | r-low | base | 292 | 0.000 | 0.000 | 0.884 | 0.753 | 0.418 | 0.908 | 0.815 | 0.884 | 0.925 | 1.00 | 24079 | 0 | 473 | 450 | 28809 | 28809 | 14.2 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
