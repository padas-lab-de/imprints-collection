# E50 screening, address, dev500 e49 (L* = 1)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | P@1 | P@2 | cov@1 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 200 | 0.000 | 0.000 | 0.900 | 0.610 | 0.900 | 0.910 | 1.000 | 0.79 | 1011 | 0 | 60 | 0 | 1610 | 1610 | 0.9 |
| agentworld | r-none | c3000 | 200 | 0.000 | 0.000 | 0.885 | 0.595 | 0.885 | 0.915 | 1.000 | 0.79 | 882 | 338 | 58 | 0 | 1128 | 1466 | 0.3 |
| agentworld | r-none | f-schema | 200 | 0.000 | 0.000 | 0.905 | 0.610 | 0.905 | 0.910 | 1.000 | 0.79 | 1011 | 544 | 60 | 0 | 1064 | 1608 | 0.8 |
| agentworld | r-none | f-schema__mode-main | 200 | 0.000 | 0.000 | 0.945 | 0.650 | 0.945 | 0.935 | 1.000 | 0.79 | 838 | 0 | 38 | 0 | 1213 | 1213 | 0.6 |
| agentworld | r-none | mode-main | 200 | 0.000 | 0.000 | 0.945 | 0.650 | 0.945 | 0.935 | 1.000 | 0.79 | 838 | 0 | 37 | 0 | 1212 | 1212 | 0.6 |
| agentworld | r-short | base | 200 | 0.000 | 0.000 | 0.920 | 0.620 | 0.920 | 0.925 | 1.000 | 0.79 | 1023 | 496 | 93 | 0 | 1455 | 1952 | 1.0 |
| agentworld | r-short | joint-poi-wz-address | 200 | 0.000 | 0.010 | 0.835 | 0.630 | 0.835 | 0.906 | 1.000 | 1.00 | 26970 | 23000 | 162 | 0 | 5586 | 28585 | 4.6 |
| gemma | r-low | base | 200 | 0.000 | 0.000 | 0.975 | 0.670 | 0.975 | 0.964 | 1.000 | 0.79 | 1049 | 352 | 734 | 646 | 8041 | 8393 | 10.6 |
| gemma | r-none | base | 200 | 0.000 | 0.000 | 0.980 | 0.675 | 0.980 | 0.971 | 1.000 | 0.79 | 1051 | 352 | 86 | 0 | 1563 | 1914 | 1.4 |
| gemma | r-none | c3000 | 200 | 0.000 | 0.000 | 0.955 | 0.650 | 0.955 | 0.963 | 1.000 | 0.79 | 917 | 352 | 83 | 0 | 1396 | 1747 | 0.6 |
| gemma | r-none | f-schema | 200 | 0.000 | 0.000 | 0.975 | 0.670 | 0.975 | 0.964 | 1.000 | 0.79 | 1051 | 352 | 57 | 0 | 1271 | 1623 | 1.0 |
| gemma | r-none | f-schema__mode-main | 200 | 0.000 | 0.000 | 0.970 | 0.665 | 0.970 | 0.957 | 1.000 | 0.79 | 871 | 176 | 39 | 0 | 1085 | 1261 | 1.1 |
| gemma | r-none | mode-main | 200 | 0.000 | 0.000 | 0.970 | 0.665 | 0.970 | 0.957 | 1.000 | 0.79 | 871 | 175 | 57 | 0 | 1265 | 1440 | 1.0 |
| gemma | r-short | base | 200 | 0.000 | 0.000 | 0.980 | 0.675 | 0.980 | 0.971 | 1.000 | 0.79 | 1063 | 399 | 111 | 0 | 1778 | 2178 | 1.8 |
| gemma | r-short | joint-poi-wz-address | 200 | 0.000 | 0.000 | 0.845 | 0.665 | 0.845 | 0.957 | 1.000 | 1.00 | 27263 | 23190 | 160 | 0 | 5669 | 28859 | 7.4 |
| qwen | r-default | joint-poi-wz-address | 200 | 0.070 | 0.075 | 0.775 | 0.480 | 0.775 | 0.897 | 1.000 | 1.00 | 26991 | 22509 | 2283 | 2195 | 27314 | 49823 | 35.7 |
| qwen | r-low | base | 200 | 0.000 | 0.000 | 0.980 | 0.675 | 0.980 | 0.978 | 1.000 | 0.79 | 1030 | 0 | 393 | 336 | 4962 | 4962 | 6.4 |
| qwen | r-none | base | 200 | 0.000 | 0.000 | 0.965 | 0.660 | 0.965 | 0.950 | 1.000 | 0.79 | 1011 | 0 | 79 | 0 | 1805 | 1805 | 1.7 |
| qwen | r-none | c3000 | 200 | 0.000 | 0.000 | 0.945 | 0.640 | 0.945 | 0.948 | 1.000 | 0.79 | 882 | 106 | 76 | 0 | 1533 | 1638 | 0.6 |
| qwen | r-none | f-schema | 200 | 0.000 | 0.000 | 0.965 | 0.660 | 0.965 | 0.950 | 1.000 | 0.79 | 1011 | 0 | 79 | 0 | 1801 | 1801 | 1.6 |
| qwen | r-none | f-schema__mode-main | 200 | 0.000 | 0.000 | 0.975 | 0.670 | 0.975 | 0.964 | 1.000 | 0.79 | 838 | 0 | 51 | 0 | 1345 | 1345 | 1.2 |
| qwen | r-none | mode-main | 200 | 0.000 | 0.000 | 0.975 | 0.670 | 0.975 | 0.964 | 1.000 | 0.79 | 838 | 0 | 51 | 0 | 1345 | 1345 | 1.2 |
| qwen | r-short | base | 200 | 0.000 | 0.000 | 0.945 | 0.640 | 0.945 | 0.948 | 1.000 | 0.79 | 1023 | 639 | 112 | 0 | 1507 | 2146 | 1.9 |

## Reasoning level vs base level (per model, paired, acc@1)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 200 | +0.020 | [-0.015, +0.055] | +0.020 | 8/4 | 0.388 | 0.90 | no difference |
| gemma | r-low | r-none | 200 | -0.005 | [-0.025, +0.015] | -0.005 | 2/3 | 1.000 | 5.15 | no difference |
| gemma | r-short | r-none | 200 | +0.000 | [+0.000, +0.000] | +0.000 | 0/0 | 1.000 | 1.14 | no difference |
| qwen | r-low | r-none | 200 | +0.015 | [-0.010, +0.040] | +0.015 | 5/2 | 0.453 | 2.75 | no difference |
| qwen | r-short | r-none | 200 | -0.020 | [-0.045, +0.000] | -0.020 | 1/5 | 0.219 | 0.84 | worse/inadmissible |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c3000 | agentworld+gemma+qwen | 200 | -0.023 | [-0.045, -0.005] | agentworld -0.015, gemma -0.025, qwen -0.020 | -0.023 | 0/9 | 0.004 | 0.87 | worse/inadmissible |
| f-schema | agentworld+gemma+qwen | 200 | -0.003 | [-0.008, +0.000] | agentworld +0.005, gemma -0.005, qwen +0.000 | -0.003 | 0/1 | 1.000 | 0.91 | no difference |
| f-schema__mode-main | agentworld+gemma+qwen | 200 | +0.000 | [-0.013, +0.013] | agentworld +0.045, gemma -0.010, qwen +0.010 | +0.000 | 3/3 | 1.000 | 0.72 | cheaper, non-inferior |
| mode-main | agentworld+gemma+qwen | 200 | +0.000 | [-0.013, +0.013] | agentworld +0.045, gemma -0.010, qwen +0.010 | +0.000 | 3/3 | 1.000 | 0.78 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).

Address: acc@1 = main_ok (main address equal on street, number, postcode, town, or both without a main address); acc@2 = main exact over all hosts; P@2 = main exact among hosts where reference and prediction both have a main address (cov@2 = their share).
