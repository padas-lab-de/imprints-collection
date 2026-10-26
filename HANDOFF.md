# Handoff 2026-10-26: lead moves from crawl VM `aspe` to a new lead VM

Read CLAUDE.md, docs/status.md, docs/decisions.md first; this file only covers the move. Delete it once taken over.

## Get the code (nothing is pushed)
Branch `lead-record` (tip: this commit) exists only on `aspe`. From the new VM:
`git remote add aspe ssh://aspe/home/dinzinger/GitHub/imprints-collection && git fetch aspe && git checkout -b lead-record aspe/lead-record`
(or ask the user to approve a push to origin). All E-branches are merged into lead-record.

## What stays on `aspe` (untracked, not in git)
- datasets/E16/seeds (5.9 GB, growing), datasets/E16/seed_hosts_shuffled.txt (6,560,119 hosts, the batch definition: all VMs must use this same file)
- datasets/gold (2.1 GB: 952 captures, assignment.jsonl; labels/ not started), datasets/E12 (7.1 GB), datasets/E19 (recovery lists, built from batches 0-20)
- .env (INNKUBE_API_KEY), photon geocoder (java, ~/opt/photon, running)
- Venvs inside worktrees, do not remove: `.claude/worktrees/agent-a9795ebab2b1874a2/.venv` (E16 runs with it), `.claude/worktrees/agent-ac37363e2dedffa7e/.venv-render` + `.render-libs` (Playwright, gold capture). The other 13 worktrees are merged and can be cleaned up.

## E16 at handoff
- 50 of 263 batches done (0-48 + part of 49); range 49-51 running since 09:03 UTC, ~58 min per batch, 3 batches per process (scripts/E16/run.sh, STEP=3). Measured ETA on `aspe` alone: ~8.5 days; over 5 VMs ~2 days.
- E20 leak fix is in the code since range 25-27, but the production RSS check (flat over 2+ batches?) was not done: log `ps -o rss= -p <pid>` per batch on one VM before raising STEP to 10. 3.9 GB RSS at 28 min into range 49-51.
- Do not edit scripts/E16/run.sh while a driver runs (bash reads scripts incrementally).

## Spreading E16 over the 5 crawl VMs (D20 A, A5 now possible)
1. Per VM: check its own public IP (A5 card), Python 3.10+, ~30 GB free; clone lead-record, venv (`pip install -e .`), copy seed_hosts_shuffled.txt from `aspe` (same file, same shuffle).
2. On `aspe`, stop the driver at a range boundary: `kill <run.sh pid>` only (the python child finishes its range), then `nohup bash scripts/E16/run.sh 52 93`.
3. Other VMs, e.g.: 94-135, 136-177, 178-219, 220-262 (`PY=.venv/bin/python nohup bash scripts/E16/run.sh FIRST LAST`; run.sh hardcodes ROOT, adjust).
4. Each per-provider limit is per process: per IP the load stays as now, but Strato/IONOS see 5 IPs in total. Watch throttled counts in the first batch on each VM.
5. Collect all fetch_status_batch*.tsv + records into one place after the run.

## Next after the move
- E19-crawl-recovery-pass: pilot ~1,000 of datasets/E19/recovery_all.txt from a VM with another IP (`scripts/E19/run.sh`), then merge_report.py; rebuild the list with collect.py when E16 is done.
- Strato gold hosts: `bash scripts/gold/e17_run.sh --hosts deferred_strato.txt --no-strato-filter` from a non-`aspe` IP (needs the render venv there).
- Open cards: D21-guideline-open-points (recommend A), A5-crawl-vm-access (now unblocked by the user's VMs: close it once IPs are checked).
