# E50 screening, address, dev500 e51 (L* = 1)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | P@1 | P@2 | cov@1 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 300 | 0.000 | 0.003 | 0.913 | 0.877 | 0.913 | 0.956 | 1.000 | 1.00 | 1146 | 0 | 82 | 0 | 1964 | 1964 | 1.1 |
| agentworld | r-none | c3000 | 300 | 0.000 | 0.000 | 0.907 | 0.870 | 0.907 | 0.956 | 1.000 | 1.00 | 1028 | 327 | 80 | 0 | 1497 | 1825 | 0.3 |
| agentworld | r-none | f-schema | 300 | 0.000 | 0.003 | 0.910 | 0.873 | 0.910 | 0.956 | 1.000 | 1.00 | 1146 | 567 | 83 | 0 | 1410 | 1977 | 1.0 |
| agentworld | r-none | f-schema__mode-main | 300 | 0.000 | 0.000 | 0.940 | 0.903 | 0.940 | 0.961 | 1.000 | 1.00 | 926 | 0 | 50 | 0 | 1423 | 1423 | 0.8 |
| agentworld | r-none | mode-main | 300 | 0.000 | 0.000 | 0.937 | 0.897 | 0.937 | 0.954 | 1.000 | 1.00 | 926 | 0 | 50 | 0 | 1422 | 1422 | 0.8 |
| agentworld | r-short | base | 300 | 0.000 | 0.003 | 0.927 | 0.877 | 0.927 | 0.946 | 1.000 | 1.00 | 1161 | 475 | 125 | 0 | 1941 | 2416 | 1.4 |
| agentworld | r-short | joint-poi-wz-address | 300 | 0.000 | 0.003 | 0.913 | 0.877 | 0.913 | 0.936 | 1.000 | 1.00 | 26913 | 23232 | 165 | 0 | 5331 | 28563 | 4.4 |
| gemma | r-low | base | 300 | 0.000 | 0.000 | 0.983 | 0.930 | 0.983 | 0.993 | 1.000 | 1.00 | 1203 | 448 | 934 | 816 | 10097 | 10545 | 13.6 |
| gemma | r-none | base | 300 | 0.000 | 0.003 | 0.980 | 0.927 | 0.980 | 0.989 | 1.000 | 1.00 | 1205 | 445 | 116 | 0 | 1923 | 2368 | 1.8 |
| gemma | r-none | c3000 | 300 | 0.000 | 0.000 | 0.973 | 0.920 | 0.973 | 0.986 | 1.000 | 1.00 | 1080 | 460 | 112 | 0 | 1744 | 2204 | 1.5 |
| gemma | r-none | f-schema | 300 | 0.000 | 0.003 | 0.973 | 0.920 | 0.973 | 0.982 | 1.000 | 1.00 | 1205 | 448 | 77 | 0 | 1528 | 1976 | 1.3 |
| gemma | r-none | f-schema__mode-main | 300 | 0.000 | 0.000 | 0.970 | 0.920 | 0.970 | 0.979 | 1.000 | 1.00 | 977 | 224 | 52 | 0 | 1268 | 1492 | 1.4 |
| gemma | r-none | mode-main | 300 | 0.000 | 0.000 | 0.970 | 0.920 | 0.970 | 0.979 | 1.000 | 1.00 | 977 | 224 | 75 | 0 | 1503 | 1727 | 1.3 |
| gemma | r-short | base | 300 | 0.000 | 0.000 | 0.980 | 0.927 | 0.980 | 0.986 | 1.000 | 1.00 | 1220 | 448 | 147 | 0 | 2245 | 2693 | 2.3 |
| gemma | r-short | joint-poi-wz-address | 300 | 0.000 | 0.000 | 0.967 | 0.920 | 0.967 | 0.979 | 1.000 | 1.00 | 27222 | 23268 | 176 | 0 | 5711 | 28980 | 7.5 |
| qwen | r-default | joint-poi-wz-address | 300 | 0.083 | 0.083 | 0.827 | 0.773 | 0.827 | 0.947 | 1.000 | 1.00 | 26934 | 22736 | 2409 | 2297 | 28288 | 51024 | 40.2 |
| qwen | r-low | base | 300 | 0.000 | 0.000 | 0.980 | 0.927 | 0.980 | 0.986 | 1.000 | 1.00 | 1170 | 0 | 450 | 370 | 5669 | 5669 | 7.5 |
| qwen | r-none | base | 300 | 0.000 | 0.003 | 0.973 | 0.920 | 0.973 | 0.982 | 1.000 | 1.00 | 1146 | 0 | 105 | 0 | 2195 | 2195 | 2.5 |
| qwen | r-none | c3000 | 300 | 0.000 | 0.000 | 0.970 | 0.917 | 0.970 | 0.982 | 1.000 | 1.00 | 1028 | 133 | 101 | 0 | 1910 | 2043 | 0.7 |
| qwen | r-none | f-schema | 300 | 0.000 | 0.003 | 0.973 | 0.920 | 0.973 | 0.982 | 1.000 | 1.00 | 1146 | 3 | 105 | 0 | 2192 | 2195 | 2.1 |
| qwen | r-none | f-schema__mode-main | 300 | 0.000 | 0.000 | 0.977 | 0.923 | 0.977 | 0.982 | 1.000 | 1.00 | 926 | 0 | 67 | 0 | 1601 | 1601 | 1.3 |
| qwen | r-none | mode-main | 300 | 0.000 | 0.000 | 0.977 | 0.923 | 0.977 | 0.982 | 1.000 | 1.00 | 926 | 0 | 67 | 0 | 1601 | 1601 | 1.4 |
| qwen | r-short | base | 300 | 0.000 | 0.000 | 0.963 | 0.910 | 0.963 | 0.978 | 1.000 | 1.00 | 1161 | 661 | 149 | 0 | 1993 | 2654 | 2.5 |

## Reasoning level vs base level (per model, paired, acc@1)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 300 | +0.013 | [-0.013, +0.040] | +0.013 | 11/7 | 0.481 | 0.99 | no difference |
| gemma | r-low | r-none | 300 | +0.003 | [-0.007, +0.013] | +0.003 | 2/1 | 1.000 | 5.25 | no difference |
| gemma | r-short | r-none | 300 | +0.000 | [-0.013, +0.013] | +0.000 | 2/2 | 1.000 | 1.17 | no difference |
| qwen | r-low | r-none | 300 | +0.007 | [-0.010, +0.023] | +0.007 | 4/2 | 0.688 | 2.58 | no difference |
| qwen | r-short | r-none | 300 | -0.010 | [-0.027, +0.007] | -0.010 | 2/5 | 0.453 | 0.91 | worse/inadmissible |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c3000 | agentworld+gemma+qwen | 300 | -0.005 | [-0.017, +0.007] | agentworld -0.007, gemma -0.007, qwen -0.003 | -0.005 | 2/5 | 0.453 | 0.89 | cheaper, non-inferior |
| f-schema | agentworld+gemma+qwen | 300 | -0.003 | [-0.008, +0.000] | agentworld -0.003, gemma -0.007, qwen +0.000 | -0.003 | 0/2 | 0.500 | 0.90 | no difference |
| f-schema__mode-main | agentworld+gemma+qwen | 300 | -0.003 | [-0.013, +0.007] | agentworld +0.027, gemma -0.010, qwen +0.003 | -0.003 | 3/5 | 0.727 | 0.70 | cheaper, non-inferior |
| mode-main | agentworld+gemma+qwen | 300 | -0.003 | [-0.013, +0.007] | agentworld +0.023, gemma -0.010, qwen +0.003 | -0.003 | 3/5 | 0.727 | 0.75 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).

Address: acc@1 = main_ok (main address equal on street, number, postcode, town, or both without a main address); acc@2 = main exact over all hosts; P@2 = main exact among hosts where reference and prediction both have a main address (cov@2 = their share).
