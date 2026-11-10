# E50 screening, wz, heldout300 all (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | c1500 | 294 | 0.000 | 0.000 | 0.837 | 0.776 | 0.721 | 0.690 | 0.616 | 0.840 | 0.784 | 0.729 | 0.702 | 0.663 | 0.990 | 1.00 | 3104 | 0 | 28 | 0 | 3383 | 3383 | 4.2 |
| gemma | r-none | c1500 | 294 | 0.000 | 0.000 | 0.854 | 0.799 | 0.765 | 0.741 | 0.684 | 0.854 | 0.802 | 0.771 | 0.752 | 0.720 | 0.993 | 1.00 | 3187 | 159 | 29 | 0 | 3316 | 3475 | 4.5 |
| qwen | r-none | c1500 | 294 | 0.000 | 0.000 | 0.840 | 0.803 | 0.745 | 0.724 | 0.680 | 0.852 | 0.814 | 0.755 | 0.737 | 0.707 | 0.986 | 1.00 | 3104 | 0 | 25 | 0 | 3352 | 3352 | 4.5 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
