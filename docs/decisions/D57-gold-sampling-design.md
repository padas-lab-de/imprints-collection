# D57-gold-sampling-design

Issued 2026-11-12 (E53-gold-set-redraw). Blocks: the draw.

Question: how do we spread 1,000 items over the population so that address, POI and WZ can all be evaluated?

Facts: only cheap features exist for all 3.9M sites (TLD, crawl source, language, text length, found_by). Topics and address cases need a model pass. E50 prompts are fixed and run free on innkube.

- **A (recommended)** Two-phase design, as v0.2 but on the new frame. Phase 1: screen a random 20,000 sites with the fixed E50 prompts (two models, crawl text) and the text detectors. Phase 2: a random core of 600 (population figures) + an oversample of 400 so that every POI top-level class, every WZ section (A-V (22 sections)) and every hard address case (AT, CH, P.O. box, no address, several addresses, non-German text) gets about 25 items where the population allows. Horvitz-Thompson weights for every item. A stratum counts as covered when either of the two models predicts it, so no single model decides the oversample.
- **B** Simple random sample of 1,000. Unbiased and simple; rare WZ sections and hard cases get 0 to 5 items.
- **C** Equal quota per WZ section and POI class (no random core). Best per-class coverage; no population figures.

Recommend A: gives population figures and per-class results with one set.

## Outcome
A (user 2026-11-12): "D57 A; note that if 1000 items in the evaluation dataset is too few to cover all categories in the schemas, we can also increase the number of items. It does not have to be 1000 if it renders the evaluation dataset less meaningful. I am also not sure about the depth to which we have cover the schemas in the dataset. You proposed only top-level categories / sections, is that right?" Lead: set size and coverage depth after the phase-1 screen, with real class counts (next card).
