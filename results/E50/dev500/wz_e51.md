# E50 screening, wz, dev500 e51 (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 294 | 0.000 | 0.000 | 0.878 | 0.830 | 0.755 | 0.704 | 0.650 | 0.881 | 0.836 | 0.766 | 0.721 | 0.695 | 0.986 | 1.00 | 3707 | 0 | 27 | 0 | 3974 | 3974 | 4.4 |
| agentworld | r-none | c1500 | 294 | 0.000 | 0.000 | 0.871 | 0.813 | 0.735 | 0.677 | 0.633 | 0.874 | 0.818 | 0.747 | 0.696 | 0.686 | 0.983 | 1.00 | 3085 | 0 | 28 | 0 | 3363 | 3363 | 4.3 |
| agentworld | r-short | base | 294 | 0.000 | 0.000 | 0.837 | 0.786 | 0.704 | 0.660 | 0.612 | 0.837 | 0.791 | 0.716 | 0.676 | 0.650 | 0.983 | 1.00 | 3722 | 0 | 95 | 0 | 4674 | 4674 | 4.3 |
| agentworld | r-short | joint-poi-wz | 294 | 0.007 | 0.017 | 0.840 | 0.799 | 0.724 | 0.680 | 0.633 | 0.852 | 0.810 | 0.740 | 0.697 | 0.664 | 0.980 | 1.00 | 26395 | 22176 | 111 | 0 | 5325 | 27501 | 4.6 |
| agentworld | r-short | joint-poi-wz-address | 294 | 0.000 | 0.003 | 0.837 | 0.806 | 0.728 | 0.677 | 0.633 | 0.845 | 0.814 | 0.738 | 0.689 | 0.664 | 0.986 | 1.00 | 26918 | 23232 | 166 | 0 | 5341 | 28573 | 4.4 |
| gemma | r-none | base | 294 | 0.000 | 0.000 | 0.854 | 0.820 | 0.759 | 0.724 | 0.694 | 0.857 | 0.825 | 0.772 | 0.745 | 0.734 | 0.983 | 1.00 | 3809 | 159 | 29 | 0 | 3939 | 4098 | 4.6 |
| gemma | r-none | c1500 | 294 | 0.000 | 0.000 | 0.861 | 0.830 | 0.762 | 0.721 | 0.687 | 0.863 | 0.836 | 0.778 | 0.741 | 0.727 | 0.980 | 1.00 | 3167 | 159 | 29 | 0 | 3296 | 3455 | 4.4 |
| gemma | r-short | base | 294 | 0.000 | 0.000 | 0.837 | 0.799 | 0.741 | 0.701 | 0.663 | 0.837 | 0.799 | 0.747 | 0.718 | 0.704 | 0.993 | 1.00 | 3824 | 160 | 72 | 0 | 4381 | 4541 | 5.3 |
| gemma | r-short | joint-poi-wz | 294 | 0.000 | 0.000 | 0.871 | 0.830 | 0.772 | 0.735 | 0.684 | 0.874 | 0.833 | 0.783 | 0.753 | 0.720 | 0.986 | 1.00 | 26675 | 22944 | 69 | 0 | 4423 | 27367 | 6.6 |
| gemma | r-short | joint-poi-wz-address | 294 | 0.000 | 0.000 | 0.840 | 0.806 | 0.745 | 0.707 | 0.673 | 0.843 | 0.809 | 0.755 | 0.727 | 0.707 | 0.986 | 1.00 | 27226 | 23265 | 176 | 0 | 5723 | 28988 | 7.5 |
| qwen | r-default | joint-poi-wz | 294 | 0.031 | 0.031 | 0.820 | 0.793 | 0.731 | 0.701 | 0.663 | 0.849 | 0.820 | 0.762 | 0.738 | 0.720 | 0.959 | 1.00 | 26416 | 22736 | 1570 | 1546 | 19381 | 42117 | 25.7 |
| qwen | r-default | joint-poi-wz-address | 294 | 0.082 | 0.082 | 0.793 | 0.762 | 0.711 | 0.677 | 0.643 | 0.869 | 0.836 | 0.783 | 0.760 | 0.744 | 0.908 | 1.00 | 26939 | 22736 | 2392 | 2280 | 28124 | 50860 | 39.9 |
| qwen | r-none | base | 294 | 0.000 | 0.000 | 0.864 | 0.827 | 0.762 | 0.718 | 0.687 | 0.879 | 0.841 | 0.778 | 0.738 | 0.716 | 0.980 | 1.00 | 3707 | 0 | 25 | 0 | 3954 | 3954 | 4.7 |
| qwen | r-none | c1500 | 294 | 0.000 | 0.000 | 0.864 | 0.816 | 0.752 | 0.711 | 0.680 | 0.876 | 0.828 | 0.765 | 0.728 | 0.707 | 0.983 | 1.00 | 3085 | 0 | 25 | 0 | 3333 | 3333 | 4.3 |
| qwen | r-short | base | 294 | 0.003 | 0.003 | 0.847 | 0.810 | 0.755 | 0.714 | 0.667 | 0.853 | 0.815 | 0.763 | 0.737 | 0.703 | 0.990 | 1.00 | 3722 | 0 | 92 | 0 | 4640 | 4640 | 5.1 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 294 | -0.051 | [-0.092, -0.014] | -0.049 | 9/24 | 0.014 | 1.18 | worse/inadmissible |
| gemma | r-short | r-none | 294 | -0.017 | [-0.041, +0.007] | -0.025 | 4/9 | 0.267 | 1.11 | worse/inadmissible |
| qwen | r-short | r-none | 294 | -0.007 | [-0.037, +0.024] | -0.015 | 11/13 | 0.839 | 1.17 | no difference |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c1500 | agentworld+gemma+qwen | 294 | -0.003 | [-0.020, +0.014] | agentworld -0.020, gemma +0.003, qwen -0.010 | -0.003 | 10/12 | 0.832 | 0.84 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
