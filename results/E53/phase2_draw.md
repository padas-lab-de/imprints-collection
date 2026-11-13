# E53 step 4: phase-2 draw (D60 D, target (h))

Command (from the repository root, no network, no paid API):

    python3 -I scripts/E53/draw.py

Defaults: `--features datasets/E53/screen/screen_features.jsonl` (19,998 screened sites), `--frame datasets/E53/frame/frame.json` (N0 = 3,901,721, n1 = 20,000), `--out-dir datasets/E53/phase2`, seed 20261113 (= frame seed 20261112 + 1, the seed of the size table in `screen_coverage.md`), core 600. Outputs: `datasets/E53/phase2/gold_sample.jsonl`, `datasets/E53/phase2/quota.tsv`.

sha256 `gold_sample.jsonl`: `1fc67a2d8ac789998c57cfbeb5e95cb1bbce5a4d36dcf1430a0508eb9c081161`
sha256 `quota.tsv`: `5badfd19c0942e69a54144b1bf43b2f9472470ab8bff8562d06f79b40eb9682a`
Run twice (also with another `--out-dir`): same hashes.

Target (h): POI L1 (8), WZ section (22), address cases (7) at T = 25; POI L2 (357) and WZ group (287) at T = 5. Memberships: union of both screen models and the text detector, restricted to the target classes.

## Counts

| | items |
|---|---:|
| Core (SRS of the screened sites) | 600 |
| Oversample (rarest priority stratum first) | 1,195 |
| Stratum top-up (`--min-stratum 1`, lead 2026-11-13) | 74 |
| Total | 1,869 |

Core + oversample equal the size table of `screen_coverage.md` for (h) (600 + 1,195). Lead decision 2026-11-13: every priority stratum with M_h > 0 gets at least one item (`--min-stratum 1`, now the default), so no part of the frame has weight 0: 1,869 items, sum of weights 3,901,330.8 = N0 x 19,998/20,000, 0 empty strata. 574 strata; 161 hold a single item and are collapsed with a neighbouring stratum for variance estimation (collapsed-strata estimator). sha256 gold_sample.jsonl fc6d45a89355f48629cf1cbb7b590475443e0c6e124f695c14c07df9e453322e; quota.tsv 06ada591519be5ab5fc93c8cdb44e937cfd56a5ff8d23ddcb1d969914982d86c. Folds: 374/374/374/374/373.

## Coverage per depth (drawn = marginal count in the sample, all memberships)

| depth | classes | T | reach T | 0 members in screen | fewer than T members, all drawn | short although members exist |
|---|---:|---:|---:|---:|---:|---:|
| POI L1 | 8 | 25 | 8 | 0 | 0 | 0 |
| WZ section | 22 | 25 | 18 | 0 | 2 (B 6, V 2) | 2 (D 15 of 66, U 12 of 38) |
| address cases | 7 | 25 | 7 | 0 | 0 | 0 |
| POI L2 | 357 | 5 | 225 | 57 | 75 | 0 |
| WZ group | 287 | 5 | 217 | 23 | 47 | 0 |

Classes below T: 206 (801 missing items in total), listed in `quota.tsv` (columns target_T, screen_members, drawn, shortfall, all_members_drawn). Of these, 80 classes have no member in the screen (57 POI L2, 23 WZ groups), 124 have fewer than T members and all of them are drawn. Two more classes (WZ sections D and U) are short although the screen has members; see below.

### Short although members exist: WZ D and U

`wz1:D` (66 screen members) reaches 15 of 25, `wz1:U` (38 members) reaches 12 of 25. Cause: the oversample draws only from the priority stratum of a class (sites whose rarest target class is that class). Other members of D and U sit in rarer priority strata (a rare POI L2 or WZ group), and those strata are only drawn up to their own T = 5. When the D priority pool is used up, the class is still short. This is the same design behaviour as in the size table (206 "still short in sample" there). A fix would draw from all members of a class, but then the priority-stratum probabilities of 4.5 no longer hold.

## Weights

- Inclusion probability pi_i = (n1 / N0) x (m_h / M_h); weight w_i = 1 / pi_i. 500 priority strata have items.
- Weight range: min 195.09, median 682.8, max 22,044.7 (core items span the same range).
- Sum of weights: 3,649,474.7 (N0 = 3,901,721).
- The identity is: sum of w = (N0 / n1) x (sum of M_h over strata with at least one item). 74 priority strata with M_h > 0 have **no item** (1,291 screened sites, 6.5% of the screen). They have no weight, so the sum falls 6.5% short of N0. Cause: the core misses a small stratum (a stratum of 100 sites gets 3 core items on average), and the oversample does not need to draw it when other strata already fill the class quota.
- With `--min-stratum 1` (off by default, not part of target (h)) every stratum gets one item: 1,869 items (+74), sum of weights 3,901,330.8 = N0 x 19,998 / 20,000 (the screen has 19,998 of the 20,000 S1 sites). With `--min-stratum 2`: 1,979 items.
- The 20,000 vs 19,998 gap: pi uses n1 = 20,000; two S1 sites are not in the screen file.

## Folds (D58 A)

5 folds, stratified by priority stratum, strata with fewer than 5 items pooled per schema: fold sizes 359, 359, 359, 359, 359. 1,037 items sit in their own stratum, 758 in pooled "rare" groups (rare:poi 402, rare:wz 345, rare:addr 10, rare:other 1).

## Doubts about the probability formula

- pi = (n1 / N0)(m_h / M_h) is **conditional** on the realised m_h and M_h. m_h is itself random: the oversample stops when other strata's draws already cover a class, so m_h depends on the rest of the draw. Within a stratum the selected set is a uniform random subset of size m_h (core uniform, extras uniform from the rest), so the formula is the usual stratified post-hoc one, but it is approximate as an unconditional design probability. Weighted estimates are consistent for populations of strata with items; they are not design-unbiased.
- Strata without any item (74, 6.5% of the screen) get no weight. Population estimates by Hajek ratio then leave out that 6.5% of the frame. Decided (lead 2026-11-13): top up every stratum to one item (applied above). Alternatives were: top up every stratum (`--min-stratum`, +74 items for one item each) or collapse empty strata into a neighbour at the analysis stage.
- Strata with exactly one item have no within-stratum variance (the linearised CI of 4.6 needs at least two per stratum, or pooling).
- Weights use the screen as frame: S1 sites missing from the screen file are not in M_h.
