# D15-gold-annotation-workforce (2026-10-23) — open
Question: who produces the gold labels?
Recommend A.
- A Model pre-labels (strong paid vision model on screenshot + rendered text, within $20/run, $30/day), a human verifies/corrects every item, a second human independently labels ~20% (agreement, Cohen's kappa). Fastest per item; risk of anchoring on model suggestions, reported via the independent 20%.
- B Two humans label every item from scratch, adjudicate disagreements. Strongest methodology claim; double human effort.
- C One human labels all from scratch, second human on ~20%. Middle ground.
