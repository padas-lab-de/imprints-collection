# E49 stage 2 run summary (200 dev hosts, innkube, 8 workers, configs one after another)

Models: qwen38-27b, gemma4-31b-it, qwen-agentworld-35b-a3b, soofi-s-isar-preview. No reference scoring here (see scores/).
"agree" = agreement with a baseline run (POI: flat path think, qwen; WZ: retrieve k30 kw path, qwen); WZ "agree full" is not meaningful for non-identical depth.
Qwen POI think, reason, retrieve k60 and the WZ qwen retrieve k30 / describe-both were copied from stage 1 (their s/host are the stage-1 values); WZ qwen rows re-run through the cache show very low s/host (0.2) because of cache hits, so ignore that column for them (stage 1: 1.5 and 1.7).
Pilot (--limit 5, one config per schema) passed for gemma, agentworld and soofi; no model dropped.
Qwen POI think and WZ retrieve think errors (empty reply, reasoning exhausted output) are counted in err; "abst" in the score files includes errored hosts.

## POI
| run | n | err | abst | unres | outside | lvl | calls | tok in | tok out | emb+rr tok | s/host | agree L1 | agree full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flat__agentworld__home__dmax__nt-path__reason | 200 | 0 | 8 | 0 | 0 | 2.09 | 1.0 | 13095 | 81 | 0 | 2.9 | 167/198 | 138/198 |
| flat__agentworld__home__dmax__nt-path__think | 200 | 56 | 56 | 0 | 0 | 2.09 | 1.0 | 13078 | 4120 | 0 | 60.2 | 139/143 | 126/143 |
| flat__gemma__both__dmax__nt-path__think | 200 | 0 | 4 | 0 | 0 | 2.11 | 1.0 | 13981 | 26 | 0 | 8.3 | 175/198 | 146/198 |
| flat__gemma__home__dmax__nt-path__reason | 200 | 0 | 2 | 0 | 0 | 2.1 | 1.0 | 13528 | 64 | 0 | 8.4 | 176/198 | 151/198 |
| flat__gemma__home__dmax__nt-path__think | 200 | 0 | 4 | 0 | 0 | 2.11 | 1.0 | 13513 | 26 | 0 | 7.5 | 175/198 | 145/198 |
| flat__qwen__both__dmax__nt-path__think | 200 | 1 | 10 | 0 | 0 | 2.09 | 1.0 | 13566 | 756 | 0 | 25.9 | 189/197 | 175/197 |
| flat__qwen__home__dmax__nt-path__reason | 200 | 0 | 17 | 1 | 0 | 2.11 | 1.0 | 13095 | 85 | 0 | 4.8 | 180/198 | 158/198 |
| flat__qwen__home__dmax__nt-path__think | 200 | 2 | 17 | 0 | 0 | 2.1 | 1.0 | 13116 | 717 | 0 | 13.1 | 198/198 | 198/198 |
| flat__soofi__home__dmax__nt-path__reason | 200 | 0 | 17 | 8 | 0 | 2.06 | 1.0 | 14884 | 50 | 0 | 2.3 | 130/198 | 88/198 |
| flat__soofi__home__dmax__nt-path__think | 200 | 1 | 4 | 0 | 0 | 2.1 | 1.0 | 14868 | 509 | 0 | 5.3 | 155/197 | 110/197 |
| retrieve__agentworld__home__dmax__nt-path__k60__emb-kw | 200 | 0 | 3 | 1 | 0 | 2.0 | 1.0 | 2016 | 22 | 877 | 1.0 | 168/198 | 139/198 |
| retrieve__gemma__home__dmax__nt-path__k60__emb-kw | 200 | 0 | 11 | 0 | 0 | 2.07 | 1.0 | 2058 | 26 | 877 | 1.7 | 178/198 | 153/198 |
| retrieve__qwen__home__dmax__nt-path__k60__emb-kw | 200 | 0 | 25 | 0 | 0 | 2.11 | 1.0 | 2016 | 22 | 877 | 1.1 | 178/198 | 160/198 |
| retrieve__soofi__home__dmax__nt-path__k60__emb-kw | 200 | 0 | 1 | 0 | 0 | 2.07 | 1.0 | 2569 | 24 | 877 | 0.7 | 147/198 | 109/198 |

Errors: [["ValueError: no JSON object in reply: ", 60]]

## WZ

| run | n | err | abst | unres | outside | lvl | calls | tok in | tok out | emb+rr tok | s/host | agree L1 | agree full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| describe__agentworld__home__dmax__nt-path__k30__emb-kw__chooser-both | 200 | 0 | 2 | 0 | 0 | 4.94 | 2.0 | 4166 | 96 | 111 | 2.7 | 172/200 | 138/200 |
| describe__gemma__home__dmax__nt-path__k30__emb-kw__chooser-both | 200 | 0 | 2 | 0 | 0 | 4.94 | 2.0 | 4190 | 84 | 88 | 3.9 | 175/200 | 139/200 |
| describe__qwen__home__dmax__nt-path__k30__emb-kw__chooser-both | 200 | 0 | 2 | 0 | 0 | 4.98 | 2.0 | 4130 | 90 | 108 | 0.3 | 185/200 | 166/200 |
| describe__soofi__home__dmax__nt-path__k30__emb-kw__chooser-both | 200 | 23 | 29 | 5 | 1 | 4.98 | 1.89 | 4664 | 85 | 87 | 1.7 | 134/177 | 94/177 |
| retrieve__agentworld__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 4 | 0 | 0 | 4.94 | 1.0 | 3295 | 28 | 877 | 1.3 | 174/200 | 149/200 |
| retrieve__agentworld__home__dmax__nt-path__think__k30__emb-kw | 200 | 72 | 73 | 0 | 0 | 5.0 | 1.0 | 3293 | 4246 | 877 | 69.7 | 126/128 | 125/128 |
| retrieve__gemma__both__dmax__nt-path__k30__emb-kw | 200 | 0 | 2 | 0 | 0 | 4.95 | 1.0 | 3846 | 29 | 1102 | 2.7 | 180/200 | 151/200 |
| retrieve__gemma__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 3 | 0 | 0 | 4.95 | 1.0 | 3363 | 29 | 877 | 2.3 | 183/200 | 158/200 |
| retrieve__gemma__home__dmax__nt-path__think__k30__emb-kw | 200 | 0 | 3 | 0 | 0 | 4.95 | 1.0 | 3363 | 29 | 877 | 2.4 | 183/200 | 159/200 |
| retrieve__gemma__home__dmax__nt-path__think__k60__emb-kw | 200 | 0 | 1 | 0 | 0 | 4.97 | 1.0 | 5467 | 29 | 877 | 5.3 | 176/200 | 149/200 |
| retrieve__qwen__both__dmax__nt-path__k30__emb-kw | 200 | 0 | 4 | 0 | 0 | 4.98 | 1.0 | 3759 | 25 | 1102 | 2.2 | 191/200 | 184/200 |
| retrieve__qwen__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 7 | 0 | 0 | 4.99 | 1.0 | 3295 | 25 | 877 | 0.2 | 200/200 | 200/200 |
| retrieve__qwen__home__dmax__nt-path__think__k30__emb-kw | 200 | 9 | 11 | 0 | 0 | 4.94 | 1.0 | 3331 | 1058 | 877 | 22.7 | 175/191 | 155/191 |
| retrieve__qwen__home__dmax__nt-path__think__k60__emb-kw | 200 | 7 | 9 | 0 | 0 | 4.96 | 1.0 | 5375 | 1023 | 877 | 15.4 | 174/193 | 149/193 |
| retrieve__soofi__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 3 | 2 | 1 | 4.98 | 1.0 | 3869 | 25 | 877 | 0.9 | 139/200 | 94/200 |
| retrieve__soofi__home__dmax__nt-path__think__k30__emb-kw | 200 | 4 | 4 | 0 | 0 | 4.97 | 1.0 | 3869 | 1407 | 877 | 9.9 | 159/196 | 125/196 |

Errors: [["ValueError: no JSON object in reply: ", 92], ["ValueError: no JSON object in reply: Der Betreiber der Websi", 22], ["ValueError: no JSON object in reply: Der Betreiber des Phili", 1]]

## Failure modes
- agentworld with think on: 28% (POI) and 36% (WZ) of hosts return an empty reply (reasoning exhausted the output), 60-70 s/host, 4100 completion tokens/host.
- soofi: weak accuracy on POI (acc@2 0.41-0.57) and WZ; WZ describe with chooser both: 23 errors (prose instead of JSON) and 29 abstentions.
- qwen think: 9 errors WZ k30, 7 errors WZ k60, 1 error POI input both (empty reply).
- Driver bug (not in scripts): grid.sh passed --out-dir .../<schema> while run.py appends the schema; files were moved up one level after the run.
