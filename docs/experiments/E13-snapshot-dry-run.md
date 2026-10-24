# E13: Per-provider limit, resume, and a 100k dry run of the E9 fetcher

Date: 2026-10-23/24. Branch `E13-snapshot-dry-run` (from `lead-record` 693ddfa). Goal: make `ic fetch` ready for the full 6.56M seed list on the crawl VM (16 cores, 31 GB RAM), then test it on 100,000 random seeds.

## Result in short

- **Limiter.** Hosts are grouped by the /24 (IPv4) or /48 (IPv6) network they resolve to. Each group gets at most 4 concurrent requests, at least 0.25 s between request starts, and a 10 s cooldown after a 429/503. A host that gets a 429/503 is retried once, as a whole, after max(Retry-After, 60 s). All of these are CLI options. Fetch behaviour is otherwise unchanged.
- **Resume.** Each batch has a status log with one line per finished host. A restart skips logged hosts and cuts the output gzip back to the records of logged hosts. Tested with `kill -9` mid-batch: no duplicates, no lost hosts, and the gzip reads cleanly.
- **100k dry run.** 100,000 hosts took 283 min, about 353 hosts/min overall and about 490/min in steady state. Found/reachable is 62.5% overall and 85.0% for .de (E9: 63.5% and 83.6%).
  - Strato (81.169.145/24): 24 of 6,433 hosts ended with a 503 (0.4%). In E8, nearly all of the ~80 Strato sample hosts answered 503.
- **Full run (6.56M) at the defaults:**
  - **Wall time:** about 12–13 days. The Strato and IONOS groups at 4 concurrent set the pace. With all limits removed the steady rate would give about 9.3 days, so the limit costs about 28% throughput here.
  - **Disk:** about 33 GB (66 GB free).
  - **Memory:** RSS grows about 0.5 GB/h (see open doubts), so the run has to be split into processes of about 10 batches.
- Tests: 115 pass (98 before; 17 new in `tests/test_fetch_politeness.py`).

## 1. Per-provider limit

### Grouping

Where a host is hosted is read from its resolved address. The key is the /24 network for IPv4 and the /48 for IPv6 (`ic.utils.politeness.network_key`); IPv4 is preferred when a host has both. Reasons:

- **Shared hosting concentrates on few /24s.** In a 3,000-seed DNS sample, IONOS 217.160.0/24 held 9.3% of resolved hosts and Strato 81.169.145/24 held 6.6%. These are the groups that have to be throttled. E5 and E8 saw the Strato 503s on exactly 81.169.145.x.
- **ASN grouping was rejected.** It would throttle a CDN such as Cloudflare (AS13335) as one group, although its front ends are many independent edges. It also needs an external ASN table. A /24 also matches how hosters rate-limit (per front-end cluster).
- **Per-IP grouping is too fine.** Many hosters spread load across a /24.
- **Resolution cost.** It is one `getaddrinfo` per host, cached. A host that does not resolve goes to the group `dns` and is not requested at all; the outcome is the same as before, it just fails faster. A temporary resolver error falls back to "no group" (unlimited) and is not cached.

In the dry run, 100k hosts fell into 21,127 groups. The largest groups:

| Group | Provider | Hosts | Reachable | Found | Hosts with 429/503 | Ended 429/503 |
|---|---|---|---|---|---|---|
| 217.160.0/24 | IONOS | 8,290 | 7,670 | 6,716 | 53 | 43 |
| 81.169.145/24 | Strato | 6,433 | 6,042 | 5,233 | 30 | 28 (24 of them 503) |
| 188.114.97/24, .96/24 | Cloudflare | 2,374 | 1,866 | 497 | 14 | 14 |
| 162.159.143/24 | Cloudflare | 1,147 | 706 | 463 | 481 | 344 |
| 172.66.3/24 | Cloudflare | 1,128 | 751 | 487 | 435 | 296 |
| 23.227.38/24 | Shopify | 1,063 | 985 | 545 | 0 | 0 |

### Mechanism (`src/ic/utils/politeness.py`, `src/ic/cli/fetch.py`)

- **`ProviderLimiter`** wraps every GET (`_limited_get`) in a slot of the host's group. It enforces:
  - at most `--provider-concurrency` requests in flight per group;
  - `--provider-delay` seconds between request starts in a group;
  - after a 429/503, a pause of `--provider-cooldown` seconds for the whole group.
- **`HostScheduler`** sits in front of the 64 worker threads and admits at most as many *hosts* per group as the request cap. Without it, 64 workers could all wait on one IONOS slot while other groups sat idle. Hosts of a full group are parked in a per-group queue, so workers keep fetching other groups.
- **One retry for 429/503.** On the first attempt, a 429/503 on any request of a host raises `RetryLater`. The host is put on a delay heap and fetched again from the start after max(Retry-After, `--retry-backoff`), capped at 600 s. On the second attempt the old E9 behaviour applies: one inline 1 s retry for 5xx; a 429 fails.
- **Off switch.** `--provider-concurrency 0` turns the limiter off; this is the E9 behaviour except for the dns shortcut and the status log.
- **New CLI options:** `--output-dir`, `--provider-concurrency 4`, `--provider-delay 0.25`, `--provider-cooldown 10`, `--retry-backoff 60`, `--progress-interval 60`. The positional arguments are unchanged.

## 2. Readiness for 6.56M seeds

- **Resume** (`src/ic/utils/fetch_state.py`). After its output record is written and flushed, each finished host gets a line in `fetch_status_batchNNNNNN.tsv`. The columns are host, status, detail (landing error per scheme), provider group, attempts, requests, throttled, seconds and end time. On restart:
  - a batch whose hosts are all logged is skipped;
  - otherwise the output gzip is read with a tolerant reader that stops at a cut-off end, rewritten to keep only the records of logged hosts, and appended to as a new gzip member;
  - a cut-off last status line is ignored.

  Batch membership is the same on every run (shuffle with `random.seed(42)`). The input file may be `.gz`, so the seed list can be passed as `seed_hosts.txt.gz` directly.
- **Logging.** Every `--progress-interval` seconds the log gets one line with:
  - done/total and the rate;
  - status counts;
  - the scheduler queue (running, parked, delayed);
  - limiter requests, throttles and wait time;
  - the top groups.

  tqdm writes at most once a minute. The 4.7 h run wrote a 197 KB log, about 13 MB for 6.56M hosts.
- **Output size, memory:** see section 4.

## 3. Dry run on 100k seeds

- **Sample** (`scripts/E13/sample.py`): 100,000 hosts drawn with `random.seed(20261024)` from the 6,560,119 unique seeds minus the E4/E9 random 20k (pool 6,540,119). Written to `datasets/E13/random100k_seed_hosts.txt`.
- **Run** (`scripts/E13/run.sh`):
  - command: `ic fetch datasets/E13/random100k_seed_hosts.txt 25000 --output-dir datasets/E13/random100k`;
  - defaults: 64 workers, cap 4, delay 0.25 s;
  - started under nohup; log `results/E13/logs/fetch.log`;
  - resources sampled every 30 s by `scripts/E13/monitor.sh` into `results/E13/logs/resources.tsv`.
- **Analysis:** `scripts/E13/analyze.py` and `scripts/E13/capacity.py` produced `results/E13/analysis.txt` and `results/E13/capacity.txt` (untracked).
- **Concurrent load.** The run started 2026-10-23 20:46 UTC and finished 2026-10-24 01:28 UTC. Other jobs ran on the same VM and the same outgoing IP at the same time: E12 (gold screening of 10k hosts), E14 (link-expansion rounds 2–3), three `owler-fetchd` processes and `collect-travel-agencies`. The median load was 29 on 16 cores. Throughput on a quiet VM may be higher. The provider limits apply per process, so a Strato or IONOS server saw the sum of all these crawlers.

### Throughput

| Batch (25k hosts) | Wall time | 95% of hosts done after |
|---|---|---|
| 0 | 74.6 min | 48.6 min |
| 1 | 72.5 min | 47.8 min |
| 2 | 68.0 min | 49.2 min |
| 3 | 67.5 min | 51.0 min |
| All | 283 min (353 hosts/min) | |

Hosts finished per 10-minute window (hosts/min) repeat the same pattern in every batch:

- about 470–500/min while the batch runs;
- then a 20–25 min tail at 5–80/min.

The **tail** is the Strato and IONOS queues: the last 5% of every batch is 97–99% hosts of those two groups. At 4 hosts in flight:

| Group | Seconds per host | Requests per host | Capacity | Arrival in steady state |
|---|---|---|---|---|
| IONOS | 7.16 | 4.45 | 34 hosts/min (2.5 req/s) | 8.3% of 490/min = 41/min |
| Strato | 9.80 | 4.40 | 24 hosts/min (1.8 req/s) | 6.4% of 490/min = 31/min |

Both groups fall behind during a batch and are drained at the end.

All hosts: 4.24 requests per host on average (4.75 for reachable hosts); 7.6 s per host on average, median 6.4 s, p99 31 s.

### Yield

| Status | Hosts |
|---|---|
| imprint_found | 50,289 |
| imprint_not_found | 30,141 |
| host_not_found | 18,640 |
| no_valid_html_tree | 583 |
| filtered | 347 |

| Set | Found / reachable | E9 (random 20k) |
|---|---|---|
| All | 50,289 / 80,430 = 62.5% | 63.5% |
| .de | 36,895 / 43,420 = 85.0% | 83.6% |
| .at | 89.5% | |
| .ch | 81.2% | |
| .eu | 73.7% | |
| .net | 43.6% | |
| .com | 32.5% | |
| .org | 17.7% | |

- "Reachable" is found + not_found, i.e. the hosts that wrote an output record (80,430 records; no duplicate status lines).
- The yield matches E9 within sampling noise on a 5x larger, disjoint sample. The limiter did not cost yield.

### Error mix (host_not_found, 18.6% of all hosts, by landing error)

| Cause | % of all hosts |
|---|---|
| dns (does not resolve) | 5.71 |
| HTTP 403 | 4.14 |
| HTTP 404 | 1.46 |
| timeout | 1.34 |
| other 4xx | 1.32 |
| ssl | 1.06 |
| 5xx except 503 | 0.78 |
| HTTP 429 | 0.78 |
| 2xx without usable page | 0.67 |
| HTTP 503 | 0.55 |
| connection error | 0.25 |
| refused | 0.22 |
| rest (empty, redirects, binary, odd codes) | 0.35 |

### 429/503

- 1,703 hosts saw at least one 429/503. There were 2,365 later retries, and 996 retried hosts ended reachable.
- 1,325 hosts ended with a 429/503 on the landing page. Most of them are two Cloudflare /24s: 162.159.143 (344) and 172.66.3 (296). They answer 429/503 on the first request with the cooldown untouched, which looks like site-level bot challenges, not load. The limiter cannot fix this and should not slow down for it; see open doubts.
- **Strato vs E8.**
  - E8 (1,000 random seeds, run in parallel with the unthrottled E6 crawl): 80 of the ~80 Strato hosts answered 503, an IP-level block.
  - E13: of 6,433 Strato hosts, 30 saw a 429/503 and 24 ended with a 503 (0.4%); 94% were reachable.
  - IONOS: 43 of 8,290 hosts ended with a 429/503.
  - At 4 concurrent requests and 0.25 s spacing, neither hoster blocked the VM.

### Resources

- CPU of the fetch process: median 792%, p95 1,122%, max 1,445%. The work runs in C extensions (lxml, zlib, ssl) and is not GIL-bound at 64 workers.
- Threads: at most 147. The E9 timeout wrapper leaves an executor thread behind when a request exceeds the total timeout.
- RSS grows steadily over the run. Maximum per 30 min, from 0 min to 270 min: 3,175, 3,494, 3,842, 4,131, 4,216, 4,718, 4,858, 5,165, 5,398 and 5,474 MB. That is about 0.5 GB/h, across batch boundaries, so it is not per-batch state. The cause was not found (open doubts).

### Resume test

To avoid refetching the 100k, the test used a fresh slice:

- **Slice** (`scripts/E13/sample_resume.py`): 3,000 seeds drawn with `random.seed(20261025)`, outside the E4 20k and the E13 100k. Batch size 1,500 (`scripts/E13/run_resume.sh`), output `datasets/E13/resume_test`.
- **Kill.** The run was started under nohup and killed with `kill -9` at 06:39 UTC, 700 hosts into batch 0. At that moment:
  - the output gzip was cut off (plain `gzip` raises `EOFError`);
  - the tolerant reader got 566 records: 565 for logged hosts and 1 for a host whose status line was not yet written.
- **Restart** with the same command logged `Resuming batch 0: 700 hosts done (565 records kept), 800 to go`. The record without a status line was dropped and its host fetched again.
- **Final state** (`scripts/E13/verify_resume.py --strict`, after 07:04 UTC):
  - 3,000 status lines for the 3,000 input hosts: no duplicates, none missing.
  - Both output gzips read cleanly with the plain `gzip` module: 1,212 + 1,214 = 2,426 records, equal to found + not_found in the status logs. There are no duplicate records and no records of unlogged hosts.
  - Found/reachable on the slice is 1,496 / 2,426 = 61.7%.

## 4. Extrapolation to the 6.56M seed list

All figures are measured 100k rates times 65.6.

**Disk.** 100k hosts took 500 MB: outputs 488.7 MB, status logs 7.7 MB, external hosts 4.0 MB. For 6.56M that is about 32 GB of outputs, 0.5 GB of status logs and 0.26 GB of external hosts, about 33 GB in all. 66 GB are free on `/` now, but E12, E14 and the owler crawlers also write there.

**Wall time.**

| Assumption | Rate | Wall time |
|---|---|---|
| Measured effective rate (25k batches, cap 4) | 353 hosts/min | 310 h = 12.9 days |
| Strato bound at cap 4, even with one big queue | 6.4% x 6.56M = 422k hosts at 24/min | 293 h = 12.2 days |
| IONOS bound at cap 4 | 8.3% x 6.56M = 544k hosts at 34/min | 267 h = 11.1 days |
| Steady rate, no provider tail (as if unlimited) | 490 hosts/min | 223 h = 9.3 days |

**Does the limit cost throughput?** Yes, about 28% at the defaults (310 h vs 223 h). The loss is all in the batch tails, where only the Strato and IONOS queues run. Bigger batches do not remove it: at cap 4 the Strato group alone needs 293 h. To get to about 9–10 days:

- raise `--provider-concurrency` to 6–8 and keep `--provider-delay 0.25`, which still caps a group at 4 req/s. Strato at cap 8 would see about 3.6 req/s, twice the rate tested here. It did not block at 1.8 req/s, but E8 shows it does block at some rate. Watch the progress log's `throttled` count for 81.169.145 and lower the cap if it climbs.
- Alternatively, raise the cap only for named groups (a small code change; not done).

**Memory.** At +0.5 GB/h, one process over 300 h would reach about 150 GB. The run must be split. Run `ic fetch` with `--start-batch/--end-batch` over about 10 batches (250k hosts, about 12 h, about 9 GB peak) per process, then start the next range. Resume makes a restart cheap, so a cron job or loop script is enough. Running two processes on disjoint batch ranges would also work, but the per-group limits would then double (halve `--provider-concurrency`).

**Recommended command for the full run.** Run from the repository root:

```
ic fetch seed_hosts.txt.gz 25000 <start> <end> --output-dir datasets/snapshot --provider-concurrency 6
```

- 263 batches of 25k in total.
- Repeat over ranges of 10 batches.

## Open doubts

1. **RSS growth (0.5 GB/h).** The cause was not isolated.
   - Candidates: glibc arena fragmentation from the many short-lived executor threads in `requests_get_with_timeout` (unchanged E9 code), or leaked threads stuck in a request.
   - The limiter's own state is small: a host-to-group cache cleared at 500k entries and stats for about 21k groups.
   - Cheap things to try: `MALLOC_ARENA_MAX=2`, or a shared executor instead of one per request.
   - Until then, restart every about 10 batches.
2. **No A/B with the limit off.** The "28% cost" compares against the steady rate of the same run, not against a run with `--provider-concurrency 0`. Without the limit, Strato and IONOS might block the VM, as in E8, and lose yield instead of time.
3. **Cloudflare 429/503 (about 640 hosts, 0.6%) are not load-related.** They look like bot challenges on 162.159.143/24 and 172.66.3/24. Each such host costs a deferred retry, and its 429/503 also puts the whole /24 into a 10 s cooldown, which slows the other hosts there. For the full run, it may be worth not cooling down a group whose 429/503 come on the first request.
4. **Shared VM.** Throughput was measured with E12, E14, three owler-fetchd and collect-travel-agencies running. A quiet VM may be faster. The hosters see the sum of all crawlers from this IP, which the per-process limiter does not know about.
5. **DNS is resolved twice per host** (once for the group key, once by requests). The resolver cache usually absorbs this. A DNS outage would make all hosts "unlimited" for that time, not fail them.
