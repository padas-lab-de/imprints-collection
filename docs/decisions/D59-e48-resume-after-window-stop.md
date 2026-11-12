# D59-e48-resume-after-window-stop

Issued 2026-11-12 (data-collection lead). Blocks: the r5 recount (D47 final count) and the E53 gold-set redraw frame.

**Context:** At 2026-11-11T00:40Z the E48 global watcher (D45) stopped all five VMs (GLOBAL STOP, window rule). The trigger was mispel: 11 throttled responses in its last 204 requests (5.4% > 5%). Before that, the throttled count on mispel was 2 in total. The other four VMs had win_thr=0. The lead noticed the stop only on 2026-11-12 12:19Z. The 2026-11-10 status ("all VMs healthy") was correct when it was written.
State at stop (watch.log): 81,603 of 96,722 hosts done, imprint_found 34,572. 15,119 hosts are not crawled. `ic fetch` resumes per host (the last complete row per host is final), so a restart continues where it stopped.

**Recommend A:** it finishes the existing run (D47), it halves the rate after the throttling, and it keeps the same stop rule. If Shopify throttles again, the watcher stops the run and we fall back to B without another card.
- **A** Resume E48 for the 15,119 remaining hosts on all 5 VMs at half rate (one request per 6 s per VM instead of 3 s), with the same window watcher (>5% throttled in the last 200 requests on any VM → stop all). If it stops again, freeze as in B. Measured rate before the stop: about 17 hosts per 5 min per VM at the full rate.
- **B** Freeze E48 as partial now: r5 uses the 81,603 crawled hosts. The 15,119 hosts not crawled are listed in the package and documented in the guide and the paper. Cost: about 6k missing sites if the imprint rate stays at 42% (about 0.16% of 3.9M).

**Outcome:** A with 5 s (user, 2026-11-12: "Go ahead with D59 A with 5s instead of 3s as it was before."). Resume on all 5 VMs at one request per 5 s per provider group (run 1: 3 s), same window watcher; the window counts only requests after the restart (since.txt, chk.sh SINCE). Scripts: /home/dinzinger/E48-shopify/resume.sh, start_resume.sh; run-1 copies *_run1.*. If the watcher stops it again: freeze as in B.
