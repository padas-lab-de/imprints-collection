# E49 held-out check of the WZ rules gain

Question: is the dev gain of wz_rules.md (stage 3) and --rules-candidates (stage 3b) real? Innkube only, no paid APIs.

## Setup
- Sample: 100 hosts, disjoint from the 200 dev hosts, drawn with scripts/E49/build_dev.py (new option --exclude results/E49/dev_hosts.txt), seed 4950, n 100, same eligibility and topic stratification as dev (eligible after exclusion: 542 hosts). Host list: results/E49/heldout/hosts.txt.
- Reference labels (results/E49/heldout/refs/wz.jsonl): two independent Sonnet-subagent passes A and B (2 x 50 hosts each), given only the labelling spec, the WZ 2025 schema and the host texts; they were not allowed to read wz_rules.md, the dev refs, predictions or scores. I adjudicated the 23 disagreements with R1-R7 (note "adjudicated: A|B|new; reason" on each line; 1 new label: sheirlock.com 82.91.2). No rule change was needed on the 77 agreed lines. Validation (scripts/E49/refs_validate_heldout.py, a WZ-only copy of refs_validate.py for the held-out paths): 0 errors. 1 host has main = null (www.kunststoff-service.de, domain for sale), so 99 hosts are scored.
- A=B agreement: main exact 77/100; same path prefix at L1..L5 = 89/89/85/81/76 of 100. (Dev reference passes: 179/200 = 89.5%; so these refs are noisier or the held-out hosts are harder.) The A and B passes were Sonnet, the dev passes were Opus: a difference in labeller strength.
- Runs: retrieve k30, emb-text kw, node-text path, home input, gemma4-31b-it and qwen38-27b. (a) no rules; (b) --rules results/E49/wz_rules.md --keep-outside; (c) = (b) + --rules-candidates. ens2 = level-majority of gemma + qwen per config. Scorer: score.py --common; full table results/E49/heldout/scores/wz.md; paired analysis results/E49/heldout/scores/paired.md (scripts/E49/heldout_compare.py).

## Scores on the 100 held-out hosts (99 scored)
acc@L counts abstentions as wrong (over hosts whose reference reaches L); P@L = precision among answers reaching L; cov = coverage.

| config | abst | P@1..5 | acc@1..5 | cov@1..5 | tok in/host |
|---|---|---|---|---|---|
| gemma (a) no rules | 1 | .857/.827/.806/.796/.779 | .848/.818/.798/.788/.758 | .990/.990/.990/.990/.979 | 3372 |
| gemma (b) rules+keepout | 0 | .838/.798/.768/.765/.726 | .838/.798/.768/.758/.707 | 1.000/1.000/1.000/.990/.979 | 4772 |
| gemma (c) b+rules-cands | 0 | .828/.788/.758/.747/.722 | .828/.788/.758/.747/.717 | 1.000/1.000/1.000/1.000/1.000 | 8756 |
| qwen (a) no rules | 2 | .845/.794/.753/.742/.716 | .828/.778/.737/.727/.697 | .980/.980/.980/.980/.979 | 3302 |
| qwen (b) rules+keepout | 1 | .827/.786/.745/.735/.708 | .818/.778/.737/.727/.687 | .990/.990/.990/.990/.990 | 4699 |
| qwen (c) b+rules-cands | 0 | .848/.808/.768/.765/.740 | .848/.808/.768/.758/.717 | 1.000/1.000/1.000/.990/.990 | 8500 |
| ens2 (a) no rules | 6 | .871/.854/.828/.824/.810 | .818/.768/.727/.707/.657 | .939/.899/.879/.859/.814 | 6674 |
| ens2 (b) rules+keepout | 10 | .876/.851/.814/.810/.789 | .788/.747/.707/.687/.616 | .899/.879/.869/.848/.784 | 9471 |
| ens2 (c) b+rules-cands | 11 | .886/.869/.831/.829/.818 | .788/.737/.697/.687/.646 | .889/.848/.838/.828/.794 | 17255 |

## Gain of (b) and (c) over (a): held-out vs dev
hit@L = predicted path equals the reference path on the first L levels, abstention = miss, over all scored hosts (held-out 99, dev 199). Cells show net hosts, as held-out difference in points = net/99 and dev = net/199. W/L = hosts won/lost; p = exact two-sided sign test; CI = bootstrap 95% of the mean difference (5000 resamples, seed 1).

| model | L | held-out b-a | held-out c-a | dev b-a | dev c-a |
|---|---|---|---|---|---|
| gemma | 2 | -2 (4/6, p=.75, CI [-.081,+.040]) | -3 (3/6, p=.51, [-.091,+.030]) | +11 (20/9, p=.06, [.000,+.111]) | +17 (24/7, p<.01, [+.030,+.141]) |
| gemma | 5 | -5 (3/8, p=.23) | -4 (3/7, p=.34) | +11 (p=.06) | +16 (p=.01) |
| qwen | 2 | 0 (3/3, p=1.0, [-.051,+.051]) | +3 (7/4, p=.55, [-.030,+.101]) | +15 (17/2, p<.01, [+.035,+.121]) | +17 (25/8, p<.01, [+.030,+.141]) |
| qwen | 5 | -1 (4/5, p=1.0) | +2 (7/5, p=.77) | +15 (p<.01) | +18 (p<.01) |
| ens2 | 2 | -2 (2/4, p=.69, [-.071,+.030]) | -3 (2/5, p=.45, [-.081,+.020]) | +9 (15/6, p=.08, [.000,+.090]) | +18 (25/7, p<.01, [+.040,+.146]) |
| ens2 | 5 | -4 (3/7, p=.34) | -1 (5/6, p=1.0) | +12 (16/4, p=.01) | +22 (29/7, p<.01) |

Dev gains in points at L2 (acc, hit/199): gemma +5.5 (b), +8.5 (c); qwen +7.5 (b), +8.5 (c); ens2 +4.5 (b), +9.0 (c). Held-out: gemma -2.0/-3.0, qwen 0/+3.0, ens2 -2.0/-3.0. L1 and L3 give the same picture (full table in paired.md).

Other held-out observations: ens2 abstentions rise with rules (6 -> 10 -> 11; on dev they fell from b to c, 23 -> 17). Single-model abstentions drop slightly with rules (gemma 1 -> 0, qwen 2 -> 1 -> 0). Tokens per host x1.4 (b) and x2.6 (c).

## Verdict
The dev gain of the WZ rules does not hold on held-out hosts. For gemma and ens2, (b) and (c) are 2 to 5 hosts worse than (a) at L2 to L5; for qwen (b) is neutral and (c) is +3 hosts at L2. No held-out difference is significant (all sign tests p >= 0.23), and every held-out bootstrap interval contains 0, but the dev point estimates (+5 to +9 points at L2, partly p < 0.01) lie outside or at the edge of the held-out intervals of gemma and ens2 (upper limits +0.03 to +0.04). With 99 hosts we can exclude gains of more than about +4 points for gemma and ens2 (b/c), and about +10 points for qwen (c); a real gain of 2 to 3 points would stay undetected. Reading: the dev gain was mostly tuning to the dev errors (rules and rule-cited candidate codes were written from dev errors), plus label effects. Rules-candidates (c) is not better than (b) on held-out for gemma or ens2, and costs x1.8 tokens over (b); only qwen gains from it. Do not adopt the rules or --rules-candidates as the default WZ config on the strength of dev; plain (a) is at least as good on unseen hosts and cheapest. The ens2 precision/coverage trade-off holds in every config (P@2 .85 to .87 at cov@2 .85 to .90 vs single models P@2 .79 to .83 at cov@2 ~1).

## Caveats
- The held-out refs come from Sonnet passes with A=B 77% (dev 89.5% with Opus). Label noise lowers all accuracies and hides small differences symmetrically, but it is not biased toward or against the rules: the labellers did not see wz_rules.md.
- Adjudication was done by the lead agent on the two passes and the website texts, after the model runs finished but without reading any prediction.
- 99 hosts: one host = 0.010. The sign tests have low power; absence of significance is not proof of no gain.
- Held-out hosts come from the same gold pool as dev (same crawl, same eligibility); no distribution shift is tested.
- Dev "no rules" ens2 was rebuilt from the stage-2 gemma and qwen k30 preds (not stored earlier); the held-out (a) runs used the same configuration.
