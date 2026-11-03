# D34-release-www-dedup · Count and release www.x and x as one site?

Issued and decided 2026-11-03 by the user (no card needed; recorded for the paper).

## Context
- E16 has 423,017 sites found under both www.x and x. Exact-host count 3,564,994; www-collapsed 3,136,881 (dedup 2026-11-03 15:59 UTC, scripts/E22/dedup_count.py).

## Answer
User 2026-11-03: "regarding the www twins, I want to be honest about the number. It is not that important for me to report any increase over the previous number of unique imprint hosts. Actually, in our paper, we don't want to kind of do this comparison between the previous 3.56 million and what we have now. We just want to report what we have now, and this number has to be honest. So for the release, deduplicate the www. Items."

## Consequence
- Release and paper: www-collapsed count is the headline; no comparison with the original dataset.
- Variant per twin pair: the final host after redirect if known, else the non-www form. User 2026-11-03: "I like your plan that the host, the site that redirects to, is chosen if we know it, and otherwise the non-www form."
