# E50 screening, wz, dev500 e49 (L* = 3)

## Runs

| model | reasoning | variant | n | fail | cut | acc@1 | acc@2 | acc@3 | acc@4 | acc@5 | P@1 | P@2 | P@3 | P@4 | P@5 | cov@3 | calls | tok in | cached in | tok out | reas tok | C | C0 | s/host |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-none | base | 199 | 0.000 | 0.000 | 0.794 | 0.739 | 0.709 | 0.668 | 0.603 | 0.802 | 0.754 | 0.723 | 0.689 | 0.659 | 0.980 | 1.00 | 3756 | 0 | 29 | 0 | 4048 | 4048 | 4.2 |
| agentworld | r-none | c1500 | 199 | 0.000 | 0.000 | 0.784 | 0.734 | 0.683 | 0.633 | 0.578 | 0.792 | 0.741 | 0.694 | 0.649 | 0.639 | 0.985 | 1.00 | 3151 | 0 | 30 | 0 | 3446 | 3446 | 4.3 |
| agentworld | r-short | base | 199 | 0.000 | 0.000 | 0.824 | 0.769 | 0.739 | 0.693 | 0.628 | 0.841 | 0.785 | 0.754 | 0.708 | 0.676 | 0.980 | 1.00 | 3771 | 0 | 96 | 0 | 4726 | 4726 | 4.4 |
| agentworld | r-short | joint-poi-wz | 199 | 0.000 | 0.005 | 0.764 | 0.719 | 0.673 | 0.628 | 0.578 | 0.776 | 0.730 | 0.691 | 0.648 | 0.622 | 0.975 | 1.00 | 26444 | 21953 | 101 | 0 | 5505 | 27458 | 4.5 |
| agentworld | r-short | joint-poi-wz-address | 199 | 0.000 | 0.010 | 0.774 | 0.724 | 0.683 | 0.633 | 0.573 | 0.782 | 0.731 | 0.690 | 0.640 | 0.613 | 0.990 | 1.00 | 26967 | 22999 | 162 | 0 | 5587 | 28586 | 4.6 |
| gemma | r-none | base | 199 | 0.000 | 0.000 | 0.849 | 0.764 | 0.719 | 0.673 | 0.623 | 0.858 | 0.772 | 0.726 | 0.687 | 0.667 | 0.990 | 1.00 | 3843 | 158 | 29 | 0 | 3974 | 4132 | 4.3 |
| gemma | r-none | c1500 | 199 | 0.000 | 0.000 | 0.844 | 0.759 | 0.734 | 0.678 | 0.623 | 0.853 | 0.766 | 0.741 | 0.699 | 0.674 | 0.990 | 1.00 | 3227 | 159 | 29 | 0 | 3357 | 3516 | 4.4 |
| gemma | r-short | base | 199 | 0.000 | 0.000 | 0.859 | 0.789 | 0.749 | 0.709 | 0.643 | 0.859 | 0.789 | 0.749 | 0.716 | 0.688 | 1.000 | 1.00 | 3858 | 158 | 69 | 0 | 4393 | 4551 | 5.0 |
| gemma | r-short | joint-poi-wz | 199 | 0.000 | 0.000 | 0.854 | 0.769 | 0.734 | 0.693 | 0.638 | 0.863 | 0.777 | 0.741 | 0.704 | 0.676 | 0.990 | 1.00 | 26709 | 22714 | 69 | 0 | 4688 | 27402 | 7.2 |
| gemma | r-short | joint-poi-wz-address | 199 | 0.000 | 0.000 | 0.834 | 0.749 | 0.709 | 0.668 | 0.613 | 0.843 | 0.756 | 0.716 | 0.679 | 0.649 | 0.990 | 1.00 | 27260 | 23189 | 160 | 0 | 5670 | 28859 | 7.4 |
| qwen | r-default | joint-poi-wz | 199 | 0.045 | 0.040 | 0.804 | 0.754 | 0.734 | 0.704 | 0.623 | 0.847 | 0.794 | 0.772 | 0.749 | 0.701 | 0.950 | 1.00 | 26465 | 22507 | 1571 | 1548 | 19671 | 42178 | 28.0 |
| qwen | r-default | joint-poi-wz-address | 199 | 0.070 | 0.075 | 0.769 | 0.719 | 0.693 | 0.653 | 0.573 | 0.845 | 0.790 | 0.762 | 0.726 | 0.679 | 0.910 | 1.00 | 26988 | 22507 | 2290 | 2202 | 27382 | 49889 | 35.8 |
| qwen | r-none | base | 199 | 0.000 | 0.000 | 0.789 | 0.749 | 0.734 | 0.683 | 0.633 | 0.805 | 0.764 | 0.749 | 0.701 | 0.674 | 0.980 | 1.00 | 3756 | 0 | 25 | 0 | 4003 | 4003 | 4.3 |
| qwen | r-none | c1500 | 199 | 0.000 | 0.000 | 0.784 | 0.749 | 0.734 | 0.678 | 0.623 | 0.800 | 0.764 | 0.749 | 0.696 | 0.663 | 0.980 | 1.00 | 3151 | 0 | 25 | 0 | 3397 | 3397 | 4.3 |
| qwen | r-short | base | 199 | 0.000 | 0.000 | 0.814 | 0.774 | 0.729 | 0.673 | 0.613 | 0.839 | 0.798 | 0.755 | 0.698 | 0.674 | 0.965 | 1.00 | 3771 | 0 | 90 | 0 | 4666 | 4666 | 4.2 |

## Reasoning level vs base level (per model, paired, acc@3)

| model | level | vs | n | d | 95% CI | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| agentworld | r-short | r-none | 199 | +0.030 | [-0.015, +0.080] | +0.031 | 14/8 | 0.286 | 1.17 | no difference |
| gemma | r-short | r-none | 199 | +0.030 | [-0.005, +0.070] | +0.023 | 10/4 | 0.180 | 1.11 | no difference |
| qwen | r-short | r-none | 199 | -0.005 | [-0.050, +0.040] | +0.006 | 10/11 | 1.000 | 1.17 | worse/inadmissible |

## Prompt variants vs base prompt (base reasoning per model; pooled over gemma, qwen)

| variant | models | n | d pooled | 95% CI | d per model | dP | W/L | sign p | C ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| c1500 | agentworld+gemma+qwen | 199 | +0.008 | [-0.008, +0.025] | agentworld -0.025, gemma +0.015, qwen +0.000 | +0.008 | 8/5 | 0.581 | 0.85 | cheaper, non-inferior |

acc@L: share of hosts (non-null reference) whose prediction matches the reference down to level L (abstention, failure and stopping above L = miss). P@L: precision among hosts where prediction and reference reach L. fail: error or unparsable reply; cut: replies stopped at max_tokens. C = (tok in - cached in) + 10 x tok out per host; C0 without cache credit. s/host includes cached responses at their first latency. Verdict: design.md section 7 (admissible: fail <= 1%, d >= -0.01, CI low >= -0.04, every model d >= -0.03, dP >= -0.03; better: CI low > 0 or sign p < 0.05; cheaper: C ratio <= 0.9).
