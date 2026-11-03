# D29-depth2-rest-scope · What to crawl after the E22 depth-2 priority list?

Issued 2026-11-01 by the data-collection lead. Blocks: next E22 crawl on abelie (idle).

## Context
Depth-2 priority crawl (86,098 hosts on de/at/ch/eu/info/shop, D26 B) is done: 18,471 German-language Impressum pages (21.5% of hosts; .de 35.8%, .at 55.0%, .ch 22.6%, .eu 2.4%, .info 1.7%, .shop 3.4%). Depth 1 on the same TLDs gave 45.6% (abelie sample, 43,288 hosts), so the yield halves per depth step.
The depth-2 rest list has 1,715,061 hosts (com 630k, nl 177k, org 103k, net 89k, ...). At depth 1, non-priority TLDs gave 2.36% German Impressum (com 3.35%, net 4.17%, org 1.92%, nl 0.22%; abelie sample of 256,712 hosts). If depth 2 halves that: ~1-1.5% -> estimate 17-26k pages for 1.7M fetches (20x the priority list).
Depth 2 of frontier B (depth1B discoveries) and depth 3 of the priority path (depth2P discoveries) are not built yet; frontier.py builds them with known = seeds + A + B + round2_frontier.

## Options
**Recommend A:** far more German imprints per fetch, and it follows D19's DACH-first deep path; the rest list stays on disk for later.
- **A** Build the next priority frontier (inputs depth2P + depth1B discoveries, known = seeds + A + B + round2_frontier, priority TLDs only) and crawl it on abelie. Rest list later, if at all.
- **B** Crawl the depth-2 rest list, restricted to com, net, org (~822k hosts; estimate 10-15k pages).
- **C** Crawl the full depth-2 rest list (1.7M hosts; estimate 17-26k pages).

## Answer
"D29 C." (user, 2026-11-03), after asking "Is B a superset of A?" (answer: no, disjoint by TLD and source).
