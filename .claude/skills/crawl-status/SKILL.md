---
name: crawl-status
description: Crawl status across all crawl VMs (E16/E19/E22 hosts and imprints per crawl dir, running fetches with ETA, memory, disk, errors). Use when asked for the crawl status or progress, before a brief that reports running crawls, or before starting a crawl on a VM.
---

# Crawl status

Read-only. The scripts only read files and `/proc`; they never start, stop or change a crawl.

## Steps

1. Run from the repository root:
   `bash .claude/skills/crawl-status/run_all.sh "$CLAUDE_JOB_DIR/tmp/crawl-status"` (any output dir works; without one a mktemp dir is used).
   It checks every VM in `vms.tsv` in parallel over ssh (locally for this host) and prints tagged, tab-separated lines (format in the header of `check_vm.sh`), then `TOTAL` per crawl dir.
   Done when every VM in `vms.tsv` has a `VM` line or an `UNREACHABLE` line.
2. Compare with `## In flight` in `docs/decisions.md`: list size and batch ranges per experiment, which VM runs which batches, the expected end.
3. Report one block per experiment (E16, E19 shards, E22 rounds):
   - hosts done vs list size, and `imprint_found` (TOTAL line; dirs hold disjoint batch ranges, so sums are exact);
   - each running fetch: VM, batches, tqdm progress and its ETA;
   - stalls: a crawl dir whose `last_write_age_min` is over 60 while a fetch for it runs, or a driver whose last line is not "all done" and no fetch runs;
   - idle VMs (no FETCH line) as capacity for the next unit of work.
4. Flag: `UNREACHABLE` VMs, memory available < 2 GB, disk use > 90 %, every `ERROR` line (open the log with `grep -n -A5 Traceback`).
5. Update the record's `## In flight` lines for the data-collection module when the state changed (finished, stalled, moved).

## Reference

- `vms.tsv`: VM name and repo checkout (relative to `~`). Add a line when a VM joins the crawl.
- `SKIP` (env var, extended regex on the crawl dir) hides finished test crawls; default skips E0-E15 and `pilot` dirs.
- Hosts are counted by the `ic fetch` resume rule: the last complete 9-column row per host is final.
- The tqdm ETA reflects the recent rate; the tail of a batch is slow (retries of deferred hosts), so ETA can rise.
