# Lead record

## Modules (since 2026-10-26)
Two module leads share this record; each owns its In-flight block, cards and experiments.
- **Gold set** (labelling and capture of the gold dataset; E8, E12, E17, E18, E21, D14-D17, D21, D24): lead session on lorbeer.
- **Data collection** (crawl for the new dataset version; E16, E19, E20, D23, crawl VMs): its own lead session.
- IDs stay one sequence per kind for the project: `git pull` before issuing a card or experiment, take the next free number, commit and push the record at once.
- Touch only your module's lines; anything that crosses modules (VM use, shared data on aspe/lorbeer, spend ledger) goes to Cards or a note in both In-flight blocks.

## In flight
### Gold set
- Labelling not started: waits on D21, names for L1-L3, access route, calibration date. Tool + prefill on lorbeer (datasets/gold, prefill.jsonl e21-v1+filter1). Proposed: time-per-item summary; check the 11 hosts whose main address the filter removed.

### Data collection (owned by the data-collection lead)
Lead VM: lorbeer (crawls E16 107-156 since 2026-10-26, D23). Crawl VMs: plain `ssh <vm>` (A7 done); repo at ~/GitHub/imprints-collection on aspe, apfel, abelie (abelie: symlink to /tank/docker/dinzinger, ready but idle per D23; akazie: clone for the Strato capture).
Only on aspe (untracked): datasets/E16/seeds (batches 0-156), datasets/gold (952 captures, assignment.jsonl), datasets/E12, datasets/E19, .env, photon geocoder (~/opt/photon), venvs in worktrees agent-a9795ebab2b1874a2 (E16) and agent-ac37363e2dedffa7e (.venv-render + .render-libs for gold capture); do not remove.
- E16-snapshot-crawl-seeds: 263 batches of 25k from datasets/E16/seed_hosts_shuffled.txt (sha256 d89354b8..., same file on every VM), cap 8, scripts/E16/run.sh STEP=3. State 2026-10-28 ~06:50 UTC (live check); all four drivers healthy; expected end ~2026-10-29 07:00 UTC (slowest: lorbeer, mispel).
  - aspe: `run.sh 58 106` (waiter pid 160995 after A9, 2026-10-26 17:28 UTC; PY = worktree venv agent-a9795ebab2b1874a2). At range 91-93, ~64 min/batch, RSS 2.3 GB, 20 GB RAM available, 49 GB disk free.
  - apfel: `run.sh 169 213` (waiter pid 1226237 after A10, 2026-10-26 20:08 UTC; PY=.venv). At range 202-204, ~58 min/batch, 131 GB disk free. E19 runs beside it (see below).
  - lorbeer (132.231.12.38, outside the crawl /24): `run.sh 107 156` pid 347423 since 2026-10-26 17:25 UTC, clone /home/dinzinger/GitHub/imprints-collection at 636d938 (PY=.venv). Batch 137 nearly done, ~75 min/batch. Tight: 3.3 GB RAM available (shared with gold labelling and another user), disk 87% (50 GB free).
  - mispel (132.231.12.31, same /24 as lorbeer): `run.sh 214 262` pid 1128613 since 2026-10-26 17:33 UTC, ~73 min/batch, at range 241-243; RSS 5.0 GB, 22 GB available, 23 GB disk free. Tree is a `git archive` of b0160a2, not a git repo (mispel cannot reach GitHub or aspe; relay via lorbeer); venv via `~/.local/bin/virtualenv`; 188 tests.
  - D23: akazie/aralie/abelie wait for the user's extra local storage. Re-split when one joins: lower a driver's LAST by killing its run.sh (the child finishes its range) and restarting with the new LAST; never edit run.sh while a driver runs.
  - Check: `tail results/E16/logs/driver.log`, `ls datasets/E16/seeds | grep -c status_batch` per VM. Done when every driver logs "all done"; then collect fetch_status_batch*.tsv + records from all VMs into one place.
- E20 production check: scripts/E16/rss_log.sh logs RSS every 10 min to results/E16/logs/rss.log on aspe and apfel. Not flat: within a range RSS climbs ~1.8 -> 5.4 GB over 3 batches (~0.6 GB/h; aspe 52-54, apfel 157-162), reset at each restart, so STEP stays 3.
- E19-crawl-recovery-pass round 1: apfel, `run.sh datasets/E19/round1/round1_no403.txt` (55,887 hosts = retryable non-403 causes from complete E16 batches 0-49 via collect.py --out-dir datasets/E19/round1 on aspe, minus the 1,000 pilot hosts, plus 48 Strato gold; sha256 f3ff5258...) since 2026-10-26 10:42 UTC -> datasets/E19/round1, log results/E19/logs/driver_round1.log + fetch_recovery.log. One fetch process (pid 133348) covers batches 0-2 of the shuffled list. Behind: 2026-10-28 ~06:50 UTC batch 0 at 22,888/25,000 after ~44 h, <=9 hosts/min, tail parked on Shopify 23.227.38 and Cloudflare 172.66.3/162.159.143 (~25% of all round-1 hosts); batches 1-2 (30,887) not started. Route: D25-e19-round1-reshard (open). When done: copy fetch_status_batch*.tsv to aspe, `merge_report.py --recovery-dir datasets/E19/round1 --list .../recovery_input.txt`; batches 50+ get a round 2 after E16.

## Cards
| ID | Date | Question | Outcome | Landed in |
|---|---|---|---|---|
| D25-e19-round1-reshard | 2026-10-28 | Finish E19 round 1: keep apfel alone, reshard the rest over 4 VMs after E16, or drop slow networks? | open (recommend B) | — |
| A10-apfel-driver-last-213 | 2026-10-26 | Lower apfel's E16 driver to LAST=213 (mispel has 214-262); auto mode denied the lead | "A10 go" (user); lead did it 20:08 UTC | apfel driver.log |
| A9-aspe-driver-last-106 | 2026-10-26 | Lower aspe's E16 driver to LAST=106 (lorbeer has 107-156); auto mode denied the lead | "A9 go" (user); lead did it 17:28 UTC | aspe driver.log |
| A8-mispel-ssh-key | 2026-10-26 | Add lorbeer's public key to mispel's authorized_keys | done (user) | — |
| D24-gold-prefill-scope | 2026-10-26 | Which gold labels start from a model suggestion (reverses D15's no pre-labels)? | B: suggestions on all 1,000 items | `--prefill all` default |
| D23-shared-vm-crawl | 2026-10-26 | Which of akazie/aralie/abelie (shared with another user's jobs) run E16? | E16 on apfel + aspe only for now; user sorts out the other three (user). 2026-10-26 later: lorbeer and mispel cleared too; the three wait for extra local storage (user) | — |
| A7-ssh-dir-owner-lorbeer | 2026-10-26 | chown ~/.ssh on lorbeer (root-owned; ssh cannot save host keys) | done; known_hosts filled, push works | — |
| A6-tank-dirs-crawl-vms | 2026-10-26 | sudo-create /tank/dinzinger on abelie (root disk 95% full) | done: /tank/docker/dinzinger on abelie; repo + venv ready there, idle (D23) | — |
| D22-crawl-speedup-route | 2026-10-24 | Speed up the crawl: parallel VMs + polite limits + recovery pass from a 2nd IP, or a faster first round with looser limits + slow second round? | A: polite limits, more VMs, recovery pass from 2nd IP (user) | — |
| D21-guideline-open-points | 2026-10-24 | Accept the labelling guideline's seven judgement calls as drafted? | open (recommend A) | — |
| A5-crawl-vm-access | 2026-10-24 | Hostnames + SSH access for the extra crawl-subnet VMs | done 2026-10-26: 5 VMs, own IPs 193.175.2.84-90 (one /24); limits -> D23, A6 | — |
| D20-crawl-machines | 2026-10-24 | Spread the crawl over more machines: more crawl-subnet VMs, FAITH nodes, or this VM only? | A: more crawl-subnet VMs (user) | — |
| D19-link-expansion-depth | 2026-10-24 | Link expansion depth 1 all TLDs, plus depth 2-3 on .de/.at/.ch only, or depth 3 all TLDs? | C: depth 3 across all TLDs (user) | — |
| D18-snapshot-provider-cap | 2026-10-24 | Full seed crawl at 4 or 8 parallel requests per provider network? | C -> E15 run, then lead picked 8 (B): Strato block 0.7% vs 0.44%, IONOS 0.24% vs 0.53%, found rate equal, 59 vs 74 min per 25k | — |
| D17-gold-set-size | 2026-10-23 | Gold set ~1,300 items (~80 annotator h) or lean ~1,100? | B, cut to 1,000 items; no stratum comparisons needed (user) | — |
| D16-link-expansion-scope | 2026-10-23 | One round with ccTLD filter, all TLDs, or none? | B: all TLDs, keep DACH-address imprints; depth up to 3 under test (E14) (user) | — |
| D15-gold-annotation-workforce | 2026-10-23 | Who labels: model pre-label + human check, or humans from scratch? | C: every item labelled once from scratch, a second person independently ~20%; no model pre-labels (user). 2026-10-24: three labellers, one with double capacity (user) | — |
| D14-gold-label-source | 2026-10-23 | Gold labels from the live rendered site or from fetched text? | A: label from the live rendered site; archive HTML, DOM and screenshot (user) | — |
| D13-personal-data-release | 2026-10-23 | Open, two-tier or derived-only release of personal imprint data? | B: full open release, assume best case (user) | — |
| A3-dpo-consultation | 2026-10-23 | Ask Uni Passau DPO about publishing imprint personal data | dropped by user | — |
| A4-apc-funding | 2026-10-23 | Who pays the EUR 2,390 APC (DEAL agreement?) | done: covered by Uni Passau agreement | — |
| D12-town-granularity-metric | 2026-10-23 | How to score town/district differences? | A: geocoding-based location match primary; guideline copies town as written | — |
| D11-topic-eval-input | 2026-10-23 | Evaluate topics on imprint text or re-fetched homepages? | A: re-fetch homepages of the 1,000 gold hosts | — |
| D10-journal-venue | 2026-10-23 | Target journal? | Scientific Data, Data Descriptor (example s41597-026-07945-2) | — |
| D8-gold-set-extension | 2026-10-23 | Extend the 1,000-item gold set or re-do it? | A, superseded 2026-10-23: user wants a new diversity-stratified gold set (see D14) | — |
| D9-geocoding-ground-truth | 2026-10-23 | What counts as ground truth for geocoding eval? | A: automatic consistency on all + manual check of 100 | — |
| A1-env-and-models | 2026-10-23 | Create .env; tell which open models innkube/Slurm can serve | Done: .env has INNKUBE_API_KEY; innkube serves qwen38-27b, gemma4-31b-it, qwen-agentworld-35b-a3b, soofi-s-isar-preview (no Qwen3-Next any more) | — |
| A2-original-paper-and-snapshot | 2026-10-23 | Share original paper/venue/reviews and location of the old results | Partly: paper = WebSci Companion '26 demo (arXiv 2609.03971, 5 pp., no eval numbers); this machine is the crawl VM; old results no longer exist (paper figures cannot be recomputed; new snapshot replaces them) | — |
| D7-gold-set-provenance | 2026-10-23 | How was the gold set made? | Human-annotated; can extend; quality not guaranteed, may be redone entirely | — |
| D6-snapshot-growth-source | 2026-10-23 | Where does the larger snapshot come from? | Better fetch yield + link expansion | — |
| D5-topic-eval-granularity | 2026-10-23 | How to score topics vs. 11-class gold? | Map predicted category to top-level ancestor, translate, macro-F1 | — |
| D4-extension-contributions | 2026-10-23 | What does the journal extension add? | Model comparison; error analysis + geocoding eval | — |
| D3-tooling-scope | 2026-10-23 | How much to modernize tooling? | Minimal fixes (keep Poetry); modernize only where necessary | — |
| D2-llm-access | 2026-10-23 | Which LLMs may we use? | Uni Passau cluster, paid APIs (within $20/run, $30/day), FAITH Slurm cluster for own GPUs | — |
| D1-revision-driver | 2026-10-23 | Why revise now? | Journal extension with better evaluation + fresh (larger) data snapshot; no hard deadline | — |

## Lead actions
- 2026-10-26: User: the collector pulls all VM outputs back to lorbeer, later. LLM extraction of the snapshot only after a gold-set model comparison picks one model for addresses and topics (crosses modules: the comparison needs the gold labels).
- 2026-10-28: D25 option B prepared: scripts/E19/reshard.py + merge_report.py takes repeated --recovery-dir (branch e19-reshard-d25, cherry-picked; 193 tests). Dry run on apfel (read-only, /tmp/e19dry): total 55,887, done 22,890, remaining 32,997, shards 8,083/8,325/8,314/8,275. Use: stop pid 133338 first, run reshard, one empty OUT dir per VM, merge with round1 dir listed first.
- 2026-10-26: E22-link-frontier-round1 merged (scripts/E22/frontier.py; 189 tests pass; isort/black not installed on the VMs, so not run). 745,075 new hosts from 1.62M fetched (0.459/host); frontier count and sha256 rechecked on aspe. Results in status.md.
- 2026-10-26: Data-collection lead took over on lorbeer; checked E16/E19/E20 on aspe and apfel (numbers in In flight).
- 2026-10-26: E21-gold-prefill: tool redesign + suggestions (4f71ad3); prefill.jsonl for 1,000 hosts on lorbeer (2 malformed answers left, rule part only). Spot-check 34/40 main address right (results/E21/spotcheck.md). Post-filter e21-v1+filter1 (no model calls; backup prefill.v1.jsonl): rows 1254→950 (duplicate 210, no_postcode 55, third_party 39 non-main roles only); main address gone on 11 hosts (town-only rows). D24 B: `--prefill all` default.
- 2026-10-26: Gold captures copied aspe -> lorbeer datasets/gold (2.3 GB, 993 dirs, 7,288 files, same count as aspe); labelling runs on lorbeer from now on (tool checked: GET / 200, no labels written). aspe copy kept as backup; labels/ lives on lorbeer only.
- 2026-10-26: Labelling overview for the user (readiness, process, workload, tool start routes, fields, D21 table, capture issues, choices): https://claude.ai/artifact/Bqw8VuFHSVDfJR8tECr1tv. Checked: tool starts on aspe with system python3 (stdlib only), GET / 200, no labels written yet. Open before start: D21, names for L1/L2/L3, access route (tunnel to aspe vs copy), calibration meeting date.
- 2026-10-26: E17 Strato gold capture closed: 38 of 48 on aspe datasets/gold (26 landing+imprint: 5 from apfel, 21 from akazie; 12 landing_only, best of two akazie attempts; 990 capture dirs, recounted from meta.json). 10 failed (connection refused/unreachable on every try; Strato throttles each IP after a few dozen requests: apfel 503s, akazie refusals on the 3rd pass): koenigssalz.de, planwerk-a.de, skf-lippstadt.de, wolfram-chemie.com, www.eb-labenwolf.de, www.hwm-werkzeugbau.de, www.mitherzundohr.de, www.stephanusschule.de, www.wsv-bruehl.de, jennyhughes-design.de. Treated like the 49 E17 failures. akazie keeps .venv-render (py3.10, pillow 12.3.0, system libs) and attempts in datasets/gold, gold_try2_prev.
- 2026-10-26: Fixed src/ic/utils/model_run_service.py `Literal[*TOPICS]` (Python 3.11+ syntax; `ic` failed to import on the 3.10 VMs akazie/aralie/abelie) -> `Literal[tuple(TOPICS)]`; 186 tests pass on 3.10 (abelie) and 3.12 (apfel), 793 topics in the literal.
- 2026-10-26: E19 pilot done (1,000 hosts from apfel, report results/E19/pilot_report.tsv on aspe, recounted from the TSV): 148 imprint found (14.8%) + 53 reachable without imprint; imprint found by cause: throttle 54.1%, timeout 10.3%, conn 8.8%, 403 0.6% (3/525). Strato /24 hosts in the sample: 11 of 23 reachable from apfel. Assumed: recovery rounds skip 403 (0.6% yield, half the list); round 1 started.
- 2026-10-26: Took over on lorbeer from HANDOFF.md (deleted). apfel: cloned lead-record, venv, 186 tests pass, seed file copied (sha256 equal), E16 157-262 started; aspe re-planned to 52-156. Fixed scripts/E19/run.sh: end batch "-1" was parsed by click as an option (run exited at once); now computes the last batch. Added scripts/E16/rss_log.sh. E19 pilot started on apfel.
- 2026-10-26: Session ends on aspe; HANDOFF.md written for the new lead VM (code fetch over ssh, data locations, E16 split plan 52-262 over 5 VMs). E16 at 50/263 batches.
- 2026-10-25: Merged E20-fetch-memory-leak (186 tests pass). Cause: requests_get_with_timeout abandoned its request thread on timeout, and endless bodies (streams) kept downloading into memory across batches; fix reads with stream=True and stops at the next 10 KiB chunk. Test set 3x1,000 hosts: RSS 637->1901 MB before vs 644->1061 MB after, traced flat 50 MB. Not fixed: tqdm overcount (cosmetic).
- 2026-10-25: Merged E19-crawl-recovery-pass tooling (scripts/E19/); lead recount matches: 41,516 retryable of 525,000 hosts (batches 0-20, 7.9%: 403 21.3k, timeout 8.7k, 429/503 8.4k, conn 3.1k) + 48 Strato gold -> datasets/E19/recovery_all.txt. Many 403/429 on Cloudflare (bot challenge, may not recover from a new IP): pilot ~1,000 hosts first. Run waits on A5.
- 2026-10-25: E16 memory leak ~2.5 GB per batch in one fetch process (25.5 GB RSS at batch 19, swap full, OOM risk to the Owler service). Stopped and restarted from 19 with 3 batches per process; resume kept 9,455 done hosts of batch 19. Root cause not fixed yet.
- 2026-10-24: Merged E17-gold-capture (153fce2), 166 tests pass; recounted meta.json: 620 landing+imprint, 283 landing only, 49 failed, 48 Strato deferred. Known gaps: 8 pages with a persisting cookie banner, 10 click-found imprints may lack imprint text in the PNG (check DOM), 49 failed not retried (--retry-failed).
- 2026-10-24: Crawl-speed check on E16 batches 0-7: limiter is not the brake (IONOS ~2.7, Strato ~2.0 req/s vs cap 4; 1.4% hosts throttled); 64 workers x 7.2 s/host mean; ~18% of batch time is the tail; host_not_found 18.8% of hosts, of which retryable (403/429/503/timeout/conn/refused) ~15.2k = 7.6% of all hosts. clamd CPU is the Owler service's, not ours; left alone.
- 2026-10-24: merged E18 fix round (3ba4641): first address main by default, rejected save shows message; scripts/gold/e18_browser_check.py 22/22 PASS three runs (lead fixed relative --gold path). Labelling tool ready once D21 answered.
- 2026-10-24: merged E18 (91f44b9 -> baa795e; 155 tests). Assignment checked: L1 520 primary + 80 second + 50 calibration = 650, L2/L3 215+60+50 = 325; 950 items one primary, 50 calibration labelled by all three (consensus = gold); 200 second labels on other labeller. Calibration counted within the 2:1:1 loads.
- 2026-10-24: Assumed for D15 with three labellers: each item has one primary labeller, load split 2:1:1 across the 1,200 labels (1,000 primary + 200 second; about 600/300/300), second labels spread over all three pairs; calibration 50 items labelled by all three. No WARC in E17 (design doc says optional).
- 2026-10-24: merged E12-gold-screening (5d9490f): 10,000 screened, 1,000-item gold sample drawn (core 700 + oversample 300, T=30, seed 20261025) -> datasets/E12/gold_sample.jsonl; verified tests, counts, weight sum 6,555,096. Assumed (design doc §7): full frame incl. 201 not-live core items; LLM operator type for stratification only; WARCs internal. Strato block -> capture gold sites from another IP.
- 2026-10-24 E15 (cap 8, 25k fresh seeds) finished in 59 min; block rates at Strato/IONOS within noise of cap 4 -> D18 B, started E16 seed crawl.
- 2026-10-24 E14 merged; round 2/3 reachable and found counts checked against output (10,548/424, 7,965/134).
- 2026-10-24 E13 merged, 115 tests pass, 100,000 status rows and Strato 6,433 hosts (5,233 found) checked. Assumed: full crawl runs in ranges of ~10 batches per process (memory grows ~0.5 GB/h).
- 2026-10-23 E11 merged: E4 fetcher keyed landing links by URL path (fe4963b), losing external hosts; E9 count (34,771 unique) verified and is the right basis, E10 estimate and D16 stand.
- 2026-10-23 E8 merged, tests pass, prevalences re-counted from results/E8/pilot_features.jsonl. Assumed per design doc §7: full seed-list frame with negatives capped; LLM operator type for stratification only; WARC kept internal, not published; image-only quota 20; gold capture from a second IP with retries.
- 2026-10-23 E10 merged, 80 tests pass, 1,231/9,182 found verified from output.
- 2026-10-23 E9 merged, 80 tests pass, yield 10,246/16,129 and 49/50 precision verified from files. E8 hit an API rate limit and was resumed.
- 2026-10-23 E6 merged (8e35e07), 65 tests pass, yield 10,327/16,093 verified from output.
- 2026-10-23 E7 merged (741c7a8), 35 tests pass, Qwen street-level 0.982 checked in metrics.json.
- 2026-10-23 Checked: innkube gemma4-31b-it and qwen38-27b both accept image input (transcribed a synthetic address PNG correctly). Screenshot path stays an edge case per user; size decided after E8 prevalence.
- 2026-10-23 User: new diversity-stratified gold set may replace the old one (D8 superseded); A4 done; A3 dropped; D13 B.
- 2026-10-23 Venue research done: docs/venue_scientific_data.md (verified licence and personal-data policy quotes). Assumed: deposit on Zenodo under CC BY, code via GitHub + Zenodo DOI; model comparison goes into Technical Validation.
- 2026-10-23 D10/D11/D12 answered; annotation guideline: Town copied as written. A2: old results gone, paper's address count cannot be recomputed.
- 2026-10-23 Assumed: implement E5 static-rule fixes F1-F6, F9 under D6 (no card); F7 landing-page-as-imprint and F8 Kontakt-as-imprint left out (change what counts as an imprint). Assumed: fix stats.py/merge.py empty-address count (bug fix).
- 2026-10-23 E5 done, verified (counts match JSONL; dasekg.de base href and terontec.de query link confirmed live).
- 2026-10-23 E4 random 20k done (results in status.md); data in datasets/E4/.
- 2026-10-23 E2 done (see status.md). Created docs/status.md.
- 2026-10-23 Merged e1-eval-harness (oracle 100%; 28 tests pass after fixing duplicate dev-deps table). Added Qwen3.8-27B/Gemma4-31B to config with per-model extra_body; Qwen3.8 needs reasoning_effort=none (else 6/20 topic calls hit the 2,000-token limit). Note: scoring treats all-blank addresses as failed; must change to a valid 'no address' answer once D8 negatives exist.
- 2026-10-23 Merged d3-minimal-fixes (17 smoke tests pass; vllm optional; python <3.13; README paths fixed; CLAUDE.md added).
- 2026-10-23 Appended MODEL_API_ENDPOINT/MODEL_API_KEY (interpolates INNKUBE_API_KEY)/GEOCODING_API_ENDPOINT to .env; local Photon on :2322 answers.
- 2026-10-23 Paper finding: 3,226,331 imprints -> 3,225,347 'extracted addresses' (99.97%); Address schema has only required fields, so the LLM cannot answer 'no address' -> precision unknown. Probe (gemma4-31b-it, qwen38-27b, one address-free imprint): both return all-empty fields, so no forced hallucination in the clear case; CONFIRMED src/ic/cli/stats.py:126 counts every record with an 'address' key, incl. all-empty ones -> paper's 3,225,347 'extracted address' counts responses, not addresses; recompute from old results (needs A2 path).
- 2026-10-23 Drafted docs/annotation_guideline.md v0.1 for D8 (awaits user review).
- 2026-10-23 Gold audit: 987/1000 items have all address fields verbatim in text; all 1000 have exactly one address, 999 'Deutschland'; no negatives, no multi-address, no AT/CH.
- 2026-10-23 Orientation: found gold standard unused by code; gold topic labels (11 English top-level) differ from model label space (796 German categories); gold has no empty-address cases; deps/README drift.
