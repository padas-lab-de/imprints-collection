# E49 stage 3b summary: WZ candidate-set variants

Setup as in stage 3 (retrieve, emb-text kw, node-text path, --rules results/E49/wz_rules.md, --keep-outside, home input, 200 dev hosts, scores --common = 199 hosts, refs results/E49/refs/wz.jsonl). Innkube only, no paid APIs. V1 = --k 60. V2 = --k 30 plus the 58 node ids cited in wz_rules.md (new flag --rules-candidates; tag suffix "rulescand"; off by default). V3 = V2 with --k 60. ens2 = level-majority of gemma4-31b-it + qwen38-27b. Full scores: results/E49/stage3b/scores/wz.md. acc@L counts abstentions and stops above L as wrong (strict, over hosts reaching L); P@L = precision among hosts whose answer reaches L; cov = coverage per level among hosts whose reference reaches L. Baselines are the stage-3 preds.

| config | abst | P@1..5 | acc@1..5 | cov@1..5 | s/host | tok/host |
|---|---|---|---|---|---|---|
| gemma k30 (baseline) | 0 | .874/.829/.794/.761/.741 | .874/.829/.794/.754/.704 | 1/1/1/.990/.979 | 4.97 | 4793 |
| gemma V1 k60 | 0 | .874/.839/.799/.774/.751 | .874/.839/.799/.759/.719 | 1/1/1/.980/.979 | 7.53 | 6896 |
| gemma V2 k30+rules-cands | 0 | .884/.859/.824/.796/.761 | .884/.859/.824/.784/.729 | 1/1/1/.985/.974 | 8.17 | 8779 |
| gemma V3 k60+rules-cands | 0 | .889/.864/.819/.793/.770 | .889/.864/.819/.789/.749 | 1/1/1/.995/.990 | 10.98 | 10525 |
| qwen k30 (baseline) | 3 | .867/.832/.816/.781/.747 | .854/.819/.804/.769/.714 | .985/.985/.985/.985/.984 | 2.24 | 4717 |
| qwen V1 k60 | 1 | .869/.833/.818/.802/.764 | .864/.829/.814/.794/.734 | .995/.995/.995/.990/.990 | 7.04 | 6762 |
| qwen V2 k30+rules-cands | 1 | .864/.833/.823/.792/.763 | .859/.829/.819/.784/.729 | .995/.995/.995/.990/.984 | 8.25 | 8523 |
| qwen V3 k60+rules-cands | 1 | .864/.838/.818/.803/.766 | .859/.834/.814/.799/.739 | .995/.995/.995/.995/.995 | 9.31 | 10225 |
| ens2 k30 (baseline) | 23 | .920/.889/.874/.852/.830 | .814/.764/.734/.693/.643 | .884/.859/.839/.814/.793 | 7.21 | 9510 |
| ens2 V1 k60 | 21 | .921/.901/.886/.870/.851 | .824/.779/.744/.709/.658 | .894/.864/.839/.814/.798 | 14.57 | 13658 |
| ens2 V2 k30+rules-cands | 17 | .918/.894/.886/.864/.839 | .839/.809/.779/.734/.693 | .915/.905/.879/.849/.834 | 16.42 | 17302 |
| ens2 V3 k60+rules-cands | 19 | .922/.904/.884/.870/.854 | .834/.804/.769/.739/.688 | .905/.889/.869/.849/.819 | 20.28 | 20751 |

Latency: endpoint shared, ens2 s/host = sum of members; read as rough ratios only. Tokens grow with the candidate list (rules-candidates adds up to 58 ids plus ancestors).

## ens2 depth distribution (hosts per canonical answer depth, 200 hosts)
| config | none | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|---|
| baseline | 23 | 5 | 4 | 5 | 6 | 157 |
| V1 k60 | 21 | 6 | 5 | 5 | 6 | 157 |
| V2 k30+rules-cands | 17 | 2 | 5 | 6 | 7 | 163 |
| V3 k60+rules-cands | 19 | 3 | 4 | 4 | 8 | 162 |

## Findings
- V1 (k60 alone) gives small gains: ens2 P@2 .889 -> .901, abstentions 23 -> 21; singles move by at most 1 point; cost +40% tokens.
- V2 (rules-candidates) helps most: gemma acc@2 .829 -> .859, acc@3 .794 -> .824 (gemma single model now matches the old ens2 on P@2); ens2 abstentions 23 -> 17, acc@2 .764 -> .809, acc@3 .734 -> .779, P@5 .830 -> .839. Qwen is flat (within 1 host). Tokens x1.8.
- V3 (both) adds little over V2: ens2 P@2 .904 / P@5 .854 (best) but acc@2/3 and abstentions are worse than V2 (19 vs 17); gemma single improves (acc@5 .749) at +20% tokens over V2.
- The 12% no-code problem is reduced to 8.5% (V2), not removed: the models still disagree on the section for about 17 hosts.

## Recommendation
Use V2 (k30 + --rules-candidates) for both models in the adaptive ens2. It gives the best coverage and acc@1..5 of the ensembles at 1.8x tokens of the baseline; P@1..3 are equal to the other variants within noise (one host = 0.005). k60 is not worth the extra cost on top. Single-model fallback: gemma V2/V3.

## Caveats
- Rules and rule-cited candidates came from reading dev errors (rule codes) and are tuned on the same 200 hosts: gains are optimistic; confirm on the gold set.
- Differences of 1-3 hosts (0.005-0.015) are within noise; V2 vs V3 is not distinguishable.
- Qwen had 1 error host in the V2/V3 runs (counted as abstention).
