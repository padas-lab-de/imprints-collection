# E49 poi3b: bilingual node names on POI v3 (dev and held-out)

Date 2026-11-10. Innkube only, no paid cost. Schema `poi3` (English names). Variants: **a** current prompt; **b** `--node-lang both` (candidate list and few-shot show "English (Deutsch)" on every path element); **c** b plus `--mfr-line` (system-prompt line: a manufacturer that also sells its products is Manufacturer or Factory, not "... Supplier"). Models: qwen38-27b flat think input both (a, b, c), gemma4-31b-it flat reason both (a, b; held-out only). Dev = 200 hosts, refs `results/E49/refs/poi_v3.jsonl` (dev a reused from `results/E49/poi3/preds`). Held-out = 100 hosts disjoint from dev, refs `results/E49/heldout/refs/poi_v3.jsonl` (two Sonnet passes, adjudicated with R1-R7; A=B exact main 74/100, same path prefix L1/L2/L3 = 87/76/40; 3 main = null, so 97 scored; 13 online_only). Hosts scored are those common to all configs of a set with a non-null ref (dev 199; held-out 97). Scorer `score.py` semantics (acc = acc_trunc, P = precision among covered). tok = prompt / completion tokens per host. Tables and paired CIs come from `scripts/E49/poi3b_summary.py` (paired: host bootstrap, 5000 resamples, seed 1; sign test on acc@2). Preds: `results/E49/poi3b/preds/{dev,heldout}/poi3/`.

Held-out label caveat: the held-out refs are Sonnet-labelled and noisier than the dev refs (A=B 74% vs 89.5% on dev POI v2), so absolute numbers are not strictly comparable between the sets; paired differences within a set are.

## Findings
- Bilingual names (b) raise qwen P@2 from .824 to .852 on dev (all hosts) and from .830 to .854 on held-out; acc@2 +.030 / +.031. The direction replicates, but only the dev offline gain has a CI above 0 (acc@2 +.041 [+.012,+.076], sign p=.04). On held-out the all-host CI includes 0 (+.031 [-.010,+.082]); offline acc@2 +.047 [+.012,+.094] (4 wins, 0 losses; the gain is small in hosts).
- gemma4-31b-it b vs a on held-out: P@2 .833 -> .867, acc@2 +.031 [.000,+.072] (3 wins, 0 losses). Same direction, CI touches 0.
- Manufacturer line (c) adds nothing over b: dev acc@2 -.005, held-out -.010 (CIs include 0), and c has more failed replies on dev (5 vs 2). Not recommended.
- P@2 >= 0.8 on held-out: yes for every config, including the current prompt a (qwen .830, gemma .833) and all offline subsets (.841 to .881). The dev drop from .896 (migrated v2) to .824 is therefore not a held-out-only artefact, but the .8 bar is not at risk; the margin is thin for a (.830, n=97). Bilingual gives .854 (qwen) and .867 (gemma).
- Cost: bilingual about doubles the prompt (12.5k -> 24k tokens per host), completions +10% (qwen). Latency not compared (server load varied).

## Tables
### dev, all hosts (n=199)

| config | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen a current | 199 | 10 | 1 | 0.921 | 0.824 | 0.874 | 0.754 | 0.973 | 12546 | 603 |
| qwen b bilingual | 199 | 10 | 2 | 0.926 | 0.852 | 0.879 | 0.784 | 0.979 | 24116 | 670 |
| qwen c bilingual+mfr | 199 | 10 | 5 | 0.931 | 0.852 | 0.884 | 0.779 | 0.973 | 24153 | 796 |

Paired (dev, all hosts): difference x - y, 95% bootstrap CI over hosts

| x vs y | n | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|---|
| qwen b bilingual vs qwen a current | 199 | +0.005 [-0.025,+0.035] | +0.030 [+0.000,+0.060] | +0.028 [-0.004,+0.063] | 8/2, p=0.11 |
| qwen c bilingual+mfr vs qwen a current | 199 | +0.010 [-0.025,+0.045] | +0.025 [-0.020,+0.070] | +0.027 [-0.021,+0.076] | 13/8, p=0.38 |
| qwen c bilingual+mfr vs qwen b bilingual | 199 | +0.005 [-0.025,+0.040] | -0.005 [-0.040,+0.030] | -0.001 [-0.037,+0.037] | 5/6, p=1.00 |

### dev, offline (online_only false) (n=172)

| config | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen a current | 172 | 1 | 0 | 0.947 | 0.833 | 0.942 | 0.814 | 0.994 | 12523 | 475 |
| qwen b bilingual | 172 | 2 | 2 | 0.953 | 0.875 | 0.942 | 0.855 | 0.994 | 24093 | 574 |
| qwen c bilingual+mfr | 172 | 1 | 1 | 0.959 | 0.869 | 0.953 | 0.849 | 0.994 | 24130 | 625 |

Paired (dev, offline (online_only false)): difference x - y, 95% bootstrap CI over hosts

| x vs y | n | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|---|
| qwen b bilingual vs qwen a current | 172 | +0.000 [-0.023,+0.023] | +0.041 [+0.012,+0.076] | +0.042 [+0.011,+0.077] | 8/1, p=0.04 |
| qwen c bilingual+mfr vs qwen a current | 172 | +0.012 [-0.023,+0.047] | +0.035 [-0.012,+0.081] | +0.036 [-0.010,+0.083] | 12/6, p=0.24 |
| qwen c bilingual+mfr vs qwen b bilingual | 172 | +0.012 [-0.017,+0.047] | -0.006 [-0.041,+0.029] | -0.006 [-0.041,+0.029] | 4/5, p=1.00 |

### held-out, all hosts (n=97)

| config | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen a current | 97 | 3 | 0 | 0.926 | 0.830 | 0.897 | 0.763 | 0.978 | 12494 | 500 |
| qwen b bilingual | 97 | 4 | 0 | 0.957 | 0.854 | 0.918 | 0.794 | 0.989 | 24064 | 538 |
| qwen c bilingual+mfr | 97 | 2 | 1 | 0.937 | 0.833 | 0.918 | 0.784 | 1.000 | 24101 | 614 |
| gemma a current | 97 | 1 | 0 | 0.927 | 0.833 | 0.918 | 0.784 | 1.000 | 12708 | 66 |
| gemma b bilingual | 97 | 0 | 0 | 0.948 | 0.867 | 0.948 | 0.814 | 1.000 | 24238 | 68 |

Paired (held-out, all hosts): difference x - y, 95% bootstrap CI over hosts

| x vs y | n | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|---|
| qwen b bilingual vs qwen a current | 97 | +0.021 [-0.031,+0.072] | +0.031 [-0.010,+0.082] | +0.024 [-0.015,+0.071] | 4/1, p=0.38 |
| qwen c bilingual+mfr vs qwen a current | 97 | +0.021 [-0.031,+0.072] | +0.021 [-0.021,+0.062] | +0.004 [-0.047,+0.057] | 3/1, p=0.62 |
| qwen c bilingual+mfr vs qwen b bilingual | 97 | +0.000 [-0.031,+0.031] | -0.010 [-0.052,+0.021] | -0.021 [-0.056,+0.003] | 1/2, p=1.00 |
| gemma b bilingual vs gemma a current | 97 | +0.031 [+0.000,+0.072] | +0.031 [+0.000,+0.072] | +0.033 [+0.000,+0.078] | 3/0, p=0.25 |

### held-out, offline (online_only false) (n=85)

| config | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen a current | 85 | 2 | 0 | 0.964 | 0.841 | 0.941 | 0.812 | 0.976 | 12521 | 415 |
| qwen b bilingual | 85 | 0 | 0 | 0.988 | 0.869 | 0.988 | 0.871 | 1.000 | 24091 | 479 |
| qwen c bilingual+mfr | 85 | 0 | 0 | 0.976 | 0.845 | 0.976 | 0.847 | 1.000 | 24128 | 512 |
| gemma a current | 85 | 0 | 0 | 0.953 | 0.845 | 0.953 | 0.835 | 1.000 | 12735 | 66 |
| gemma b bilingual | 85 | 0 | 0 | 0.988 | 0.881 | 0.988 | 0.871 | 1.000 | 24265 | 67 |

Paired (held-out, offline (online_only false)): difference x - y, 95% bootstrap CI over hosts

| x vs y | n | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|---|
| qwen b bilingual vs qwen a current | 85 | +0.047 [+0.012,+0.094] | +0.047 [+0.012,+0.094] | +0.028 [-0.015,+0.076] | 4/0, p=0.12 |
| qwen c bilingual+mfr vs qwen a current | 85 | +0.035 [-0.012,+0.094] | +0.024 [-0.024,+0.071] | +0.004 [-0.051,+0.060] | 3/1, p=0.62 |
| qwen c bilingual+mfr vs qwen b bilingual | 85 | -0.012 [-0.035,+0.000] | -0.024 [-0.059,+0.000] | -0.024 [-0.060,+0.000] | 0/2, p=0.50 |
| gemma b bilingual vs gemma a current | 85 | +0.035 [+0.000,+0.082] | +0.035 [+0.000,+0.082] | +0.036 [+0.000,+0.083] | 3/0, p=0.25 |

## Recommendation
Use `--node-lang both` as the POI v3 default for the final runs: it is the only variant with a consistent gain (+2.4 to +4.2 points P@2 on dev, held-out and both models), it replicates on held-out in direction and approximately in size, and P@2 stays above .8 everywhere. Do not adopt the manufacturer line. State in the paper that the gain is small and that held-out CIs include 0 for all hosts (n=97); the prompt cost is 2x input tokens. The default of `run.py` stays unchanged (opt-in flag), so existing tags and caches are intact.

## Doubts
- Held-out refs are single-family (Sonnet) labels with 26 adjudicated disagreements; 3 hosts are null (2 block/for-sale pages, 1 personal blog). Differences of 3 to 4 hosts decide the paired results.
- Not tested: bilingual only on leaf names, or German-only names; only the all-elements variant was run.
- Dev a was run earlier (same cfg, not rerun), b and c later; temperature 0 but server-side nondeterminism is possible (qwen has 1 to 5 failed replies per run).
- The schema line of the system prompt still says "English category names" in b and c (kept so tags and caches stay unchanged when the flag is off).
