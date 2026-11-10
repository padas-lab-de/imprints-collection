# E50 screening, wz, dev500 all (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 493 | 0.000 | 0.000 | 0.844 | 0.793 | 0.736 | 0.690 | 0.631 | 0.849 | 0.803 | 0.748 | 0.708 | 0.681 | 0.984 | 1.00 | 3726 | 0 | 28 | 0 | 4004 | 4004 | 4.3 |
| agentworld | r-none | c1500 | 493 | 0.000 | 0.000 | 0.836 | 0.781 | 0.714 | 0.659 | 0.611 | 0.841 | 0.787 | 0.726 | 0.677 | 0.667 | 0.984 | 1.00 | 3111 | 0 | 29 | 0 | 3397 | 3397 | 4.3 |
| agentworld | r-short | base | 493 | 0.000 | 0.000 | 0.832 | 0.779 | 0.718 | 0.673 | 0.619 | 0.838 | 0.789 | 0.731 | 0.689 | 0.660 | 0.982 | 1.00 | 3741 | 0 | 95 | 0 | 4695 | 4695 | 4.3 |
| agentworld | r-short | joint-poi-wz | 493 | 0.004 | 0.012 | 0.809 | 0.767 | 0.704 | 0.659 | 0.611 | 0.821 | 0.778 | 0.720 | 0.677 | 0.647 | 0.978 | 1.00 | 26414 | 22086 | 107 | 0 | 5398 | 27484 | 4.6 |
| agentworld | r-short | joint-poi-wz-address | 493 | 0.000 | 0.006 | 0.811 | 0.773 | 0.710 | 0.659 | 0.609 | 0.820 | 0.781 | 0.719 | 0.669 | 0.644 | 0.988 | 1.00 | 26937 | 23138 | 164 | 0 | 5441 | 28578 | 4.5 |
| gemma | r-none | base | 493 | 0.000 | 0.000 | 0.852 | 0.797 | 0.742 | 0.704 | 0.665 | 0.857 | 0.804 | 0.753 | 0.721 | 0.707 | 0.986 | 1.00 | 3823 | 159 | 29 | 0 | 3953 | 4112 | 4.4 |
| gemma | r-none | c1500 | 493 | 0.000 | 0.000 | 0.854 | 0.801 | 0.751 | 0.704 | 0.661 | 0.859 | 0.808 | 0.763 | 0.724 | 0.706 | 0.984 | 1.00 | 3191 | 159 | 29 | 0 | 3321 | 3480 | 4.4 |
| gemma | r-short | base | 493 | 0.000 | 0.000 | 0.846 | 0.795 | 0.744 | 0.704 | 0.655 | 0.846 | 0.795 | 0.747 | 0.717 | 0.698 | 0.996 | 1.00 | 3838 | 159 | 71 | 0 | 4386 | 4545 | 5.2 |
| gemma | r-short | joint-poi-wz | 493 | 0.000 | 0.000 | 0.864 | 0.805 | 0.757 | 0.718 | 0.665 | 0.869 | 0.810 | 0.766 | 0.733 | 0.702 | 0.988 | 1.00 | 26689 | 22851 | 69 | 0 | 4530 | 27381 | 6.9 |
| gemma | r-short | joint-poi-wz-address | 493 | 0.000 | 0.000 | 0.838 | 0.783 | 0.730 | 0.692 | 0.649 | 0.843 | 0.788 | 0.739 | 0.707 | 0.684 | 0.988 | 1.00 | 27240 | 23235 | 170 | 0 | 5701 | 28936 | 7.4 |
| qwen | r-default | joint-poi-wz | 493 | 0.037 | 0.034 | 0.813 | 0.777 | 0.732 | 0.702 | 0.647 | 0.848 | 0.810 | 0.766 | 0.742 | 0.712 | 0.955 | 1.00 | 26435 | 22644 | 1571 | 1547 | 19498 | 42142 | 26.6 |
| qwen | r-default | joint-poi-wz-address | 493 | 0.077 | 0.079 | 0.783 | 0.744 | 0.704 | 0.667 | 0.615 | 0.860 | 0.817 | 0.775 | 0.746 | 0.718 | 0.909 | 1.00 | 26958 | 22644 | 2351 | 2248 | 27825 | 50468 | 38.3 |
| qwen | r-none | base | 493 | 0.000 | 0.000 | 0.834 | 0.795 | 0.751 | 0.704 | 0.665 | 0.849 | 0.810 | 0.766 | 0.723 | 0.699 | 0.980 | 1.00 | 3726 | 0 | 25 | 0 | 3974 | 3974 | 4.6 |
| qwen | r-none | c1500 | 493 | 0.000 | 0.000 | 0.832 | 0.789 | 0.744 | 0.698 | 0.657 | 0.845 | 0.802 | 0.758 | 0.715 | 0.689 | 0.982 | 1.00 | 3111 | 0 | 25 | 0 | 3359 | 3359 | 4.3 |
| qwen | r-short | base | 493 | 0.002 | 0.002 | 0.834 | 0.795 | 0.744 | 0.698 | 0.645 | 0.847 | 0.808 | 0.760 | 0.721 | 0.691 | 0.980 | 1.00 | 3741 | 0 | 91 | 0 | 4651 | 4651 | 4.7 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 493 | -0.018 | [-0.047, +0.010] | -0.017 | 23/32 | 0.281 | 1.17 | worse/inadmissible |
| gemma | r-short | r-none | 493 | +0.002 | [-0.018, +0.022] | -0.006 | 14/13 | 1.000 | 1.11 | no difference |
| qwen | r-short | r-none | 493 | -0.006 | [-0.032, +0.020] | -0.006 | 21/24 | 0.766 | 1.17 | no difference |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c1500 | agentworld+gemma+qwen | 493 | +0.001 | [-0.011, +0.013] | agentworld -0.022, gemma +0.008, qwen -0.006 | +0.001 | 18/17 | 1.000 | 0.84 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
