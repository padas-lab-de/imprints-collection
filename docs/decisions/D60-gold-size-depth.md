# D60-gold-size-depth

Issued 2026-11-13 (E53-gold-set-redraw). Blocks: the phase-2 draw.

Question: how many items, and down to which schema depth do we guarantee coverage? (User 2026-11-12: more than 1,000 is fine if it makes the set more meaningful.)

Facts (results/E53/screen_coverage.md; full screen of 19,998 sites, 0 errors): every option has a random core of 600 for the population figures (acc@2 POI, acc@3 WZ, address). The oversample only adds rare classes. Classes too rare for the 20,000 screen (WZ B mining: 6 sites, V extraterritorial: 2; 57 POI L2 classes and 23 WZ groups: 0) get all sites the screen found. A larger screen does not help: filling them needs about 250,000 screened sites.

| Option | Coverage guarantee | Items | Labels (incl. ~20% double + calibration) |
|---|---|---:|---:|
| A | top level 25 each + WZ divisions 10 each | ~1,040 | ~1,350 |
| B | top level 25 each + WZ divisions 5 + POI L2 5 each | ~1,470 | ~1,860 |
| C | top level 25 each + POI L2 3 + WZ groups 3 each (evaluation depths) | ~1,330 | ~1,700 |
| D | top level 25 each + POI L2 5 + WZ groups 5 each | ~1,800 | ~2,260 |

Per-class rates need about 10+ items; 3-5 items per class serve only pooled analysis ("rare classes" as a group) and show that the label space is covered.

Recommend B: every reachable WZ division and POI L2 class (POI's evaluation depth) gets at least 5 items, so a pooled tail analysis has about 900 rare-class items; 40% more labels than A.

## Outcome
(open)
