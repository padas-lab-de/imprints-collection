# E53 step 5: same-day ic fetch and gold capture (2026-11-13)

Input: `datasets/E53/phase2/gold_sample.jsonl`, 1,869 items, sha256 `fc6d45a89355f48629cf1cbb7b590475443e0c6e124f695c14c07df9e453322e`
(host list `hosts.txt` sha256 `2f4ecd63…`). No paid API calls in this step.

## Runs

| | ic fetch | capture |
|---|---|---|
| VM / IP group | aralie | akazie |
| checkout | `~/GitHub/imprints-collection-e53`, tree **collection-release 88b162a** (release fetcher) | `~/GitHub/imprints-collection-e53`, tree a384a19 (this branch), `.venv-render` (Playwright 1.64.1, Chromium 156.0.8078.4) |
| driver | `scripts/E53/fetch_run.sh` (driver PGID 304873, python PID 305003) | `run_capture.sh` -> `scripts/E53/capture.py` (PID 25527) |
| start / end UTC | 09:21:42Z – 09:31:34Z (records 09:21:49Z – 09:31:34Z) | 09:25:41Z – 11:33:07Z; `--retry-failed` once 11:40:03Z – 11:41:34Z |
| logs (copied to `datasets/E53/`) | `fetch_aralie/fetch_driver.log`, `fetch_main.log`, `fetch_shopify.log` | `capture_logs/capture.log`, `capture_retry.log` |

Commands:

```
# aralie (release settings E22 + Shopify D59)
ic fetch hosts.txt 25000 0 0 64 --provider-concurrency 8 --skip-provider-group v4:23.227.38 --output-dir datasets/E53/fetch/main
ic fetch shopify_hosts.txt 25000 0 0 4 --provider-concurrency 1 --provider-delay 5 \
    --provider-cooldown 5 --retry-backoff 300 --output-dir datasets/E53/fetch/shopify   # 10 hosts
# akazie
python scripts/E53/capture.py --sample datasets/E53/phase2/gold_sample.jsonl --out datasets/E53/gold --ip-group akazie --workers 6
python scripts/E53/capture.py ... --retry-failed      # once, 10 items
# lorbeer (local, after rsync)
python3 -I scripts/E53/merge_fetch.py --sample datasets/E53/phase2/gold_sample.jsonl --gold datasets/E53/gold \
    --fetch-dir datasets/E53/fetch_aralie/main --fetch-dir datasets/E53/fetch_aralie/shopify \
    --fetch-vm aralie --fetch-tree 88b162a --summary datasets/E53/step5_summary.json
```

Output: `datasets/E53/gold/<host>/` = `ic_fetch.jsonl` (last ic fetch record + fetch_status/detail/fetched_at/fetch_vm;
stub line if no record) + capture files + `meta.json` (`ic_fetch` block with timestamps, `input_day_mismatch`).

## Counts (source: `datasets/E53/step5_summary.json`)

| | all (1,869) | Strato 81.169.145.0/24 (156) | other (1,713) |
|---|---|---|---|
| ic fetch imprint found | 1,816 | 156 | 1,660 |
| ic fetch no imprint | 18 | 0 | 18 |
| ic fetch failed | 35 (host_not_found 32, filtered 3) | 0 | 35 |
| capture landing+imprint | 1,703 | 50 | 1,653 |
| capture landing only | 157 | 106 | 51 |
| capture failed | 9 | 0 | 9 |

- Capture failed after the retry (10 -> 9): no_dns 6 and ReadTimeout 1 (all 7 also host_not_found in ic fetch); ConnectTimeout 2 (ic fetch found an imprint).
- input_day_mismatch (capture day != ic fetch day): **0**. All runs were on 2026-11-13.
- Cookie banner actions (`meta.json` `consent_banner`):
  - landing: none 1,430, rejected 405, clicked_banner_persisted 8;
  - imprint: none 1,659, rejected 37, clicked_banner_persisted 6.
- Manifest: `datasets/E53/gold/manifest.sha256`, 17,935 files, sha256 **`f0bb63e57b4f935be81b22df4760fe515bc4d969eb197a5a00734057da7c7c96`**.

## Prefill dry run (no paid call)

`prefill.py --dry-run --ic-fetch-dir datasets/E53/gold --out-dir datasets/E53/gold`:
`1869 items to do (53 without imprint text)`; the estimate is **$0.5344 for 1,816 calls** (4,254,615 in / 217,920 out tokens), worst case $1.3335.
The ledger shows E53-prefill $0.0066 of $10.00 spent so far.
The adapter reads all 1,869 items. The 53 without imprint text are 18 no_imprint and 35 failed.

## Notes and doubts

- **UA difference.**
  - ic fetch runs the release fetcher 88b162a with the D39 B bot UA `Mozilla/5.0 (compatible; ImprintsCollectionBot/1.0; +https://www.fim.uni-passau.de/data-science)` and the E35 recall patch.
  - The capture uses the E17 Chrome-like research UA `Mozilla/5.0 (X11; Linux x86_64) … Chrome/126.0 Safari/537.36 (research crawl, Uni Passau imprints project)`.
  - The `fetch.py` on the lead-record branch still has UA `Mozilla/5.0`. It is not the release fetcher and was not used.
- **Strato blocked akazie partway through the capture.**
  - Before 10:59Z: 42 of 47 Strato items were landing+imprint.
  - From 10:59Z: 101 of 109 were landing_only. Most landing pages returned HTTP 503 (static and rendered). The other landing_only Strato items have no render status.
  - aralie's ic fetch got an imprint for all 156 Strato hosts.
  - About 100 Strato items therefore have only a 503 capture. Labellers need either a re-capture from another IP group or later, or the ic fetch text as the source for these items. This step did not use another VM (coordinator instruction).
- **The other 51 landing_only items** are site-side: no imprint link found (about 34, most of them live with HTTP 200), imprint navigation timeout or error (4), and 403/404/410/502 responses.
- **JSONL fix.**
  - The first prefill dry run failed on 37 items. `ic_fetch.jsonl` was written with `ensure_ascii=False`, so U+2028 and U+0085 in page text broke `str.splitlines()` in `prefill.read_ic_fetch`.
  - merge_fetch now writes ASCII-escaped JSON, and `read_ic_fetch` splits on `\n` only.
  - Rerunning the merge gave identical counts and a new manifest sha (above).
  - `prefill.py` writes its own output with `ensure_ascii=False`. Consumers of that file should also split on `\n` only.
