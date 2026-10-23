# D14-gold-label-source (2026-10-23) — decided
Context: user wants a new gold set that replaces the old one, stratified by website diversity (old/new, corporate/personal, PHP/WordPress/Blogspot/..., JS rendering needed, imprint only in screenshot/image). User, verbatim: "I would like to rethink the evaluation with the gold set. The aspects that should be represented in the gold set should be that the respective websites originated from a diverse set of websites, some old, some new, some corporate websites, some personal, some php, some wordpress, some blogspot, some requiring JS rendering, some requiring parsing the web page screenshot, etc. The old gold set can be entirely substituted by a new one, if the new one stands out with this kind of sophisticated methodology."
Question: where do gold labels come from?
Recommend A.
- A From the live site as a human sees it: annotator opens the site in a browser, finds the imprint, labels address + topic; we archive static HTML, rendered DOM and screenshot per item so labels stay reproducible. Allows end-to-end evaluation per stratum (did the pipeline find the imprint at all, and extract correctly) — the JS and screenshot strata only make sense this way.
- B From the pipeline's fetched imprint text (as the old set). Measures extraction only; JS/screenshot sites have no text, so those strata cannot be evaluated.


## Answer (2026-10-23)
User, verbatim: "D14 A D15 C, go - just to be clear, the screenshot rendering is very much an edge case. I'm not even sure how often we really need it."
Outcome: A: labels from the live rendered site; archive HTML, rendered DOM, screenshot.
