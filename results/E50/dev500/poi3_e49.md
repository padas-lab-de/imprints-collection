# E50 screening, poi3, dev500 e49 (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 199 | 0.000 | 0.015 | 0.894 | 0.719 | 0.302 | 0.899 | 0.803 | 0.789 | 0.894 | 1.00 | 24095 | 0 | 86 | 0 | 24951 | 24951 | 0.1 |
| agentworld | r-short | joint-poi-wz | 199 | 0.000 | 0.005 | 0.844 | 0.608 | 0.231 | 0.853 | 0.703 | 0.708 | 0.864 | 1.00 | 26444 | 21953 | 101 | 0 | 5505 | 27458 | 4.5 |
| agentworld | r-short | joint-poi-wz-address | 199 | 0.000 | 0.010 | 0.804 | 0.558 | 0.146 | 0.829 | 0.665 | 0.592 | 0.839 | 1.00 | 26967 | 22999 | 162 | 0 | 5587 | 28586 | 4.6 |
| agentworld | r-short | list_first_q | 199 | 0.000 | 0.000 | 0.869 | 0.693 | 0.286 | 0.883 | 0.784 | 0.781 | 0.884 | 1.00 | 24110 | 21953 | 80 | 0 | 2959 | 24913 | 1.4 |
| agentworld | r-short | retrieve | 199 | 0.000 | 0.000 | 0.899 | 0.749 | 0.342 | 0.913 | 0.814 | 0.895 | 0.920 | 1.00 | 2567 | 0 | 79 | 0 | 3353 | 3353 | 2.5 |
| gemma | r-short | base | 199 | 0.000 | 0.000 | 0.920 | 0.799 | 0.367 | 0.934 | 0.855 | 0.880 | 0.935 | 1.00 | 24292 | 128 | 67 | 0 | 24838 | 24966 | 0.1 |
| gemma | r-short | joint-poi-wz | 199 | 0.000 | 0.000 | 0.804 | 0.673 | 0.291 | 0.947 | 0.822 | 0.853 | 0.819 | 1.00 | 26709 | 22714 | 69 | 0 | 4688 | 27402 | 7.2 |
| gemma | r-short | joint-poi-wz-address | 199 | 0.000 | 0.000 | 0.749 | 0.628 | 0.261 | 0.949 | 0.850 | 0.800 | 0.739 | 1.00 | 27260 | 23189 | 160 | 0 | 5670 | 28859 | 7.4 |
| gemma | r-short | list_first_q | 199 | 0.000 | 0.000 | 0.879 | 0.754 | 0.312 | 0.931 | 0.829 | 0.805 | 0.910 | 1.00 | 24307 | 22682 | 68 | 0 | 2305 | 24986 | 2.1 |
| gemma | r-short | retrieve | 199 | 0.000 | 0.000 | 0.920 | 0.769 | 0.332 | 0.943 | 0.845 | 0.880 | 0.910 | 1.00 | 2604 | 127 | 59 | 0 | 3071 | 3199 | 2.9 |
| qwen | r-default | base | 199 | 0.010 | 0.010 | 0.879 | 0.784 | 0.357 | 0.926 | 0.852 | 0.899 | 0.920 | 1.00 | 24116 | 0 | 670 | 646 | 30813 | 30813 | 0.1 |
| qwen | r-default | joint-poi-wz | 199 | 0.045 | 0.040 | 0.844 | 0.744 | 0.367 | 0.933 | 0.846 | 0.936 | 0.879 | 1.00 | 26465 | 22507 | 1571 | 1548 | 19671 | 42178 | 28.0 |
| qwen | r-default | joint-poi-wz-address | 199 | 0.070 | 0.075 | 0.839 | 0.724 | 0.342 | 0.933 | 0.842 | 0.907 | 0.859 | 1.00 | 26988 | 22507 | 2290 | 2202 | 27382 | 49889 | 35.8 |
| qwen | r-default | list_first_q | 199 | 0.020 | 0.010 | 0.874 | 0.749 | 0.362 | 0.935 | 0.828 | 0.900 | 0.905 | 1.00 | 24131 | 22507 | 660 | 638 | 8226 | 30734 | 16.0 |
| qwen | r-default | retrieve | 199 | 0.000 | 0.000 | 0.884 | 0.759 | 0.337 | 0.941 | 0.848 | 0.918 | 0.894 | 1.00 | 2588 | 0 | 580 | 557 | 8388 | 8388 | 11.6 |
| qwen | r-low | base | 199 | 0.000 | 0.000 | 0.920 | 0.809 | 0.372 | 0.958 | 0.875 | 0.892 | 0.925 | 1.00 | 24104 | 0 | 475 | 452 | 28854 | 28854 | 0.1 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen | r-low | r-default | 199 | +0.025 | [-0.005, +0.060] | +0.023 | 8/3 | 0.227 | 0.94 | no difference |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| joint-poi-wz | agentworld+gemma+qwen | 199 | -0.083 | [-0.121, -0.050] | agentworld -0.111, gemma -0.126, qwen -0.040 | -0.020 | 9/42 | 0.000 | 0.44 | worse/inadmissible |
| joint-poi-wz-address | agentworld+gemma+qwen | 199 | -0.116 | [-0.158, -0.075] | agentworld -0.161, gemma -0.171, qwen -0.060 | -0.007 | 11/57 | 0.000 | 0.59 | worse/inadmissible |
| list_first_q | agentworld+gemma+qwen | 199 | -0.040 | [-0.073, -0.008] | agentworld -0.025, gemma -0.045, qwen -0.035 | -0.025 | 9/25 | 0.009 | 0.19 | worse/inadmissible |
| retrieve | agentworld+gemma+qwen | 199 | -0.028 | [-0.055, -0.003] | agentworld +0.030, gemma -0.030, qwen -0.025 | -0.007 | 7/18 | 0.043 | 0.21 | worse/inadmissible |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
