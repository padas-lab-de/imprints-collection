# E53 step 6: labeller assignment

Items: 1869. Seed: 20261113. n_cal 50, n_second 375. Labellers L1, L2, L3 (names to be set).
Script: `scripts/E53/assign.py`, function `ic.gold.assignment.build_assignment_folds`. No network.

## Counts per labeller and role

| Labeller | primary | second | calibration | total |
|---|---|---|---|---|
| L1 | 998 | 124 | 50 | 1172 |
| L2 | 411 | 125 | 50 | 586 |
| L3 | 410 | 126 | 50 | 586 |
| all | 1819 | 375 | 150 | 2344 |

Calibration items have three `calibration` rows and no `primary` row (their gold label is the consensus). Items with one label: 1444; double-labelled (primary + second): 375; calibration: 50; together 1869.

## Second labels per pair

| Pair | items | first-named is primary / second is primary |
|---|---|---|
| L1-L2 | 125 | 63 / 62 |
| L1-L3 | 125 | 63 / 62 |
| L2-L3 | 125 | 63 / 62 |

## Per fold

| Fold | items | calibration | calibration core | second | L1-L2 | L1-L3 | L2-L3 | failed captures |
|---|---|---|---|---|---|---|---|---|
| 0 | 374 | 10 | 4 | 74 | 25 | 25 | 24 | 2 |
| 1 | 374 | 10 | 3 | 75 | 25 | 25 | 25 | 3 |
| 2 | 374 | 10 | 3 | 75 | 25 | 25 | 25 | 3 |
| 3 | 374 | 10 | 3 | 75 | 25 | 25 | 25 | 1 |
| 4 | 373 | 10 | 3 | 76 | 25 | 25 | 26 | 0 |

Core / oversample: sample 600 / 1269; calibration 16 / 34; second 120 / 255.

Failed captures: 9; in calibration: 0; in second labels: 0 (both excluded by design; they keep one primary label).
Strato landing-only items: 106, all kept in the assignment as normal items (card D62 decides their capture later); the assignment format has no field to mark them. In calibration: 4; in second labels: 17.

## Design choices

- Load split 2:1:1 over all labels incl. calibration (design 5.2): L1 1,172, L2 586, L3 586 of 2,344.
- Calibration: 10 per fold, core/oversample in proportion inside the fold; seeded random.
- Second labels: 375 = 125 per pair; drawn proportional over fold x core; pairs and directions dealt in fold order, so every fold is close to even over the pairs.
- Order: per labeller, calibration block first (random), then the rest (random). Not by stratum, weight or fold. The file holds no stratum, weight or fold.

## Files and sha256

| File | sha256 |
|---|---|
| `datasets/E53/gold/assignment.jsonl` | `37a72fb9afe8788392efcf7ee07a57ee589fe1ba66da9e6ff824ec857f7c8259` |
| `datasets/E53/phase2/gold_sample.jsonl` | `fc6d45a89355f48629cf1cbb7b590475443e0c6e124f695c14c07df9e453322e` |
| `datasets/E53/gold/prefill.jsonl (read only)` | `4edc04a2225941242f1c004032c53916a24705afad6d75b194744c97f0cc2088` |

