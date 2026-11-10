# E50 stage D: joint vs separate calls, dev500 e49

| model | joint run | part | n | separate | joint | d | 95% CI | W/L | C separate (sum) | C joint | C ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | joint-poi-wz (r-short) | poi3 (r-short) | 199 | 0.799 | 0.673 | -0.126 | [-0.181, -0.075] | 4/29 | 28811 | 4688 | 0.16 |
| gemma | joint-poi-wz (r-short) | wz (r-none) | 199 | 0.719 | 0.734 | +0.015 | [-0.020, +0.050] | 8/5 | 28811 | 4688 | 0.16 |
| gemma | joint-poi-wz-address (r-short) | poi3 (r-short) | 199 | 0.799 | 0.628 | -0.171 | [-0.231, -0.116] | 4/38 | 30373 | 5670 | 0.19 |
| gemma | joint-poi-wz-address (r-short) | wz (r-none) | 199 | 0.719 | 0.709 | -0.010 | [-0.040, +0.020] | 4/6 | 30373 | 5670 | 0.19 |
| gemma | joint-poi-wz-address (r-short) | address (r-none) | 200 | 0.980 | 0.845 | -0.135 | [-0.185, -0.090] | 1/28 | 30373 | 5670 | 0.19 |
| qwen | joint-poi-wz (r-default) | poi3 (r-default) | 199 | 0.784 | 0.744 | -0.040 | [-0.085, +0.000] | 5/13 | 34815 | 19671 | 0.56 |
| qwen | joint-poi-wz (r-default) | wz (r-none) | 199 | 0.734 | 0.734 | +0.000 | [-0.045, +0.045] | 11/11 | 34815 | 19671 | 0.56 |
| qwen | joint-poi-wz-address (r-default) | poi3 (r-default) | 199 | 0.784 | 0.724 | -0.060 | [-0.111, -0.010] | 7/19 | 36618 | 27382 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | wz (r-none) | 199 | 0.734 | 0.693 | -0.040 | [-0.090, +0.005] | 8/16 | 36618 | 27382 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | address (r-none) | 200 | 0.965 | 0.775 | -0.190 | [-0.255, -0.130] | 4/42 | 36618 | 27382 | 0.75 |
| agentworld | joint-poi-wz (r-short) | poi3 (r-short) | 199 | 0.719 | 0.608 | -0.111 | [-0.176, -0.050] | 10/32 | 28999 | 5505 | 0.19 |
| agentworld | joint-poi-wz (r-short) | wz (r-none) | 199 | 0.709 | 0.673 | -0.035 | [-0.085, +0.015] | 9/16 | 28999 | 5505 | 0.19 |
| agentworld | joint-poi-wz-address (r-short) | poi3 (r-short) | 199 | 0.719 | 0.558 | -0.161 | [-0.226, -0.101] | 7/39 | 30607 | 5587 | 0.18 |
| agentworld | joint-poi-wz-address (r-short) | wz (r-none) | 199 | 0.709 | 0.683 | -0.025 | [-0.075, +0.025] | 10/15 | 30607 | 5587 | 0.18 |
| agentworld | joint-poi-wz-address (r-short) | address (r-none) | 200 | 0.900 | 0.835 | -0.065 | [-0.120, -0.015] | 9/22 | 30607 | 5587 | 0.18 |

Metric per part: poi3 acc@2, wz acc@3, address main_ok. separate = the model's base run of that part (reasoning in brackets); joint = the part of the joint call at the model's POI base reasoning. C per host = (tok in - cached in) + 10 x tok out over the hosts common to all parts; C separate = sum over the parts.
