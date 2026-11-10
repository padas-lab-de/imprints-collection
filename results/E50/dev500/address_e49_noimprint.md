# E50 screening, address, dev500 e49_noimprint (L* = 1)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | P@1 | P@2 | cov@1 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| agentworld | r-none | c3000 | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| agentworld | r-none | f-schema | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| agentworld | r-none | f-schema__mode-main | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| agentworld | r-none | mode-main | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| agentworld | r-short | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| agentworld | r-short | joint-poi-wz-address | 42 | 0.000 | 0.024 | 0.595 | 0.000 | 0.595 |  | 1.000 | 1.00 | 26504 | 22679 | 150 | 0 | 5329 | 28008 | 4.5 |
| gemma | r-low | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-none | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-none | c3000 | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-none | f-schema | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-none | f-schema__mode-main | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-none | mode-main | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-short | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| gemma | r-short | joint-poi-wz-address | 42 | 0.000 | 0.000 | 0.452 | 0.000 | 0.452 |  | 1.000 | 1.00 | 26780 | 23424 | 131 | 0 | 4668 | 28092 | 6.7 |
| qwen | r-default | joint-poi-wz-address | 42 | 0.071 | 0.071 | 0.952 | 0.000 | 0.952 |  | 1.000 | 1.00 | 26526 | 22195 | 2113 | 2068 | 25458 | 47653 | 33.0 |
| qwen | r-low | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| qwen | r-none | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| qwen | r-none | c3000 | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| qwen | r-none | f-schema | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| qwen | r-none | f-schema__mode-main | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| qwen | r-none | mode-main | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| qwen | r-short | base | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |  | 1.000 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |

## Reasoning level vs base level (per model, paired, acc@1)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 42 | +0.000 | [+0.000, +0.000] | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| gemma | r-low | r-none | 42 | +0.000 | [+0.000, +0.000] | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| gemma | r-short | r-none | 42 | +0.000 | [+0.000, +0.000] | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| qwen | r-low | r-none | 42 | +0.000 | [+0.000, +0.000] | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| qwen | r-short | r-none | 42 | +0.000 | [+0.000, +0.000] | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c3000 | agentworld+gemma+qwen | 42 | +0.000 | [+0.000, +0.000] | agentworld +0.000, gemma +0.000, qwen +0.000 | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| f-schema | agentworld+gemma+qwen | 42 | +0.000 | [+0.000, +0.000] | agentworld +0.000, gemma +0.000, qwen +0.000 | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| f-schema__mode-main | agentworld+gemma+qwen | 42 | +0.000 | [+0.000, +0.000] | agentworld +0.000, gemma +0.000, qwen +0.000 | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |
| mode-main | agentworld+gemma+qwen | 42 | +0.000 | [+0.000, +0.000] | agentworld +0.000, gemma +0.000, qwen +0.000 | +0.000 | 0/0 | 1.000 | 0.00 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).

Address: acc@1 = main_ok (main address equal on street, number, postcode, town, or both without a main address); acc@2 = main exact over all hosts; P@2 = main exact among hosts where reference and prediction both have a main address (cov@2 = their share).
