# E50 stage D: joint vs separate calls, dev500 e49_noimprint

| model | joint run | part | n | separate | joint | d | 95% CI | W/L | C separate (sum) | C joint | C ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | joint-poi-wz (r-short) | poi3 (r-short) | 42 | 0.786 | 0.643 | -0.143 | [-0.262, -0.048] | 0/6 | 27853 | 3991 | 0.14 |
| gemma | joint-poi-wz (r-short) | wz (r-none) | 42 | 0.786 | 0.786 | +0.000 | [-0.071, +0.071] | 1/1 | 27853 | 3991 | 0.14 |
| gemma | joint-poi-wz-address (r-short) | poi3 (r-short) | 42 | 0.786 | 0.619 | -0.167 | [-0.286, -0.071] | 0/7 | 27853 | 4668 | 0.17 |
| gemma | joint-poi-wz-address (r-short) | wz (r-none) | 42 | 0.786 | 0.738 | -0.048 | [-0.119, +0.000] | 0/2 | 27853 | 4668 | 0.17 |
| gemma | joint-poi-wz-address (r-short) | address (r-none) | 42 | 1.000 | 0.452 | -0.548 | [-0.690, -0.405] | 0/23 | 27853 | 4668 | 0.17 |
| qwen | joint-poi-wz (r-default) | poi3 (r-default) | 42 | 0.762 | 0.762 | +0.000 | [-0.095, +0.095] | 2/2 | 33971 | 20334 | 0.60 |
| qwen | joint-poi-wz (r-default) | wz (r-none) | 42 | 0.833 | 0.762 | -0.071 | [-0.167, +0.024] | 1/4 | 33971 | 20334 | 0.60 |
| qwen | joint-poi-wz-address (r-default) | poi3 (r-default) | 42 | 0.762 | 0.714 | -0.048 | [-0.167, +0.071] | 2/4 | 33971 | 25458 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | wz (r-none) | 42 | 0.833 | 0.690 | -0.143 | [-0.262, -0.024] | 1/7 | 33971 | 25458 | 0.75 |
| qwen | joint-poi-wz-address (r-default) | address (r-none) | 42 | 1.000 | 0.952 | -0.048 | [-0.119, +0.000] | 0/2 | 33971 | 25458 | 0.75 |
| agentworld | joint-poi-wz (r-short) | poi3 (r-short) | 42 | 0.714 | 0.571 | -0.143 | [-0.310, +0.024] | 3/9 | 28120 | 4843 | 0.17 |
| agentworld | joint-poi-wz (r-short) | wz (r-none) | 42 | 0.690 | 0.643 | -0.048 | [-0.167, +0.071] | 3/5 | 28120 | 4843 | 0.17 |
| agentworld | joint-poi-wz-address (r-short) | poi3 (r-short) | 42 | 0.714 | 0.571 | -0.143 | [-0.310, +0.000] | 3/9 | 28120 | 5329 | 0.19 |
| agentworld | joint-poi-wz-address (r-short) | wz (r-none) | 42 | 0.690 | 0.667 | -0.024 | [-0.143, +0.095] | 3/4 | 28120 | 5329 | 0.19 |
| agentworld | joint-poi-wz-address (r-short) | address (r-none) | 42 | 1.000 | 0.595 | -0.405 | [-0.548, -0.262] | 0/17 | 28120 | 5329 | 0.19 |

Metric per part: poi3 acc@2, wz acc@3, address main_ok. separate = the model's base run of that part (reasoning in brackets); joint = the part of the joint call at the model's POI base reasoning. C per host = (tok in - cached in) + 10 x tok out over the hosts common to all parts; C separate = sum over the parts.
