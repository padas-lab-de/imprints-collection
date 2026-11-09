# E49 stage 1 run summary (qwen38-27b, 200 dev hosts, innkube, 8 workers, configs run one after another)

No reference scoring here. "agree" = agreement with a baseline run (POI: flat path home; WZ: flat depth 3 path home);
WZ "agree full" is only meaningful against depth-3 runs. Total: 29 configs, 10143 LLM calls, wall about 47 min (node descriptions for WZ: 2030 nodes, about 4 min, separate).

## POI (18 configs)

| run | n | err | abst | unres | outside | lvl | calls | tok in | tok out | emb+rr tok | s/host | agree L1 | agree full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| describe__qwen__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 26 | 0 | 0 | 2.09 | 2.0 | 1675 | 86 | 108 | 2.0 | 171/200 | 158/200 |
| describe__qwen__home__dmax__nt-path__k30__emb-kw__chooser-both | 200 | 0 | 24 | 0 | 0 | 2.11 | 2.0 | 2516 | 86 | 108 | 1.0 | 179/200 | 166/200 |
| flat__qwen__both__dmax__nt-path | 200 | 0 | 24 | 0 | 0 | 2.11 | 1.0 | 13530 | 22 | 0 | 5.3 | 192/200 | 186/200 |
| flat__qwen__home__dmax__nt-desc | 200 | 0 | 52 | 0 | 0 | 2.13 | 1.0 | 43071 | 23 | 0 | 17.3 | 168/200 | 153/200 |
| flat__qwen__home__dmax__nt-kw | 200 | 0 | 35 | 0 | 0 | 2.12 | 1.0 | 13808 | 21 | 0 | 5.1 | 188/200 | 179/200 |
| flat__qwen__home__dmax__nt-name | 200 | 0 | 27 | 0 | 0 | 2.11 | 1.0 | 9013 | 21 | 0 | 3.5 | 188/200 | 181/200 |
| flat__qwen__home__dmax__nt-path | 200 | 0 | 25 | 0 | 0 | 2.11 | 1.0 | 13080 | 22 | 0 | 4.9 | 200/200 | 200/200 |
| flat__qwen__home__dmax__nt-path__en | 200 | 0 | 47 | 0 | 0 | 2.11 | 1.0 | 13051 | 22 | 0 | 5.8 | 173/200 | 165/200 |
| flat__qwen__home__dmax__nt-path__reason | 200 | 0 | 17 | 1 | 0 | 2.11 | 1.0 | 13095 | 85 | 0 | 4.8 | 180/200 | 163/200 |
| flat__qwen__home__dmax__nt-path__shots4 | 200 | 0 | 26 | 0 | 0 | 2.1 | 1.0 | 13301 | 22 | 0 | 4.9 | 188/200 | 179/200 |
| flat__qwen__home__dmax__nt-path__think | 200 | 2 | 17 | 0 | 0 | 2.1 | 1.0 | 13116 | 717 | 0 | 13.1 | 175/198 | 159/198 |
| flat__qwen__home__dmax__nt-path__top3 | 200 | 1 | 35 | 0 | 0 | 2.11 | 1.0 | 13094 | 43 | 0 | 6.4 | 180/199 | 171/199 |
| flat__qwen__imprint__dmax__nt-path | 200 | 42 | 63 | 0 | 0 | 2.06 | 0.79 | 10258 | 17 | 0 | 4.2 | 129/158 | 109/158 |
| hier__qwen__home__dmax__nt-path | 200 | 0 | 17 | 0 | 1 | 1.75 | 1.94 | 3561 | 42 | 0 | 1.5 | 130/200 | 108/200 |
| hier__qwen__home__dmax__nt-path__beam2 | 200 | 0 | 1 | 4 | 2 | 1.76 | 3.99 | 7299 | 99 | 0 | 2.4 | 142/200 | 116/200 |
| retrieve__qwen__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 29 | 0 | 0 | 2.11 | 1.0 | 1546 | 22 | 877 | 1.3 | 174/200 | 161/200 |
| retrieve__qwen__home__dmax__nt-path__k30__emb-kw__rr | 200 | 0 | 25 | 0 | 0 | 2.1 | 1.0 | 1536 | 22 | 33147 | 1.3 | 177/200 | 165/200 |
| retrieve__qwen__home__dmax__nt-path__k60__emb-kw | 200 | 0 | 25 | 0 | 0 | 2.11 | 1.0 | 2016 | 22 | 877 | 1.1 | 184/200 | 170/200 |

Errors: [["no_input", 42], ["ValueError: no JSON object in reply: ", 2], ["ValueError: no JSON object in reply: Dealabs ist eine franzö", 1]]

## WZ (11 configs)

| run | n | err | abst | unres | outside | lvl | calls | tok in | tok out | emb+rr tok | s/host | agree L1 | agree full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| describe__qwen__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 2 | 0 | 0 | 4.98 | 2.0 | 3289 | 90 | 108 | 1.5 | 174/200 | 8/200 |
| describe__qwen__home__dmax__nt-path__k30__emb-kw__chooser-both | 200 | 0 | 2 | 0 | 0 | 4.98 | 2.0 | 4130 | 90 | 108 | 1.7 | 175/200 | 9/200 |
| flat__qwen__home__d2__nt-path | 200 | 0 | 0 | 0 | 0 | 2.0 | 1.0 | 3384 | 20 | 0 | 1.4 | 191/200 | 5/200 |
| flat__qwen__home__d3__nt-path | 200 | 0 | 0 | 0 | 0 | 3.0 | 1.0 | 13402 | 22 | 0 | 4.9 | 200/200 | 200/200 |
| hier__qwen__home__dmax__nt-incl | 200 | 0 | 0 | 0 | 0 | 4.27 | 3.83 | 6650 | 80 | 0 | 2.4 | 169/200 | 11/200 |
| hier__qwen__home__dmax__nt-incl__beam2 | 200 | 0 | 0 | 0 | 0 | 4.47 | 6.39 | 10041 | 141 | 0 | 2.1 | 175/200 | 11/200 |
| hier__qwen__home__dmax__nt-kw | 200 | 0 | 0 | 0 | 0 | 4.54 | 3.96 | 6654 | 83 | 0 | 2.8 | 184/200 | 11/200 |
| hier__qwen__home__dmax__nt-path | 200 | 0 | 0 | 0 | 0 | 4.22 | 3.81 | 4922 | 80 | 0 | 2.4 | 148/200 | 10/200 |
| retrieve__qwen__home__dmax__nt-path__k30__emb-kw | 200 | 0 | 7 | 0 | 0 | 4.99 | 1.0 | 3295 | 25 | 877 | 1.5 | 176/200 | 7/200 |
| retrieve__qwen__home__dmax__nt-path__k30__emb-kw__rr | 200 | 0 | 5 | 0 | 0 | 4.97 | 1.0 | 3098 | 25 | 43237 | 2.2 | 175/200 | 9/200 |
| retrieve__qwen__home__dmax__nt-path__k60__emb-kw | 200 | 0 | 3 | 0 | 0 | 4.97 | 1.0 | 5339 | 25 | 877 | 2.6 | 179/200 | 9/200 |

Errors: []

## Failure modes
- no_input: 42 of 200 hosts have no imprint text, so `--input imprint` errors for them (expected, not a bug).
- Empty content: think on gave 2 errors "no JSON object in reply" with empty reply (reasoning exhausted output).
- Prose instead of JSON: top3 gave 1 error (reply starts with prose, "Dealabs ist eine franzoesische ...").
- Unresolved ids: poi flat+reason 1; poi hier beam 2: 4; outside-candidate answers: hier 1, hier beam 2: 2. WZ: none.
- Abstentions (KEINE): highest for node-text desc (52), English prompt (47); beam 2 hier nearly none (1); WZ near none.
- Not run / differences from the brief: WZ "flat depth 2/3" use node-text path; WZ retrieve/describe use node-text path, emb-text kw (default); WZ describe run with both chooser desc and both. POI "reason" = `--reason short`. No flag was missing.
- No code changes were needed.
