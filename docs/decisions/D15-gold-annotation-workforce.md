# D15-gold-annotation-workforce (2026-10-23) — decided
Question: who produces the gold labels?
Recommend A.
- A Model pre-labels (strong paid vision model on screenshot + rendered text, within $20/run, $30/day), a human verifies/corrects every item, a second human independently labels ~20% (agreement, Cohen's kappa). Fastest per item; risk of anchoring on model suggestions, reported via the independent 20%.
- B Two humans label every item from scratch, adjudicate disagreements. Strongest methodology claim; double human effort.
- C One human labels all from scratch, second human on ~20%. Middle ground.


## Answer (2026-10-23)
User, verbatim: "D14 A D15 C, go - just to be clear, the screenshot rendering is very much an edge case. I'm not even sure how often we really need it."
Outcome: C: one human labels all from scratch, second human ~20%; no model pre-labels.
