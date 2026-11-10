# E49 poi3c: gemma b vs qwen b vs level-majority ens2 (POI v3, --node-lang both)

Date 2026-11-10. Innkube only, no paid cost. Schema `poi3`, input both, `--node-lang both` (variant b of poi3b). Configs: **qwen b** = qwen38-27b flat think; **gemma b** = gemma4-31b-it flat reason; **ens2** = `ensemble.py --vote level_majority` of qwen b + gemma b (strict majority of both voters, so the ensemble descends only while both agree; adaptive depth). Dev: 200 hosts, refs `results/E49/refs/poi_v3.jsonl`; gemma b dev was run now (200 hosts, 0 errors, 0 cache hits), qwen b dev and held-out qwen b and gemma b come from `results/E49/poi3b/preds` (reused). Held-out: 100 hosts, refs `results/E49/heldout/refs/poi_v3.jsonl` (Sonnet labels, noisier than dev; 3 null refs). Scored hosts = common to all configs with a non-null ref (dev 199, held-out 97; offline = online_only false, 172 / 85). Semantics as poi3b: acc = acc_trunc (abstention and stopping above L count wrong), P@L = precision among covered, cov@L = coverage among hosts whose ref reaches L. Paired: host bootstrap 5000 resamples, seed 1; sign test on acc@2. Code: `scripts/E49/poi3c_summary.py`. Preds: `results/E49/poi3c/preds/{dev,heldout}/poi3/` (dev gemma b, both ens2 files); tables also in `summary_tables.md`.

Latency and tokens: s/host is model latency of one call, no cache hits in any of the five pred sets (all are comparable in that respect), but server load varied between runs (qwen b dev/held-out and gemma b held-out ran earlier), so differences of a few s are not reliable. ens2 s/host and tokens = sum of both members (sequential cost; the two calls can run in parallel). tok = prompt / completion tokens per host.

## Findings
- **gemma b is as good as qwen b.** All-host acc@2 .799 vs .784 (dev) and .814 vs .794 (held-out); paired d acc@2 +.015 [-.025,+.055] and +.021 [-.031,+.072], sign tests p=.63 and .69; P@2 equal within .013. acc@1 is better for gemma (+.040 [+.005,+.080] dev, +.031 [.000,+.072] held-out) because it abstains less (3 vs 10 dev, 0 vs 4 held-out). Offline: identical acc@2 on dev (.855 vs .855) and +.012 on held-out. No evidence gemma is worse; no evidence it is better at L2.
- **gemma b is cheaper, but only modestly faster.** Completion tokens 67 vs 540-670 (8-10x fewer), prompt tokens the same (24k). s/host 16.2 vs 19.9 (dev), 14.6 vs 18.9 (held-out): about 20% faster, because the 24k-token prompt dominates latency. gemma b had no failed replies (qwen b: 2 on dev).
- **ens2 raises P@2 as hoped, at a coverage and accuracy cost.** P@2 .914 (dev) and .914 (held-out) vs .852 / .854 (qwen b) and .855 / .867 (gemma b). Gain over qwen b +.062 [+.029,+.098] dev, +.060 [+.017,+.115] held-out; over gemma b +.059 [+.027,+.096] dev, +.047 [+.007,+.094] held-out (offline smaller: +.041 to +.046 dev, +.029 to +.041 held-out, held-out vs gemma CI touches 0). Cost: cov@2 .872 dev and .900 held-out (vs .98 to 1.0), acc@2 drops -.035 (vs qwen b) and -.050 (vs gemma b) on dev, CIs below 0 (0 wins, 7 and 10 losses); held-out -.021 and -.041.
- **Depth distribution of ens2** (all hosts): dev none 21, L1 12, L2 91, L3 75 (of 199); held-out none 6, L1 10, L2 33, L3 48 (of 97). "none" = the models disagree on the root, so about 10% of dev and 6% of held-out hosts get no label; 21 and 6 respectively equals the abstain column. ens2 reaches L3 on 38% (dev) and 49% (held-out) of hosts, with P@3 .943 / .911 on the covered ones (single models: .88 to .90, but they cover L3 on 81 to 92% of the L3-capable hosts; ens2 only 72 to 87%).
- P@2 >= 0.8 holds for all three setups on both sets; the question is only whether the extra .06 P@2 is worth losing 10 points of coverage and 2 to 5 points of acc@2. P@3 (single models .88 to .90) is already above .8 with bilingual names.
- ens2 costs 2x tokens (48k in) and the sum of both latencies if run sequentially.

## Tables
Source: `scripts/E49/poi3c_summary.py` (copied from run output).

### dev, all hosts (n=199)

| config | abst | err | P@1 | P@2 | P@3 | acc@1 | acc@2 | acc@3 | cov@1 | cov@2 | cov@3 | s/host | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen b | 10 | 2 | 0.926 | 0.852 | 0.899 | 0.879 | 0.784 | 0.698 | 0.950 | 0.979 | 0.814 | 19.91 | 24116 | 670 |
| gemma b | 3 | 0 | 0.934 | 0.855 | 0.880 | 0.920 | 0.799 | 0.714 | 0.985 | 0.995 | 0.856 | 16.18 | 24292 | 67 |
| ens2 | 21 | 0 | 0.961 | 0.914 | 0.943 | 0.859 | 0.759 | 0.673 | 0.894 | 0.872 | 0.722 | 36.08 | 48408 | 737 |

Paired (dev, all hosts): x - y, 95% bootstrap CI over hosts

| x vs y | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|
| gemma b vs qwen b | +0.040 [+0.005,+0.080] | +0.015 [-0.025,+0.055] | +0.002 [-0.042,+0.047] | 10/7, p=0.63 |
| ens2 vs qwen b | -0.020 [-0.040,-0.005] | -0.035 [-0.060,-0.010] | +0.062 [+0.029,+0.098] | 0/7, p=0.02 |
| ens2 vs gemma b | -0.060 [-0.095,-0.030] | -0.050 [-0.080,-0.020] | +0.059 [+0.027,+0.096] | 0/10, p=0.00 |

ens2 depth (canonical path length) over 199 hosts: none=21, L1=12, L2=91, L3=75

### dev, offline (n=172)

| config | abst | err | P@1 | P@2 | P@3 | acc@1 | acc@2 | acc@3 | cov@1 | cov@2 | cov@3 | s/host | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen b | 2 | 2 | 0.953 | 0.875 | 0.907 | 0.942 | 0.855 | 0.767 | 0.988 | 0.994 | 0.833 | 17.21 | 24093 | 574 |
| gemma b | 0 | 0 | 0.959 | 0.870 | 0.883 | 0.959 | 0.855 | 0.767 | 1.000 | 1.000 | 0.856 | 15.93 | 24271 | 67 |
| ens2 | 7 | 0 | 0.970 | 0.916 | 0.940 | 0.930 | 0.831 | 0.744 | 0.959 | 0.917 | 0.744 | 33.14 | 48364 | 641 |

Paired (dev, offline): x - y, 95% bootstrap CI over hosts

| x vs y | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|
| gemma b vs qwen b | +0.017 [-0.012,+0.047] | +0.000 [-0.035,+0.035] | -0.005 [-0.042,+0.032] | 5/5, p=1.00 |
| ens2 vs qwen b | -0.012 [-0.029,+0.000] | -0.029 [-0.058,-0.006] | +0.041 [+0.014,+0.074] | 0/5, p=0.06 |
| ens2 vs gemma b | -0.029 [-0.058,-0.006] | -0.029 [-0.058,-0.006] | +0.046 [+0.018,+0.080] | 0/5, p=0.06 |

### held-out, all hosts (n=97)

| config | abst | err | P@1 | P@2 | P@3 | acc@1 | acc@2 | acc@3 | cov@1 | cov@2 | cov@3 | s/host | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen b | 4 | 0 | 0.957 | 0.854 | 0.875 | 0.918 | 0.794 | 0.701 | 0.959 | 0.989 | 0.923 | 18.94 | 24064 | 538 |
| gemma b | 0 | 0 | 0.948 | 0.867 | 0.894 | 0.948 | 0.814 | 0.742 | 1.000 | 1.000 | 0.904 | 14.58 | 24238 | 68 |
| ens2 | 6 | 0 | 0.978 | 0.914 | 0.911 | 0.918 | 0.784 | 0.701 | 0.938 | 0.900 | 0.865 | 33.52 | 48302 | 606 |

Paired (held-out, all hosts): x - y, 95% bootstrap CI over hosts

| x vs y | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|
| gemma b vs qwen b | +0.031 [+0.000,+0.072] | +0.021 [-0.031,+0.072] | +0.013 [-0.034,+0.066] | 4/2, p=0.69 |
| ens2 vs qwen b | +0.000 [+0.000,+0.000] | -0.021 [-0.052,+0.000] | +0.060 [+0.017,+0.115] | 0/2, p=0.50 |
| ens2 vs gemma b | -0.031 [-0.072,+0.000] | -0.041 [-0.082,-0.010] | +0.047 [+0.007,+0.094] | 0/4, p=0.12 |

ens2 depth (canonical path length) over 97 hosts: none=6, L1=10, L2=33, L3=48

### held-out, offline (n=85)

| config | abst | err | P@1 | P@2 | P@3 | acc@1 | acc@2 | acc@3 | cov@1 | cov@2 | cov@3 | s/host | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen b | 0 | 0 | 0.988 | 0.869 | 0.889 | 0.988 | 0.871 | 0.765 | 1.000 | 1.000 | 0.918 | 17.36 | 24091 | 479 |
| gemma b | 0 | 0 | 0.988 | 0.881 | 0.889 | 0.988 | 0.871 | 0.788 | 1.000 | 1.000 | 0.918 | 14.51 | 24265 | 67 |
| ens2 | 0 | 0 | 0.988 | 0.910 | 0.907 | 0.988 | 0.847 | 0.753 | 1.000 | 0.929 | 0.878 | 31.86 | 48356 | 546 |

Paired (held-out, offline): x - y, 95% bootstrap CI over hosts

| x vs y | d acc@1 | d acc@2 | d P@2 | acc@2 W/L, sign p |
|---|---|---|---|---|
| gemma b vs qwen b | +0.000 [+0.000,+0.000] | +0.012 [-0.035,+0.059] | +0.012 [-0.037,+0.060] | 3/2, p=1.00 |
| ens2 vs qwen b | +0.000 [+0.000,+0.000] | -0.024 [-0.059,+0.000] | +0.041 [+0.005,+0.086] | 0/2, p=0.50 |
| ens2 vs gemma b | +0.000 [+0.000,+0.000] | -0.035 [-0.082,+0.000] | +0.029 [-0.003,+0.071] | 0/3, p=0.25 |

## Recommendation
- **Default POI setup for the final runs: gemma4-31b-it flat reason, input both, `--node-lang both`, single model.** It matches qwen b on every L2 metric (CIs include 0, point estimates slightly higher), abstains less, never failed a reply, emits 8-10x fewer completion tokens and is about 20% faster per host; one model, one call, no ensemble logic.
- **Optional high-precision layer: ens2 (qwen b + gemma b, level majority).** Use it only if the paper needs a "confident" subset: it gives P@2 about .91 and P@3 about .91 to .94 with 10 to 13% of hosts unlabelled at L2 and 3 to 6% at L1. Report it as a coverage/precision trade-off, not as a better labeller (acc@2 is lower by 2 to 5 points). Cost 2x tokens and 2 calls per host. For a single full-corpus run, ens2 is not worth it unless qwen is already being run for another reason.
- Keep qwen b as the fallback if gemma is unavailable (statistically indistinguishable).

## Doubts
- Differences are 2 to 10 hosts; all gemma-vs-qwen CIs at L2 include 0, so "as good as" means not distinguishably different at n=199/97 (non-inferiority margin not tested, CI half-width about .04 to .05).
- Held-out refs are single-family (Sonnet) labels and noisier; qwen and gemma are not Sonnet-independent of each other, so ens2 agreement may partly reflect shared biases.
- ens2 gain in P@2 is partly selection (dropping hard hosts), which the coverage columns make visible; it is not a gain in accuracy.
- Latency: server load differed between runs; the 20% speedup is indicative only. Dev gemma b ran now, the rest earlier.
- ens2 with 2 voters needs unanimity (strict majority of 2); a third voter (e.g. gemma retrieve) was not tried here for POI v3 (stage 3 found ens3 weaker on v2).
- The summary script rebuilds ens2 files on each run; results are deterministic given the preds.
