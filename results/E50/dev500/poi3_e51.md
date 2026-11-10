# E50 screening, poi3, dev500 e51 (L* = 2)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | P@1 | P@2 | P@3 | cov@2 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | base | 294 | 0.000 | 0.007 | 0.891 | 0.718 | 0.310 | 0.900 | 0.784 | 0.835 | 0.915 | 1.00 | 24090 | 0 | 79 | 0 | 24881 | 24881 | 3.2 |
| agentworld | r-short | joint-poi-wz | 294 | 0.007 | 0.017 | 0.827 | 0.565 | 0.231 | 0.856 | 0.656 | 0.810 | 0.861 | 1.00 | 26395 | 22176 | 111 | 0 | 5325 | 27501 | 4.6 |
| agentworld | r-short | joint-poi-wz-address | 294 | 0.000 | 0.003 | 0.806 | 0.548 | 0.201 | 0.835 | 0.668 | 0.797 | 0.820 | 1.00 | 26918 | 23232 | 166 | 0 | 5341 | 28573 | 4.4 |
| agentworld | r-short | list_first_q | 294 | 0.000 | 0.003 | 0.871 | 0.673 | 0.262 | 0.892 | 0.736 | 0.786 | 0.915 | 1.00 | 24105 | 22176 | 85 | 0 | 2776 | 24952 | 1.4 |
| agentworld | r-short | retrieve | 294 | 0.000 | 0.000 | 0.918 | 0.779 | 0.344 | 0.925 | 0.833 | 0.849 | 0.935 | 1.00 | 2555 | 0 | 79 | 0 | 3341 | 3341 | 2.6 |
| gemma | r-short | base | 294 | 0.000 | 0.000 | 0.929 | 0.806 | 0.364 | 0.929 | 0.843 | 0.836 | 0.956 | 1.00 | 24305 | 128 | 68 | 0 | 24860 | 24988 | 13.6 |
| gemma | r-short | joint-poi-wz | 294 | 0.000 | 0.000 | 0.796 | 0.639 | 0.265 | 0.940 | 0.800 | 0.743 | 0.799 | 1.00 | 26675 | 22944 | 69 | 0 | 4423 | 27367 | 6.6 |
| gemma | r-short | joint-poi-wz-address | 294 | 0.000 | 0.000 | 0.762 | 0.588 | 0.252 | 0.949 | 0.797 | 0.763 | 0.738 | 1.00 | 27226 | 23265 | 176 | 0 | 5723 | 28988 | 7.5 |
| gemma | r-short | list_first_q | 294 | 0.000 | 0.000 | 0.898 | 0.711 | 0.316 | 0.936 | 0.766 | 0.788 | 0.929 | 1.00 | 24320 | 22757 | 71 | 0 | 2273 | 25030 | 2.0 |
| gemma | r-short | retrieve | 294 | 0.000 | 0.000 | 0.925 | 0.782 | 0.350 | 0.935 | 0.836 | 0.873 | 0.935 | 1.00 | 2623 | 127 | 61 | 0 | 3105 | 3232 | 3.0 |
| qwen | r-default | base | 294 | 0.000 | 0.000 | 0.912 | 0.779 | 0.350 | 0.927 | 0.833 | 0.858 | 0.935 | 1.00 | 24111 | 0 | 710 | 686 | 31213 | 31213 | 19.2 |
| qwen | r-default | joint-poi-wz | 294 | 0.031 | 0.031 | 0.888 | 0.765 | 0.354 | 0.932 | 0.836 | 0.929 | 0.915 | 1.00 | 26416 | 22736 | 1570 | 1546 | 19381 | 42117 | 25.7 |
| qwen | r-default | joint-poi-wz-address | 294 | 0.082 | 0.082 | 0.840 | 0.704 | 0.323 | 0.925 | 0.821 | 0.905 | 0.857 | 1.00 | 26939 | 22736 | 2392 | 2280 | 28124 | 50860 | 39.9 |
| qwen | r-default | list_first_q | 294 | 0.014 | 0.010 | 0.898 | 0.752 | 0.350 | 0.940 | 0.825 | 0.858 | 0.912 | 1.00 | 24126 | 22736 | 721 | 698 | 8603 | 31339 | 12.8 |
| qwen | r-default | retrieve | 294 | 0.000 | 0.000 | 0.898 | 0.748 | 0.347 | 0.920 | 0.821 | 0.887 | 0.912 | 1.00 | 2576 | 0 | 638 | 615 | 8958 | 8958 | 12.2 |
| qwen | r-low | base | 294 | 0.000 | 0.000 | 0.905 | 0.779 | 0.361 | 0.930 | 0.830 | 0.862 | 0.939 | 1.00 | 24099 | 0 | 490 | 467 | 29002 | 29002 | 15.1 |

## Reasoning level vs base level (per model, paired, acc@2)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen | r-low | r-default | 294 | +0.000 | [-0.031, +0.031] | -0.003 | 10/10 | 1.000 | 0.93 | no difference |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| joint-poi-wz | agentworld+gemma+qwen | 294 | -0.090 | [-0.129, -0.051] | agentworld -0.153, gemma -0.167, qwen -0.014 | -0.020 | 31/84 | 0.000 | 0.42 | worse/inadmissible |
| joint-poi-wz-address | agentworld+gemma+qwen | 294 | -0.146 | [-0.187, -0.104] | agentworld -0.170, gemma -0.218, qwen -0.075 | -0.029 | 27/113 | 0.000 | 0.60 | worse/inadmissible |
| list_first_q | agentworld+gemma+qwen | 294 | -0.061 | [-0.094, -0.027] | agentworld -0.044, gemma -0.095, qwen -0.027 | -0.043 | 22/58 | 0.000 | 0.19 | worse/inadmissible |
| retrieve | agentworld+gemma+qwen | 294 | -0.027 | [-0.056, +0.003] | agentworld +0.061, gemma -0.024, qwen -0.031 | -0.009 | 22/38 | 0.052 | 0.22 | worse/inadmissible |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
