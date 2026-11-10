# E49 stage 3 summary: WZ rules, self-consistency, ensembles

Dev set: 200 hosts (results/E49/dev_hosts.txt), refs results/E49/refs/{poi,wz}.jsonl (two Opus passes, adjudicated). Scores: score.py --common (199 hosts). acc@L counts abstentions and stops above L as wrong. P@L = precision among hosts whose answer reaches L. Innkube only, no paid APIs. Full tables: scores/{wz,poi,poi_offline}.md.

## WZ 2025
| config | abst | P@1..P@5 | acc@1/2/3/5 | deepest P>=0.8 | s/host | tok/host |
|---|---|---|---|---|---|---|
| stage-2 gemma retrieve k30 | 3 | .857/.786/.750/.710/.683 | .844/.774/.739/.648 | L1 | 2.3 | 3.4k |
| gemma k30 + rules + keepout | 0 | .874/.829/.794/.761/.741 | .874/.829/.794/.704 | L2 | 5.0 | 4.8k |
| qwen k30 + rules + keepout | 3 | .867/.832/.816/.781/.747 | .854/.819/.804/.714 | L3 | 2.2 | 4.7k |
| gemma rules keepout, 5 samples t0.7 | 0 | .869/.824/.789/.756/.735 | .869/.824/.789/.698 | L2 | 12.2 | 24k |
| ens2 level-majority (gemma + qwen, rules, keepout) | 23 | .920/.889/.874/.852/.830 | .814/.764/.734/.643 | L5 | 7.2 | 9.5k |
| ens4 (no rules) | 19 | .894/.849/.820/.785/.782 | .809/.734/.688/.603 | L3 | 22.9 | 17.4k |

- Rules (results/E49/wz_rules.md, 11 rules from official include/exclude texts): acc@2 +5.5 (gemma), +7.5 (qwen) points. Needs --keep-outside, else rule-named codes outside the 30 candidates become abstentions.
- ens2 depth over 200 hosts: 157 to L5, 6 L4, 5 L3, 4 L2, 5 L1, 23 none (models disagree on the section).

## POI
| config | abst | P@1/2/3 | acc@1/2/3 | deepest P>=0.8 | s/host | offline acc@2 / P@2 |
|---|---|---|---|---|---|---|
| qwen flat think, input both | 10 | .942/.874/.722 | .894/.799/.769 | L2 | 25.9 | .872 / .893 |
| gemma flat reason | 2 | .904/.781/.789 | .894/.739/.714 | L1 | 8.4 | .779 / .787 |
| gemma flat reason, 5 samples | 4 | .908/.785/.789 | .889/.734/.709 | L1 | 23.0 | .779 / .793 |
| ens3 (qwen, gemma flat, gemma retrieve k60) | 8 | .937/.857/.737 | .899/.764/.734 | L2 | 36.0 | .820 / .859 |
| ens2 (qwen + gemma flat) | 22 | .960/.919/.769 | .854/.688/.653 | L2 | 34.3 | .750 / .921 |

- No POI config reaches P >= 0.8 at L3 (only 5 inner nodes have children there). Offline = refs with online_only false (172 hosts).

## Findings
- Self-consistency gives no gain (5 samples agree on 168/200 POI, 193/200 WZ hosts) at 2.5x latency and 5x tokens.
- Level-majority ensembles trade coverage for precision; they are the adaptive-depth route.

## Caveats
- WZ rules and --keep-outside were written after seeing dev errors; gains are optimistic and must be checked on the gold set.
- ~200 hosts: one host moves P by ~0.005; "deepest level" flips near 0.8.
- Latencies of rules runs are inflated (shared endpoint); ensemble s/host = sum of members.
