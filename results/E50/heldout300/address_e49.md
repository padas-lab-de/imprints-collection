# E50 screening, address, heldout300 e49 (L* = 1)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | P@1 | P@2 | cov@1 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | f-schema__mode-main | 100 | 0.000 | 0.000 | 0.950 | 0.620 | 0.950 | 0.939 | 1.000 | 0.70 | 733 | 0 | 34 | 0 | 1076 | 1076 | 0.5 |
| gemma | r-none | f-schema__mode-main | 100 | 0.000 | 0.000 | 0.980 | 0.650 | 0.980 | 0.985 | 1.000 | 0.70 | 762 | 155 | 36 | 0 | 965 | 1120 | 0.7 |
| qwen | r-none | f-schema__mode-main | 100 | 0.000 | 0.000 | 0.980 | 0.640 | 0.980 | 0.970 | 1.000 | 0.70 | 733 | 0 | 47 | 0 | 1201 | 1201 | 0.9 |

## Reasoning level vs base level (per model, paired, acc@1)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).

Address: acc@1 = main_ok (main address equal on street, number, postcode, town, or both without a main address); acc@2 = main exact over all hosts; P@2 = main exact among hosts where reference and prediction both have a main address (cov@2 = their share).
