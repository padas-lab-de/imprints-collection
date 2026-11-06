# A14-abuse-reply-mispel-20261105

Issued 2026-11-05 11:37 UTC. Corrected 2026-11-05 after the user chose D39 B. Card file written late, at the correction.

**Action (user):** send this reply to the abuse desk (edit as needed). It closes the report on mispel (132.231.12.31). See D39-crawler-identification.

**Text:**

> The requests from 132.231.12.31 on 2026-11-04 16:11:57 UTC came from a research crawler at the University of Passau. It builds a dataset of German website imprints (Impressum pages). The crawler requested the start page of templers.de, which runs on 188.40.61.153, and standard imprint paths such as /impressum and /imprint: 7 requests in total, with no attack payloads. This was not a vulnerability scan. New crawls will send a crawler name and a contact URL (https://www.fim.uni-passau.de/data-science) in the User-Agent.

**Correction:** the first draft also promised "read robots.txt", "reduce the number of path requests" and a "block list". D39 B does not include them and no block list exists, so they are removed. The first draft also said "one request per path"; the status log shows 7 requests, so the text now states 7. The user must check the "University of Passau" wording.

**Outcome:** done. User 2026-11-06: "record the reply to the abuse report as done, as this matter has been clarified."
