# D37-full-e16-recheck · Re-fetch all E16 DACH imprint_not_found hosts with the E35 fetcher?

Issued 2026-11-04 by the data-collection lead. Blocks: the full E16 re-check (D36 B made it conditional on a user yes after the E36 pilot).

## Context (E36-fetch-recall-recheck-pilot, lead-verified)
- Population: 484,573 .de/.at/.ch hosts with E16 status imprint_not_found, minus hosts found in any E31 source (www-collapsed), minus the E32 audit sample.
- Pilot: 5,000 random hosts (seed 36), E35 tree b54aaa1 on apfel, 2026-11-04 07:58-08:30 UTC.
- Result: 294 imprint_found (5.9% of all, 6.1% of reachable). found_by: link 174, probe 63, kontakt 57.
- Labels (lead read 3 of 80, all agreed): kontakt 50 = 38 true / 5 false / 7 unclear; other 30 = 25 true / 0 false / 5 unclear.
  Kontakt false rate 10% (Wilson 95% CI 4.3-21.4%), 24% if unclear counts as false.
- False Kontakt finds: casino/spam pages on hijacked domains (3), contact pages with no operator or address (2).
- Expected for the full set if the pilot is representative: about 28.5k new imprint_found, about 5.5k of them by Kontakt (about 0.5k-1.3k wrong).
- The D33 rule (> 10% yield) was set for new-seed crawls; this pilot is below it.
- Wrong Kontakt finds without a DACH postal address fall out later under D16 / address extraction; spam pages with an address do not.

## Options
- **A** Run the full re-check now with the E35 fetcher. It queues behind E33 on apfel, mispel, abelie and aspe (about 480k hosts, 20 batches). Kontakt finds keep found_by=kontakt so they can be audited or dropped later.
- **B** First add a Kontakt guard (reject casino/spam text and pages with no postal address; new experiment, re-test on the 57 pilot Kontakt finds), then run the full re-check as in A.
- **C** No full re-check. Keep the 294 pilot finds; spend the VMs on new seeds (E33, E34 round 2).

Recommend A: about 28.5k new sites at no money cost; the Kontakt errors are tagged and mostly removed by address extraction.

## Answer
User 2026-11-04 ~09:15 UTC: "D37 A."
Run as E37-e16-full-recheck.
