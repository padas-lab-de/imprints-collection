# D56-gold-input-form

Issued 2026-11-12 (E53-gold-set-redraw). Blocks: capture of the new gold items.

Question: what do the annotators see, and what do the models get, so that the evaluation speaks for the release run?

Facts: the release run extracts from crawl text (`ic fetch`: main_content of static HTML for landing, kontakt, impressum); the crawl keeps no HTML. The crawl is weeks old; sites change. The old gold captures are rendered DOM + screenshot from the live site (D14 A).

- **A (recommended)** Fresh fetch on one day per item: run `ic fetch` (the release fetch code, from the crawl VM) and the gold capture (static HTML, rendered DOM, screenshot) on the same day. Annotators label the site from the capture; models get the `ic fetch` text. Items where `ic fetch` finds no imprint stay in the set: they measure the fetch step, and the models get what the pipeline would get.
- **B** Models get the stored crawl text; annotators label from the stored crawl text plus a fresh capture as a help. Items where the site changed since the crawl are flagged and left out of scoring.
- **C** Models and annotators both get the rendered DOM capture only (as E49). Clean labels, but the input differs from the release run.

Recommend A: same input form as the release, labels and inputs from the same day, no change-over-time noise.

## Outcome
(open)
