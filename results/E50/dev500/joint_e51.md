# E50 stage D: joint vs separate calls, dev500 e51

| model | joint run | part | n | separate | joint | d | 95% CI | W/L | C separate (sum) | C joint | C ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | joint-poi-wz (r-short) | poi3 (r-short) | 294 | 0.806 | 0.639 | -0.167 | [-0.221, -0.112] | 14/63 | 28799 | 4423 | 0.15 |
| gemma | joint-poi-wz (r-short) | wz (r-none) | 294 | 0.759 | 0.772 | +0.014 | [-0.017, +0.044] | 12/8 | 28799 | 4423 | 0.15 |
| gemma | joint-poi-wz-address (r-short) | poi3 (r-short) | 294 | 0.806 | 0.588 | -0.218 | [-0.272, -0.163] | 10/74 | 30727 | 5723 | 0.19 |
| gemma | joint-poi-wz-address (r-short) | wz (r-none) | 294 | 0.759 | 0.745 | -0.014 | [-0.044, +0.014] | 7/11 | 30727 | 5723 | 0.19 |
| gemma | joint-poi-wz-address (r-short) | address (r-none) | 300 | 0.980 | 0.967 | -0.013 | [-0.033, +0.007] | 3/7 | 30727 | 5723 | 0.19 |
| qwen | joint-poi-wz (r-default) | poi3 (r-default) | 294 | 0.779 | 0.765 | -0.014 | [-0.054, +0.031] | 17/21 | 35167 | 19381 | 0.55 |
| qwen | joint-poi-wz (r-default) | wz (r-none) | 294 | 0.762 | 0.731 | -0.031 | [-0.065, +0.003] | 9/18 | 35167 | 19381 | 0.55 |
| qwen | joint-poi-wz-address (r-default) | poi3 (r-default) | 294 | 0.779 | 0.704 | -0.075 | [-0.126, -0.024] | 17/39 | 37368 | 28124 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | wz (r-none) | 294 | 0.762 | 0.711 | -0.051 | [-0.092, -0.010] | 11/26 | 37368 | 28124 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | address (r-none) | 300 | 0.973 | 0.827 | -0.147 | [-0.190, -0.107] | 2/46 | 37368 | 28124 | 0.75 |
| agentworld | joint-poi-wz (r-short) | poi3 (r-short) | 294 | 0.718 | 0.565 | -0.153 | [-0.204, -0.099] | 12/57 | 28855 | 5325 | 0.18 |
| agentworld | joint-poi-wz (r-short) | wz (r-none) | 294 | 0.755 | 0.724 | -0.031 | [-0.068, +0.010] | 13/22 | 28855 | 5325 | 0.18 |
| agentworld | joint-poi-wz-address (r-short) | poi3 (r-short) | 294 | 0.718 | 0.548 | -0.170 | [-0.221, -0.116] | 11/61 | 30825 | 5341 | 0.17 |
| agentworld | joint-poi-wz-address (r-short) | wz (r-none) | 294 | 0.755 | 0.728 | -0.027 | [-0.065, +0.010] | 11/19 | 30825 | 5341 | 0.17 |
| agentworld | joint-poi-wz-address (r-short) | address (r-none) | 300 | 0.913 | 0.913 | +0.000 | [-0.033, +0.033] | 13/13 | 30825 | 5341 | 0.17 |

Metric per part: poi3 acc@2, wz acc@3, address main_ok. separate = the model's base run of that part (reasoning in brackets); joint = the part of the joint call at the model's POI base reasoning. C per host = (tok in - cached in) + 10 x tok out over the hosts common to all parts; C separate = sum over the parts.
