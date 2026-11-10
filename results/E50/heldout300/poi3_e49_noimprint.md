# E50 screening, poi3, heldout300 e49_noimprint (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 28 | 0.000 | 0.000 | 0.821 | 0.571 | 0.250 | 0.852 | 0.696 | 0.583 | 0.821 | 1.00 | 23475 | 0 | 74 | 0 | 24212 | 24212 | 3.2 |
| gemma | r-short | base | 28 | 0.000 | 0.000 | 0.929 | 0.679 | 0.429 | 0.929 | 0.792 | 1.000 | 0.857 | 1.00 | 23655 | 128 | 70 | 0 | 24223 | 24351 | 0.1 |
| qwen | r-low | base | 28 | 0.000 | 0.000 | 0.857 | 0.643 | 0.429 | 0.923 | 0.750 | 0.923 | 0.857 | 1.00 | 23484 | 0 | 428 | 405 | 27760 | 27760 | 13.4 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
