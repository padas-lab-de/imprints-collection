# E50 screening, wz, heldout300 e49 (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | c1500 | 99 | 0.000 | 0.000 | 0.818 | 0.737 | 0.687 | 0.636 | 0.586 | 0.827 | 0.753 | 0.701 | 0.649 | 0.624 | 0.980 | 1.00 | 3152 | 0 | 26 | 0 | 3411 | 3411 | 4.4 |
| gemma | r-none | c1500 | 99 | 0.000 | 0.000 | 0.859 | 0.798 | 0.788 | 0.768 | 0.737 | 0.859 | 0.798 | 0.788 | 0.776 | 0.760 | 1.000 | 1.00 | 3229 | 158 | 29 | 0 | 3360 | 3518 | 5.0 |
| qwen | r-none | c1500 | 99 | 0.000 | 0.000 | 0.798 | 0.747 | 0.687 | 0.667 | 0.626 | 0.814 | 0.763 | 0.701 | 0.680 | 0.660 | 0.980 | 1.00 | 3152 | 0 | 25 | 0 | 3399 | 3399 | 4.7 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
