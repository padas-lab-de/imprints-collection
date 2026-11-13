# D62-e48-finish-remaining-hosts

Issued 2026-11-13 after the user asked "Is it possible to finalize E48?".

## Context
- E48-shopify was frozen as partial on 2026-11-13 per the D59 outcome (second window stop at 09:38:59Z, trigger lorbeer 11 throttled in 202 requests).
- Hosts left per VM: apfel 1,072, aspe 1,117, abelie 765, mispel 994, lorbeer 902 (about 4,850 of 96,722).
- Measured rate in the 24 h before the stop: 1,841 to 2,225 hosts per VM per day at 5 s per request.
- The crawl output is copied to e35 datasets/E48 (sha256 checked). The r5 count is built from that copy.
- A resume uses the same output dirs; `ic fetch` skips logged hosts and salvages the truncated gz tail.
- Cause of the 11-13 throttle burst is not known (the gold-lead fetch on aralie saw no throttling).

## Question
Finish the about 4,850 remaining E48 hosts, or keep E48 frozen as partial?

## Options
- **A** Resume on all 5 VMs at 10 s per request (half the D59 rate), same D39 B user agent, same watcher with the window reset. If the watcher stops it again: freeze for good, no further attempt. Then copy the new output again and rerun r5 (scan, recount, deltas).
- **B** Keep E48 frozen. r5 is final with E48 at 91,867 of 96,722 hosts; the paper states the 4,855 hosts as not crawled.

**Recommend A:** a complete crawl removes a limitation from the paper. The slower rate and the one-stop rule keep the throttle risk bounded.

## Outcome
(open)
