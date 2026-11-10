# E50 screening, poi3, dev500 all (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 493 | 0.000 | 0.010 | 0.892 | 0.718 | 0.306 | 0.900 | 0.792 | 0.816 | 0.907 | 1.00 | 24092 | 0 | 82 | 0 | 24909 | 24909 | 1.9 |
| agentworld | r-short | joint-poi-wz | 493 | 0.004 | 0.012 | 0.834 | 0.582 | 0.231 | 0.854 | 0.675 | 0.765 | 0.862 | 1.00 | 26414 | 22086 | 107 | 0 | 5398 | 27484 | 4.6 |
| agentworld | r-short | joint-poi-wz-address | 493 | 0.000 | 0.006 | 0.805 | 0.552 | 0.178 | 0.832 | 0.667 | 0.715 | 0.828 | 1.00 | 26937 | 23138 | 164 | 0 | 5441 | 28578 | 4.5 |
| agentworld | r-short | list_first_q | 493 | 0.000 | 0.002 | 0.870 | 0.682 | 0.272 | 0.888 | 0.755 | 0.784 | 0.903 | 1.00 | 24107 | 22086 | 83 | 0 | 2850 | 24936 | 1.4 |
| agentworld | r-short | retrieve | 493 | 0.000 | 0.000 | 0.911 | 0.767 | 0.343 | 0.920 | 0.825 | 0.867 | 0.929 | 1.00 | 2560 | 0 | 79 | 0 | 3346 | 3346 | 2.6 |
| gemma | r-short | base | 493 | 0.000 | 0.000 | 0.925 | 0.803 | 0.365 | 0.931 | 0.848 | 0.853 | 0.947 | 1.00 | 24300 | 128 | 68 | 0 | 24851 | 24979 | 8.1 |
| gemma | r-short | joint-poi-wz | 493 | 0.000 | 0.000 | 0.799 | 0.653 | 0.276 | 0.943 | 0.809 | 0.786 | 0.807 | 1.00 | 26689 | 22851 | 69 | 0 | 4530 | 27381 | 6.9 |
| gemma | r-short | joint-poi-wz-address | 493 | 0.000 | 0.000 | 0.757 | 0.604 | 0.256 | 0.949 | 0.819 | 0.778 | 0.738 | 1.00 | 27240 | 23235 | 170 | 0 | 5701 | 28936 | 7.4 |
| gemma | r-short | list_first_q | 493 | 0.000 | 0.000 | 0.890 | 0.728 | 0.314 | 0.934 | 0.791 | 0.795 | 0.921 | 1.00 | 24315 | 22727 | 70 | 0 | 2286 | 25012 | 2.0 |
| gemma | r-short | retrieve | 493 | 0.000 | 0.000 | 0.923 | 0.777 | 0.343 | 0.938 | 0.840 | 0.876 | 0.925 | 1.00 | 2616 | 127 | 60 | 0 | 3091 | 3218 | 3.0 |
| qwen | r-default | base | 493 | 0.004 | 0.004 | 0.899 | 0.781 | 0.353 | 0.927 | 0.841 | 0.874 | 0.929 | 1.00 | 24113 | 0 | 694 | 670 | 31051 | 31051 | 11.5 |
| qwen | r-default | joint-poi-wz | 493 | 0.037 | 0.034 | 0.870 | 0.757 | 0.359 | 0.933 | 0.840 | 0.932 | 0.901 | 1.00 | 26435 | 22644 | 1571 | 1547 | 19498 | 42142 | 26.6 |
| qwen | r-default | joint-poi-wz-address | 493 | 0.077 | 0.079 | 0.840 | 0.712 | 0.331 | 0.928 | 0.830 | 0.906 | 0.858 | 1.00 | 26958 | 22644 | 2351 | 2248 | 27825 | 50468 | 38.3 |
| qwen | r-default | list_first_q | 493 | 0.016 | 0.010 | 0.888 | 0.751 | 0.355 | 0.938 | 0.826 | 0.875 | 0.909 | 1.00 | 24128 | 22644 | 697 | 674 | 8451 | 31095 | 14.1 |
| qwen | r-default | retrieve | 493 | 0.000 | 0.000 | 0.892 | 0.753 | 0.343 | 0.928 | 0.832 | 0.899 | 0.905 | 1.00 | 2581 | 0 | 615 | 591 | 8728 | 8728 | 12.0 |
| qwen | r-low | base | 493 | 0.000 | 0.000 | 0.911 | 0.791 | 0.365 | 0.941 | 0.848 | 0.874 | 0.933 | 1.00 | 24101 | 0 | 484 | 461 | 28942 | 28942 | 9.0 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen | r-low | r-default | 493 | +0.010 | [-0.012, +0.030] | +0.007 | 18/13 | 0.473 | 0.93 | no difference |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| joint-poi-wz | agentworld+gemma+qwen | 493 | -0.087 | [-0.116, -0.059] | agentworld -0.136, gemma -0.150, qwen -0.024 | -0.020 | 40/126 | 0.000 | 0.43 | worse/inadmissible |
| joint-poi-wz-address | agentworld+gemma+qwen | 493 | -0.134 | [-0.163, -0.102] | agentworld -0.166, gemma -0.199, qwen -0.069 | -0.020 | 38/170 | 0.000 | 0.60 | worse/inadmissible |
| list_first_q | agentworld+gemma+qwen | 493 | -0.053 | [-0.077, -0.028] | agentworld -0.037, gemma -0.075, qwen -0.030 | -0.036 | 31/83 | 0.000 | 0.19 | worse/inadmissible |
| retrieve | agentworld+gemma+qwen | 493 | -0.027 | [-0.049, -0.008] | agentworld +0.049, gemma -0.026, qwen -0.028 | -0.008 | 29/56 | 0.005 | 0.21 | worse/inadmissible |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
