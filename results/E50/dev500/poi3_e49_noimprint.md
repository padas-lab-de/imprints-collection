# E50 screening, poi3, dev500 e49_noimprint (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 42 | 0.000 | 0.024 | 0.929 | 0.714 | 0.310 | 0.929 | 0.750 | 0.684 | 0.952 | 1.00 | 23643 | 0 | 94 | 0 | 24580 | 24580 | 0.1 |
| agentworld | r-short | joint-poi-wz | 42 | 0.000 | 0.000 | 0.810 | 0.571 | 0.214 | 0.810 | 0.615 | 0.500 | 0.929 | 1.00 | 25982 | 22176 | 104 | 0 | 4843 | 27019 | 4.7 |
| agentworld | r-short | joint-poi-wz-address | 42 | 0.000 | 0.024 | 0.786 | 0.571 | 0.143 | 0.805 | 0.686 | 0.462 | 0.833 | 1.00 | 26504 | 22679 | 150 | 0 | 5329 | 28008 | 4.5 |
| agentworld | r-short | list_first_q | 42 | 0.000 | 0.000 | 0.857 | 0.667 | 0.357 | 0.857 | 0.700 | 0.714 | 0.952 | 1.00 | 23658 | 21648 | 81 | 0 | 2822 | 24470 | 1.4 |
| agentworld | r-short | retrieve | 42 | 0.000 | 0.000 | 0.929 | 0.738 | 0.333 | 0.929 | 0.775 | 0.824 | 0.952 | 1.00 | 2119 | 0 | 78 | 0 | 2900 | 2900 | 2.7 |
| gemma | r-short | base | 42 | 0.000 | 0.000 | 0.929 | 0.786 | 0.381 | 0.929 | 0.786 | 0.800 | 1.000 | 1.00 | 23828 | 128 | 66 | 0 | 24361 | 24489 | 0.1 |
| gemma | r-short | joint-poi-wz | 42 | 0.000 | 0.000 | 0.786 | 0.643 | 0.333 | 0.971 | 0.818 | 0.737 | 0.786 | 1.00 | 26229 | 22944 | 71 | 0 | 3991 | 26935 | 6.4 |
| gemma | r-short | joint-poi-wz-address | 42 | 0.000 | 0.000 | 0.738 | 0.619 | 0.286 | 0.969 | 0.897 | 0.706 | 0.690 | 1.00 | 26780 | 23424 | 131 | 0 | 4668 | 28092 | 6.7 |
| gemma | r-short | list_first_q | 42 | 0.000 | 0.000 | 0.881 | 0.762 | 0.333 | 0.925 | 0.800 | 0.700 | 0.952 | 1.00 | 23843 | 22912 | 67 | 0 | 1604 | 24516 | 2.1 |
| gemma | r-short | retrieve | 42 | 0.000 | 0.000 | 0.905 | 0.690 | 0.333 | 0.905 | 0.707 | 0.824 | 0.976 | 1.00 | 2142 | 128 | 59 | 0 | 2601 | 2729 | 2.9 |
| qwen | r-default | base | 42 | 0.024 | 0.024 | 0.857 | 0.762 | 0.429 | 0.947 | 0.842 | 0.900 | 0.905 | 1.00 | 23664 | 0 | 677 | 654 | 30430 | 30430 | 0.1 |
| qwen | r-default | joint-poi-wz | 42 | 0.024 | 0.024 | 0.952 | 0.762 | 0.405 | 1.000 | 0.800 | 0.810 | 0.952 | 1.00 | 26002 | 22736 | 1707 | 1683 | 20334 | 43070 | 29.8 |
| qwen | r-default | joint-poi-wz-address | 42 | 0.071 | 0.071 | 0.833 | 0.714 | 0.381 | 0.921 | 0.789 | 0.842 | 0.905 | 1.00 | 26526 | 22195 | 2113 | 2068 | 25458 | 47653 | 33.0 |
| qwen | r-default | list_first_q | 42 | 0.024 | 0.000 | 0.905 | 0.762 | 0.405 | 0.974 | 0.821 | 0.850 | 0.929 | 1.00 | 23679 | 22195 | 539 | 517 | 6873 | 29067 | 13.0 |
| qwen | r-default | retrieve | 42 | 0.000 | 0.000 | 0.881 | 0.714 | 0.333 | 0.949 | 0.789 | 0.875 | 0.905 | 1.00 | 2140 | 0 | 581 | 558 | 7951 | 7951 | 12.0 |
| qwen | r-low | base | 42 | 0.000 | 0.000 | 0.952 | 0.810 | 0.405 | 0.976 | 0.829 | 0.810 | 0.976 | 1.00 | 23652 | 0 | 437 | 414 | 28020 | 28020 | 0.1 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen | r-low | r-default | 42 | +0.048 | [+0.000, +0.119] | -0.013 | 2/0 | 0.500 | 0.92 | no difference |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| joint-poi-wz | agentworld+gemma+qwen | 42 | -0.071 | [-0.143, -0.012] | agentworld -0.143, gemma -0.143, qwen +0.000 | -0.005 | 2/8 | 0.109 | 0.44 | worse/inadmissible |
| joint-poi-wz-address | agentworld+gemma+qwen | 42 | -0.107 | [-0.190, -0.036] | agentworld -0.143, gemma -0.167, qwen -0.048 | +0.029 | 2/11 | 0.022 | 0.55 | worse/inadmissible |
| list_first_q | agentworld+gemma+qwen | 42 | -0.012 | [-0.071, +0.060] | agentworld -0.048, gemma -0.024, qwen +0.000 | -0.004 | 2/3 | 1.000 | 0.15 | worse/inadmissible |
| retrieve | agentworld+gemma+qwen | 42 | -0.071 | [-0.167, +0.012] | agentworld +0.024, gemma -0.095, qwen -0.048 | -0.066 | 3/9 | 0.146 | 0.19 | worse/inadmissible |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
