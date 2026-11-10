# E50 screening, wz, heldout300 e49_noimprint (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | c1500 | 30 | 0.000 | 0.000 | 0.833 | 0.700 | 0.667 | 0.567 | 0.533 | 0.862 | 0.750 | 0.714 | 0.607 | 0.640 | 0.933 | 1.00 | 2935 | 0 | 26 | 0 | 3198 | 3198 | 4.5 |
| gemma | r-none | c1500 | 30 | 0.000 | 0.000 | 0.833 | 0.733 | 0.700 | 0.667 | 0.633 | 0.833 | 0.733 | 0.700 | 0.690 | 0.679 | 1.000 | 1.00 | 3000 | 160 | 29 | 0 | 3129 | 3289 | 5.5 |
| qwen | r-none | c1500 | 30 | 0.000 | 0.000 | 0.800 | 0.733 | 0.667 | 0.633 | 0.600 | 0.828 | 0.759 | 0.690 | 0.655 | 0.643 | 0.967 | 1.00 | 2935 | 0 | 25 | 0 | 3182 | 3182 | 4.9 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
