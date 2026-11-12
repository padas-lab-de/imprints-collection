# E53 frame F0 and phase-1 sample S1

- Frame source: `/home/dinzinger/GitHub/imprints-collection-e35/datasets/E40/r2/canonical_sites_after_filter.txt` (sha256 `748f70f44517f62e627997e7697d910956b477fb560b025db1cab1b3c1e717a2`), U = 3,908,045 sites.
- Exclusion keys (union of the lists, www-collapsed): 12,495.
- Removed from U: 6,324. **N0 = 3,901,721.**
- Permutation: sort by sha256(f'{seed}:{key}'), key = lower-case host without leading www., seed 20261112. Stored: `datasets/E53/frame/F0_perm.txt` (sha256 `4989f2daaeb5364f095aa587cd9259f7aa926e3b0d021bfe1fa984dfa2b006ee`).
- S1 = first n1 = 20,000 of the permutation: `datasets/E53/phase1_hosts.txt` (sha256 `6b3b96bd8deda693adc30b6897392a66f1314d04ce61cc9c5b69cb4813bbcd51`). A longer prefix extends S1 and stays an SRS of F0.

| list | keys | removed from U |
|---|---:|---:|
| old_gold | 1,000 | 815 |
| e8 | 1,000 | 473 |
| e12_screen | 9,999 | 4,588 |
| e12_sample | 1,000 | 560 |
| e49 | 300 | 206 |
| e51 | 500 | 452 |
| union | 12,495 | 6,324 |
