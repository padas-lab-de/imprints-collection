# E53 phase-1 screen: run status

Started 2026-11-12T13:12Z (UTC), detached (`setsid nohup`), innkube only, 6 runs x 4 concurrent calls.

- Process group (PGID) / driver PID: **521215** (`bash .../datasets/E53/runtime/scripts/E53/screen_run.sh 0 4`).
  Stop all six runs: `kill -- -521215`. Resume: start the same command again (append jsonl, done hosts are skipped).
- Code: a copy of the tree at b5db9a4 + the E53 scripts, in `datasets/E53/runtime/` (the run does not depend on
  the worktree). Command:
  `setsid nohup bash /home/dinzinger/GitLab/fim/imprints-collection/datasets/E53/runtime/scripts/E53/screen_run.sh 0 4 > /home/dinzinger/GitLab/fim/imprints-collection/datasets/E53/screen/logs/driver.out 2>&1 < /dev/null &`
- Input: `datasets/E53/screen/inputs.jsonl` (19,998 of the 20,000 S1 sites; 2 not found in the release package).
- Output: `datasets/E53/screen/preds/{poi3,wz,address}/<tag>.jsonl`; logs `datasets/E53/screen/logs/<run>.log`
  (each ends with a JSON summary line and `<run> exit <code>`), `driver.log` gets `all runs finished`.
- Expected end: about 2026-11-13T03:00Z (slowest run qwen POI r-low, 2.5 s per site at 4 workers in the pilot;
  the other five runs end after about 2-7.5 h).

Check progress:

    wc -l /home/dinzinger/GitLab/fim/imprints-collection/datasets/E53/screen/preds/*/*.jsonl
    grep -h "exit\|Traceback" /home/dinzinger/GitLab/fim/imprints-collection/datasets/E53/screen/logs/*.log
    ps -o pid,etime,args -g 521215

After the end (or for a partial table at any time), from the repository root:

    python3 -I scripts/E53/features.py
    python3 -I scripts/E53/coverage.py            # add --partial while the screen still runs

## Pilot (first 200 S1 sites, 2026-11-12T12:57-13:06Z, 4 workers per run, 6 runs in parallel)

| run (tag) | errors | truncated | wall s | s/site (latency) | tokens in / out per site |
|---|---:|---:|---:|---:|---:|
| POI gemma `retrieve__gemma__r-short` | 0 | 0 | 208 | 4.13 | 2,591 / 61 |
| POI qwen `retrieve__qwen__r-low` | 0 | 0 | 499 | 9.93 | 2,524 / 454 |
| WZ gemma `retrieve__gemma__r-none__c1500` | 0 | 0 | 272 | 5.43 | 3,132 / 29 |
| WZ qwen `retrieve__qwen__r-none__c1500` | 0 | 0 | 224 | 4.47 | 3,047 / 25 |
| address gemma `address__gemma__r-none__f-schema__mode-main` | 0 | 0 | 92 | 1.83 | 944 / 51 |
| address qwen `address__qwen__r-none__f-schema__mode-main` | 0 | 0 | 88 | 1.74 | 895 / 67 |

Total wall time 8.4 min (includes building the node embeddings into the new cache `datasets/E53/cache`).
No main topic (null) in 8/9 (POI gemma/qwen) and 5/8 (WZ) of 200 sites; main address found by each model in
187/200.
