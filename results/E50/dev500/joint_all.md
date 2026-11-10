# E50 stage D: joint vs separate calls, dev500 all

| model | joint run | part | n | separate | joint | d | 95% CI | W/L | C separate (sum) | C joint | C ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | joint-poi-wz (r-short) | poi3 (r-short) | 493 | 0.803 | 0.653 | -0.150 | [-0.189, -0.110] | 18/92 | 28804 | 4530 | 0.16 |
| gemma | joint-poi-wz (r-short) | wz (r-none) | 493 | 0.742 | 0.757 | +0.014 | [-0.008, +0.037] | 20/13 | 28804 | 4530 | 0.16 |
| gemma | joint-poi-wz-address (r-short) | poi3 (r-short) | 493 | 0.803 | 0.604 | -0.199 | [-0.239, -0.156] | 14/112 | 30584 | 5701 | 0.19 |
| gemma | joint-poi-wz-address (r-short) | wz (r-none) | 493 | 0.742 | 0.730 | -0.012 | [-0.034, +0.008] | 11/17 | 30584 | 5701 | 0.19 |
| gemma | joint-poi-wz-address (r-short) | address (r-none) | 500 | 0.980 | 0.918 | -0.062 | [-0.086, -0.038] | 4/35 | 30584 | 5701 | 0.19 |
| qwen | joint-poi-wz (r-default) | poi3 (r-default) | 493 | 0.781 | 0.757 | -0.024 | [-0.055, +0.006] | 22/34 | 35025 | 19498 | 0.56 |
| qwen | joint-poi-wz (r-default) | wz (r-none) | 493 | 0.751 | 0.732 | -0.018 | [-0.047, +0.008] | 20/29 | 35025 | 19498 | 0.56 |
| qwen | joint-poi-wz-address (r-default) | poi3 (r-default) | 493 | 0.781 | 0.712 | -0.069 | [-0.105, -0.032] | 24/58 | 37065 | 27825 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | wz (r-none) | 493 | 0.751 | 0.704 | -0.047 | [-0.077, -0.016] | 19/42 | 37065 | 27825 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | address (r-none) | 500 | 0.970 | 0.806 | -0.164 | [-0.200, -0.130] | 6/88 | 37065 | 27825 | 0.75 |
| agentworld | joint-poi-wz (r-short) | poi3 (r-short) | 493 | 0.718 | 0.582 | -0.136 | [-0.176, -0.097] | 22/89 | 28913 | 5398 | 0.19 |
| agentworld | joint-poi-wz (r-short) | wz (r-none) | 493 | 0.736 | 0.704 | -0.032 | [-0.063, -0.002] | 22/38 | 28913 | 5398 | 0.19 |
| agentworld | joint-poi-wz-address (r-short) | poi3 (r-short) | 493 | 0.718 | 0.552 | -0.166 | [-0.209, -0.126] | 18/100 | 30737 | 5441 | 0.18 |
| agentworld | joint-poi-wz-address (r-short) | wz (r-none) | 493 | 0.736 | 0.710 | -0.026 | [-0.057, +0.004] | 21/34 | 30737 | 5441 | 0.18 |
| agentworld | joint-poi-wz-address (r-short) | address (r-none) | 500 | 0.908 | 0.882 | -0.026 | [-0.056, +0.002] | 22/35 | 30737 | 5441 | 0.18 |

Metric per part: poi3 acc@2, wz acc@3, address main_ok. separate = the model's base run of that part (reasoning in brackets); joint = the part of the joint call at the model's POI base reasoning. C per host = (tok in - cached in) + 10 x tok out over the hosts common to all parts; C separate = sum over the parts.
