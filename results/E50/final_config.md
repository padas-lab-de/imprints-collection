# E50 final configs (frozen 2026-11-10, before stage F)

Selected on dev 500 (E49 dev 200 rendered DOM + E51 dev2 300 static HTML) with design.md section 7, "cheapest
non-inferior". Tables: results/E50/dev500/{poi3,wz,address,joint}_{all,e49,e49_noimprint,e51}.md.
Held-out (stage F) runs these configs once, for all three models; no change after F.

| schema | config | e50_run.py arguments |
|---|---|---|
| POI (poi3) | flat, all candidates, site_first layout, base wording, de, fmt free, 6000 chars/field, landing page + imprint; reasoning gemma short, qwen low, agentworld short | `--task topic --schema poi3 --reasoning {short\|low\|short}` |

Note 2026-11-12: the user set POI **retrieve k30** as the default (cost ratio 0.21, -0.027 on dev); flat stays an E52 variant. See docs/extraction_strategy.md.
| WZ | retrieve k30 (node text path, embedding text kw), base wording, de, fmt free, 1500 chars/field, r-none | `--task topic --schema wz --reasoning none --site-chars 1500` |
| address | mode main, fmt json_schema, r-none, imprint input, 6000 chars | `--task address --reasoning none --mode main --fmt schema` |

Dev 500 evidence (pooled, paired vs the base config):
- POI qwen r-low vs r-default: d acc@2 +0.010 [-0.012, +0.030], C ratio 0.93, fail 0.000 vs 0.004. gemma and
  agentworld keep the phase-1 base (short). Rejected: list_first_q -0.053 [-0.077, -0.028] (C 0.19); retrieve k30
  -0.027 [-0.049, -0.008] (C 0.21; agentworld +0.049, gemma -0.026, qwen -0.028); joint POI+WZ -0.087, joint
  POI+WZ+address -0.134.
- WZ c1500 vs c6000: d acc@3 +0.001 [-0.011, +0.013], C ratio 0.84 (e49 +0.008, e51 -0.003). Rejected: gemma r-short
  +0.002 [-0.018, +0.022], C 1.11 (phase-1 candidate, not confirmed).
- Address mode-main + f-schema vs list/free: d main_ok -0.002 [-0.010, +0.006], C ratio 0.71 (agentworld +0.034,
  gemma -0.010, qwen +0.006). Rejected: c3000 -0.012 [-0.023, -0.002]; reasoning short/low no gain.
- Separate calls per schema (joint calls lose 0.02-0.20 per part).

Commands (stage F):
    python3 -I scripts/E50/build_sets.py --set heldout
    for each model m and its POI level r: python3 -I scripts/E50/e50_run.py --dev datasets/E50/heldout300_inputs.jsonl
        --allow-heldout --out-dir results/E50/preds/heldout300 --model m --workers 6 <arguments above>
    bash scripts/E50/report_set.sh heldout300 results/E50/heldout300
