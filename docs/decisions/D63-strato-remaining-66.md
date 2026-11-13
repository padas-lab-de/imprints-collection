# D63-strato-remaining-66

Issued 2026-11-13 (E53-gold-set-redraw, after D62 C). Blocks: a usable imprint capture for 66 of 1,869 items.

## Context
D62 C re-capture from apfel (13:52-14:13Z, 2 workers): 40 Strato items now landing+imprint (42 hosts replaced). Strato answered 503 on apfel too from about 14:05Z (after about 50 items). The agent's stop check watched memory only, so the run went on past the first 503s until it finished (63 static + 47 rendered 503). 66 Strato items stay landing-only. ic fetch (aralie, same day) has an imprint text for all of them. The block on a second IP suggests Strato throttles by volume, not only by IP.

## Options
- **A** One slow re-capture of the 66 on a later UTC day from one VM (1 worker, long delay, stop at the first 503). Items get `input_day_mismatch`. Items still blocked go to B. Cost: none; input dates differ from the ic fetch text.
- **B** Label the 66 now from the ic fetch imprint text plus the landing-only capture; flag `capture_problem`. Cost: none; no imprint screenshot for 3.5% of items, all Strato-hosted.

**Recommend A, with B as fallback.** Labelling start is parked anyway (D21), so a later-day slow retry costs nothing, and it keeps a rendered capture for most items.

## Answer
(open)
