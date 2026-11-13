# D62-strato-blocked-captures

Issued 2026-11-13 (E53-gold-set-redraw, step 5). Blocks: labelling of about 106 of 1,869 items.

## Question
Strato answered 503 to the gold capture on akazie from about 10:59Z. 106 of 156 Strato items have only a landing-only capture (most with 503). ic fetch on aralie found an imprint for all 156. How do the labellers get a usable capture for these items?

## Options
- **A** One slow re-capture of the 106 items from akazie on a later UTC day (1 worker, long delay, no retry on 503). Items get `input_day_mismatch`. Items still blocked go to B. Cost: none; the input dates differ.
- **B** Label these items from the ic fetch text (impressum main_content) plus the landing-only capture; flag `capture_problem`. Cost: none; the labeller has no screenshot of the imprint.
- **C** Re-capture now from another VM (for example apfel, a different IP). Same day; this uses a new IP after a block. The auto-mode classifier refused this when the lead tried to start it; it needs your explicit yes.

**Recommend A, with B as fallback.** It respects the block and keeps a rendered capture for most items.

## Answer
C (user, 2026-11-13: "D62 C."). Re-capture from apfel, same UTC day.
