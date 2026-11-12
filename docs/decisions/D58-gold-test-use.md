# D58-gold-test-use

Issued 2026-11-12 (E53-gold-set-redraw). Blocks: E52 protocol, not the draw.

Question: the gold set also sets the publish depth (P >= 0.8 per level) and picks the model. How do we keep the reported numbers honest?

- **A (recommended)** Cross-fitting: choose the depth cut-off on 4 of 5 folds, apply it to the 5th, report the out-of-fold numbers. All 1,000 items are test items. Model choice on the full set is reported as such (3 to 5 candidates; small selection effect).
- **B** Fixed split: 200 items for cut-off and choice, 800 for the reported numbers. Simple, but 20% fewer test items and weaker rare-class results.

Recommend A.

## Outcome
(open)
