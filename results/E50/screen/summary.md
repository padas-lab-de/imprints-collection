# E50 phase 1: topic prompt screening, summary

Written by the lead from the agent report (2026-11-10); the agent could not write this file.
Set: E49 dev 200 (199 scored), rendered-DOM inputs. Held-out not touched.
Full tables: `poi3.md`, `wz.md` (same folder). Rule for choice: "cheapest non-inferior" (`../design.md` §7).
Lead check: tests 238 passed; numbers below match the tables.

## Results

- The base prompts hold. No wording variant (w-guide, w-minimal, en, s4) and no output format (json_object, schema) beats base by a clear margin.
- POI v3, acc@2: gemma r-short base 0.799 (best); qwen r-default base 0.784; agentworld r-short 0.719.
- WZ, acc@3: gemma r-short base 0.749; qwen r-low 0.744; agentworld r-short 0.739. Reasoning "none" costs about 0.01 to 0.03.
- Input budget: c1500 is cheaper and non-inferior for WZ (+0.008 [-0.008, +0.025], cost ratio 0.85). For POI, c1500 loses 0.03 on gemma; c3000 is level.
- Cost: the POI prompt is about 24k input tokens per host (the schema is most of it). `list_first` (schema first) gets a cache ratio of about 0.9 (C/C0 = 0.09 to 0.26) but loses 0.04 to 0.06 acc@2.

## Candidates to confirm on dev 500 (phase 2)

- POI: qwen reasoning low (+0.025 in screen).
- WZ: gemma reasoning short (+0.030 over none).
- POI cache layout: schema first, site text and question last (not yet tested). If it keeps acc@2, the POI cost drops by about 4x.

## Phase-2 needs

- Merge lead-record (E51 refs and inputs) into the branch.
- Address scorer adapter for the `address_spec` format.
- Keep E51 (static HTML) and E49 (rendered DOM) score tables separate. Report the 72 E49 hosts with an empty imprint text separately.
- Stages: C address factors on dev 500; D call layout (joint vs. separate, cache layout); E combine and confirm; F held-out 300 once.
