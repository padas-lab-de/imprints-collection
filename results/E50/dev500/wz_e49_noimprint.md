# E50 screening, wz, dev500 e49_noimprint (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 42 | 0.000 | 0.000 | 0.810 | 0.714 | 0.690 | 0.690 | 0.643 | 0.829 | 0.750 | 0.725 | 0.725 | 0.692 | 0.952 | 1.00 | 3294 | 0 | 25 | 0 | 3539 | 3539 | 4.2 |
| agentworld | r-none | c1500 | 42 | 0.000 | 0.000 | 0.810 | 0.690 | 0.667 | 0.619 | 0.595 | 0.829 | 0.707 | 0.700 | 0.650 | 0.676 | 0.952 | 1.00 | 2928 | 0 | 25 | 0 | 3175 | 3175 | 4.3 |
| agentworld | r-short | base | 42 | 0.000 | 0.000 | 0.833 | 0.738 | 0.714 | 0.690 | 0.667 | 0.854 | 0.756 | 0.732 | 0.707 | 0.737 | 0.976 | 1.00 | 3308 | 0 | 93 | 0 | 4239 | 4239 | 4.5 |
| agentworld | r-short | joint-poi-wz | 42 | 0.000 | 0.000 | 0.762 | 0.714 | 0.643 | 0.595 | 0.571 | 0.780 | 0.732 | 0.659 | 0.610 | 0.600 | 0.976 | 1.00 | 25982 | 22176 | 104 | 0 | 4843 | 27019 | 4.7 |
| agentworld | r-short | joint-poi-wz-address | 42 | 0.000 | 0.024 | 0.810 | 0.714 | 0.667 | 0.595 | 0.524 | 0.829 | 0.732 | 0.683 | 0.610 | 0.579 | 0.976 | 1.00 | 26504 | 22679 | 150 | 0 | 5329 | 28008 | 4.5 |
| gemma | r-none | base | 42 | 0.000 | 0.000 | 0.952 | 0.833 | 0.786 | 0.762 | 0.714 | 0.976 | 0.854 | 0.805 | 0.780 | 0.750 | 0.976 | 1.00 | 3363 | 160 | 29 | 0 | 3492 | 3652 | 4.5 |
| gemma | r-none | c1500 | 42 | 0.000 | 0.000 | 0.929 | 0.786 | 0.738 | 0.690 | 0.619 | 0.951 | 0.805 | 0.756 | 0.725 | 0.667 | 0.976 | 1.00 | 2999 | 155 | 29 | 0 | 3132 | 3287 | 4.5 |
| gemma | r-short | base | 42 | 0.000 | 0.000 | 0.905 | 0.786 | 0.738 | 0.738 | 0.690 | 0.905 | 0.786 | 0.738 | 0.738 | 0.744 | 1.000 | 1.00 | 3378 | 156 | 65 | 0 | 3872 | 4028 | 5.0 |
| gemma | r-short | joint-poi-wz | 42 | 0.000 | 0.000 | 0.952 | 0.810 | 0.786 | 0.762 | 0.714 | 0.976 | 0.829 | 0.805 | 0.780 | 0.750 | 0.976 | 1.00 | 26229 | 22944 | 71 | 0 | 3991 | 26935 | 6.4 |
| gemma | r-short | joint-poi-wz-address | 42 | 0.000 | 0.000 | 0.929 | 0.786 | 0.738 | 0.714 | 0.667 | 0.951 | 0.805 | 0.756 | 0.732 | 0.700 | 0.976 | 1.00 | 26780 | 23424 | 131 | 0 | 4668 | 28092 | 6.7 |
| qwen | r-default | joint-poi-wz | 42 | 0.024 | 0.024 | 0.929 | 0.810 | 0.762 | 0.714 | 0.619 | 0.951 | 0.829 | 0.780 | 0.750 | 0.684 | 0.976 | 1.00 | 26002 | 22736 | 1707 | 1683 | 20334 | 43070 | 29.8 |
| qwen | r-default | joint-poi-wz-address | 42 | 0.071 | 0.071 | 0.833 | 0.714 | 0.690 | 0.643 | 0.571 | 0.921 | 0.789 | 0.763 | 0.730 | 0.706 | 0.905 | 1.00 | 26526 | 22195 | 2113 | 2068 | 25458 | 47653 | 33.0 |
| qwen | r-none | base | 42 | 0.000 | 0.000 | 0.905 | 0.857 | 0.833 | 0.786 | 0.738 | 0.927 | 0.878 | 0.854 | 0.805 | 0.775 | 0.976 | 1.00 | 3294 | 0 | 25 | 0 | 3541 | 3541 | 4.3 |
| qwen | r-none | c1500 | 42 | 0.000 | 0.000 | 0.905 | 0.857 | 0.833 | 0.786 | 0.714 | 0.950 | 0.900 | 0.875 | 0.825 | 0.769 | 0.952 | 1.00 | 2928 | 0 | 25 | 0 | 3174 | 3174 | 4.2 |
| qwen | r-short | base | 42 | 0.000 | 0.000 | 0.905 | 0.833 | 0.786 | 0.738 | 0.714 | 0.927 | 0.854 | 0.825 | 0.775 | 0.769 | 0.952 | 1.00 | 3308 | 0 | 84 | 0 | 4146 | 4146 | 4.5 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 42 | +0.024 | [-0.071, +0.119] | +0.007 | 3/2 | 1.000 | 1.20 | worse/inadmissible |
| gemma | r-short | r-none | 42 | -0.048 | [-0.119, +0.000] | -0.067 | 0/2 | 0.500 | 1.11 | worse/inadmissible |
| qwen | r-short | r-none | 42 | -0.048 | [-0.143, +0.048] | -0.029 | 1/3 | 0.625 | 1.17 | worse/inadmissible |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c1500 | agentworld+gemma+qwen | 42 | -0.024 | [-0.060, +0.000] | agentworld -0.024, gemma -0.048, qwen +0.000 | -0.014 | 1/3 | 0.625 | 0.90 | worse/inadmissible |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
