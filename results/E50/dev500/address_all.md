# E50 screening, address, dev500 all (L* = 1)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | P@1 | P@2 | cov@1 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 500 | 0.000 | 0.002 | 0.908 | 0.770 | 0.908 | 0.941 | 1.000 | 0.92 | 1092 | 0 | 73 | 0 | 1822 | 1822 | 1.1 |
| agentworld | r-none | c3000 | 500 | 0.000 | 0.000 | 0.898 | 0.760 | 0.898 | 0.943 | 1.000 | 0.92 | 970 | 332 | 71 | 0 | 1350 | 1681 | 0.3 |
| agentworld | r-none | f-schema | 500 | 0.000 | 0.002 | 0.908 | 0.768 | 0.908 | 0.941 | 1.000 | 0.92 | 1092 | 558 | 74 | 0 | 1272 | 1829 | 0.9 |
| agentworld | r-none | f-schema__mode-main | 500 | 0.000 | 0.000 | 0.942 | 0.802 | 0.942 | 0.952 | 1.000 | 0.92 | 891 | 0 | 45 | 0 | 1339 | 1339 | 0.7 |
| agentworld | r-none | mode-main | 500 | 0.000 | 0.000 | 0.940 | 0.798 | 0.940 | 0.948 | 1.000 | 0.92 | 891 | 0 | 45 | 0 | 1338 | 1338 | 0.7 |
| agentworld | r-short | base | 500 | 0.000 | 0.002 | 0.924 | 0.774 | 0.924 | 0.939 | 1.000 | 0.92 | 1106 | 484 | 112 | 0 | 1747 | 2230 | 1.2 |
| agentworld | r-short | joint-poi-wz-address | 500 | 0.000 | 0.006 | 0.882 | 0.778 | 0.882 | 0.926 | 1.000 | 1.00 | 26936 | 23139 | 164 | 0 | 5433 | 28572 | 4.5 |
| gemma | r-low | base | 500 | 0.000 | 0.000 | 0.980 | 0.826 | 0.980 | 0.983 | 1.000 | 0.92 | 1141 | 409 | 854 | 748 | 9275 | 9684 | 12.4 |
| gemma | r-none | base | 500 | 0.000 | 0.002 | 0.980 | 0.826 | 0.980 | 0.983 | 1.000 | 0.92 | 1143 | 408 | 104 | 0 | 1779 | 2187 | 1.7 |
| gemma | r-none | c3000 | 500 | 0.000 | 0.000 | 0.966 | 0.812 | 0.966 | 0.978 | 1.000 | 0.92 | 1015 | 417 | 101 | 0 | 1605 | 2021 | 1.2 |
| gemma | r-none | f-schema | 500 | 0.000 | 0.002 | 0.974 | 0.820 | 0.974 | 0.976 | 1.000 | 0.92 | 1143 | 409 | 69 | 0 | 1425 | 1835 | 1.2 |
| gemma | r-none | f-schema__mode-main | 500 | 0.000 | 0.000 | 0.970 | 0.818 | 0.970 | 0.971 | 1.000 | 0.92 | 934 | 205 | 47 | 0 | 1195 | 1400 | 1.3 |
| gemma | r-none | mode-main | 500 | 0.000 | 0.000 | 0.970 | 0.818 | 0.970 | 0.971 | 1.000 | 0.92 | 934 | 204 | 68 | 0 | 1408 | 1612 | 1.2 |
| gemma | r-short | base | 500 | 0.000 | 0.000 | 0.980 | 0.826 | 0.980 | 0.981 | 1.000 | 0.92 | 1157 | 428 | 133 | 0 | 2058 | 2487 | 2.1 |
| gemma | r-short | joint-poi-wz-address | 500 | 0.000 | 0.000 | 0.918 | 0.818 | 0.918 | 0.971 | 1.000 | 1.00 | 27239 | 23237 | 169 | 0 | 5694 | 28931 | 7.4 |
| qwen | r-default | joint-poi-wz-address | 500 | 0.078 | 0.080 | 0.806 | 0.656 | 0.806 | 0.932 | 1.000 | 1.00 | 26957 | 22645 | 2359 | 2256 | 27899 | 50544 | 38.4 |
| qwen | r-low | base | 500 | 0.000 | 0.000 | 0.980 | 0.826 | 0.980 | 0.983 | 1.000 | 0.92 | 1114 | 0 | 427 | 356 | 5386 | 5386 | 7.1 |
| qwen | r-none | base | 500 | 0.000 | 0.002 | 0.970 | 0.816 | 0.970 | 0.971 | 1.000 | 0.92 | 1092 | 0 | 95 | 0 | 2039 | 2039 | 2.2 |
| qwen | r-none | c3000 | 500 | 0.000 | 0.000 | 0.960 | 0.806 | 0.960 | 0.971 | 1.000 | 0.92 | 970 | 122 | 91 | 0 | 1759 | 1881 | 0.7 |
| qwen | r-none | f-schema | 500 | 0.000 | 0.002 | 0.970 | 0.816 | 0.970 | 0.971 | 1.000 | 0.92 | 1092 | 2 | 94 | 0 | 2036 | 2037 | 1.9 |
| qwen | r-none | f-schema__mode-main | 500 | 0.000 | 0.000 | 0.976 | 0.822 | 0.976 | 0.976 | 1.000 | 0.92 | 891 | 0 | 61 | 0 | 1499 | 1499 | 1.3 |
| qwen | r-none | mode-main | 500 | 0.000 | 0.000 | 0.976 | 0.822 | 0.976 | 0.976 | 1.000 | 0.92 | 891 | 0 | 61 | 0 | 1499 | 1499 | 1.3 |
| qwen | r-short | base | 500 | 0.000 | 0.000 | 0.956 | 0.802 | 0.956 | 0.969 | 1.000 | 0.92 | 1106 | 652 | 134 | 0 | 1799 | 2451 | 2.3 |

## Reasoning level vs base level (per model, paired, acc@1)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 500 | +0.016 | [-0.006, +0.038] | +0.016 | 19/11 | 0.200 | 0.96 | no difference |
| gemma | r-low | r-none | 500 | +0.000 | [-0.012, +0.010] | +0.000 | 4/4 | 1.000 | 5.21 | no difference |
| gemma | r-short | r-none | 500 | +0.000 | [-0.008, +0.008] | +0.000 | 2/2 | 1.000 | 1.16 | no difference |
| qwen | r-low | r-none | 500 | +0.010 | [-0.004, +0.024] | +0.010 | 9/4 | 0.267 | 2.64 | no difference |
| qwen | r-short | r-none | 500 | -0.014 | [-0.028, +0.000] | -0.014 | 3/10 | 0.092 | 0.88 | worse/inadmissible |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c3000 | agentworld+gemma+qwen | 500 | -0.012 | [-0.023, -0.002] | agentworld -0.010, gemma -0.014, qwen -0.010 | -0.012 | 2/14 | 0.004 | 0.88 | worse/inadmissible |
| f-schema | agentworld+gemma+qwen | 500 | -0.003 | [-0.007, +0.000] | agentworld +0.000, gemma -0.006, qwen +0.000 | -0.003 | 0/3 | 0.250 | 0.91 | no difference |
| f-schema__mode-main | agentworld+gemma+qwen | 500 | -0.002 | [-0.010, +0.006] | agentworld +0.034, gemma -0.010, qwen +0.006 | -0.002 | 6/8 | 0.791 | 0.71 | cheaper, non-inferior |
| mode-main | agentworld+gemma+qwen | 500 | -0.002 | [-0.010, +0.006] | agentworld +0.032, gemma -0.010, qwen +0.006 | -0.002 | 6/8 | 0.791 | 0.76 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).

Address: acc@1 = main_ok (main address equal on street, number, postcode, town, or both without a main address); acc@2 = main exact over all hosts; P@2 = main exact among hosts where reference and prediction both have a main address (cov@2 = their share).
