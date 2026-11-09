# D47-collection-wrap-up

Issued 2026-11-09 (lead, asked live). Blocks: the end of the data collection.

**Context:** The user asked to straighten the project, because imprint collection is at its end: no new jobs, only finishing existing runs (E48), and make the collection reproducible for another person with few commands. At issue time master held only the 2026-02 upload; all collection code was on 13 unmerged branches; run scripts for E22-E48 lived on the VMs and in the lead's temp folder; 11 GB of durable data were on lorbeer only.

**Questions and answers (user, 2026-11-09, verbatim choices):**
1. Git: "One branch + draft PR". One branch `collection-release` off lead-record merges all collection branches and the run scripts now outside git; one draft PR to master; the user merges.
2. Scope: "Collection only". Crawling, counts, filter, seed lists and their docs. Gold-set and extraction files stay as they are; the README only links to them.
3. Data: "Upload the data to S3 to the instance with the alias innkube in the bucket datasets under imprints/20261109/". (mc alias innkube = https://share.innkube.fim.uni-passau.de; binary ~/minio-binaries/mc on lorbeer.)
4. Recount r5: "Yes, run r5 at the end". After E48 ends: copy its data, recount r5 with E48 and the E34 round-4 pilot, round-2 filter with r2_name_for_sale flag-only. That is the final count.

**Outcome:** answered; work in flight (see decisions.md In flight).
