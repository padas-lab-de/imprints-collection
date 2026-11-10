# E50 screening, wz, heldout300 e51 (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | c1500 | 195 | 0.000 | 0.000 | 0.846 | 0.795 | 0.738 | 0.718 | 0.631 | 0.846 | 0.799 | 0.742 | 0.729 | 0.683 | 0.995 | 1.00 | 3080 | 0 | 29 | 0 | 3369 | 3369 | 4.1 |
| gemma | r-none | c1500 | 195 | 0.000 | 0.000 | 0.851 | 0.800 | 0.754 | 0.728 | 0.656 | 0.851 | 0.804 | 0.762 | 0.740 | 0.699 | 0.990 | 1.00 | 3165 | 160 | 29 | 0 | 3294 | 3454 | 4.3 |
| qwen | r-none | c1500 | 195 | 0.000 | 0.000 | 0.862 | 0.831 | 0.774 | 0.754 | 0.708 | 0.870 | 0.839 | 0.782 | 0.766 | 0.730 | 0.990 | 1.00 | 3080 | 0 | 25 | 0 | 3328 | 3328 | 4.4 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
