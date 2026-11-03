# D36-fetch-recall-patch

Issued 2026-11-03 ~22:40 UTC by the data-collection lead. Blocks: which fetcher version new crawls (E33 full crawls, E34 round 2) use; whether to re-check old imprint_not_found hosts.

## Context
E32-imprint-recall-audit (tmp/E32/summary.md; branch worktree-agent-a9cc78812de351bb8 @ 46b7fc7): of 300 DACH imprint_not_found hosts, 20 (6.7%, CI 4.4-10.1%) have a real imprint (name + postal address). 6 of those are found by today's code on re-fetch (crawl-time errors). The patch tmp/E32/fetch_change.patch (/impressum.php, /impressum.htm, probe after failed candidates, accept Kontakt page with imprint word + evidence, guards, query-only links) finds 18 of 20 on 32 replayed hosts, 1 false positive. New yield from the patch alone: 4.0% (CI 2.3-6.9%) of imprint_not_found hosts; E16 5.3%, E26 2.7%.

Running crawls (E26, E29, E30, E34, depth2R) use fetch.py sha256 c34d09b2... in the d29 tree; changing that file mid-crawl changes later batches.

## Options
- **A** Apply the patch (after review + tests) in a new tree for crawls started from now on; running crawls stay on c34d09b2. No re-check of old hosts. The paper states the fetcher version per source. Cost: none extra; recall differs slightly between sources.
- **B** A, plus a 5k re-check pilot of E16 imprint_not_found DACH hosts with the patched fetcher; full re-check (~486k hosts, rough +26k imprints) only if you approve after the pilot. Expected pilot yield ~4-5%, below the D33 10% rule, so it needs your explicit yes.
- **C** Keep the fetcher unchanged for all crawls (same code for the whole release). Cost: ~4-7% of imprint_not_found hosts stay missed.

Recommend B: the patch is cheap and validated; the re-check pilot measures the real gain before any large run.

## Answer
(open)
