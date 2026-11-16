# Reproduce the gold set and the model evaluation

This document lists one command per step, in order. The method is in `docs/gold_set_design.md`, the scoring in `docs/model_eval_protocol.md`, the labelling rules in `docs/annotation_guideline.md` and `docs/annotation_howto.md`.

## Conventions

- Run every command from the repository root. `ic` reads `topics/` and `prompts/` with relative paths.
- Data folder: `$IC_GOLD_DATA`, default `datasets/goldset`. All gold-set steps read and write below it. The evaluation runs use `$EVAL`, default `datasets/evaluation`. Both folders are not part of the repository.
- Scripts that read crawled or captured files run with `python3 -I`.
- Model endpoint and key: `MODEL_API_ENDPOINT`, `MODEL_API_KEY` (environment or `.env`, see `.env.template`). The prefill step uses `OPENROUTER_API_KEY`. Never commit `.env`.
- Machine names (`capture1`, `crawl1`) are free names. They are stored as provenance only.
- Seeds: frame 20261112, phase 2 and assignment 20261113, top-up 20261114. Same seed and same input give the same output.

| Step | Script | Network | Output (below `$IC_GOLD_DATA`) |
|---|---|---|---|
| 1 exclusions | `goldset/exclusions.py` | no | `exclusions/` |
| 2 frame | `goldset/frame.py` | no | `frame/`, `phase1_hosts.txt`, `reports/frame.md` |
| 3 screen | `goldset/screen_inputs.py`, `goldset/screen.sh`, `goldset/screen_features.py` | model endpoint | `screen/` |
| 4 draw | `goldset/draw.py` | no | `phase2/gold_sample.jsonl` |
| 5 top-up draw | `goldset/topup.py draw` | no | `topup_sample.jsonl`, `dropped_final.jsonl`, `topup/` |
| 6 capture | `goldset/fetch.sh`, `goldset/capture.py`, `goldset/merge_fetch.py`, `goldset/recapture_merge.py`, `goldset/topup.py merge` | web | `gold/<host>/` |
| 7 assign | `goldset/assign.py`, `goldset/topup.py assign` | no | `gold/assignment.jsonl` |
| 8 prefill | `goldset/prefill.py` | paid API | `gold/prefill.jsonl`, `gold/prefill_topup.jsonl` |
| 9 labelling | `python3 -m ic.gold.annotate` | local only | `gold/labels/L<n>.jsonl` |
| 10 model runs | `evaluation/build_inputs.py`, `evaluation/run_candidates.sh` | model endpoint | `$EVAL/preds/` |
| 11 scoring | `python3 -m ic.eval` | no | `results/score/<run-id>/` |

## 1. Exclusion lists

Every host used before in a gold, pilot or prompt study is excluded. One `--list` per earlier study:

```console
python3 -I goldset/exclusions.py --list old_gold=evaluation/gold_standard_data.jsonl:url --list NAME=FILE[,FILE...]
```

## 2. Frame and phase-1 sample

`--sites` is the release site list (one canonical host per line, after the parked-site filter; see `docs/reproduce_collection.md`).

```console
python3 -I goldset/frame.py --sites canonical_sites_after_filter.txt --n1 20000 --seed 20261112
```

## 3. Phase-1 screen

Screen inputs from the stored crawl text (read only). `sources.tsv` has the format of `collection/crawl_sources.example.tsv`.

```console
python3 -I goldset/screen_inputs.py --crawl-root CRAWLS --sources sources.tsv --procs 8
bash goldset/screen.sh 0 4
python3 -I goldset/screen_features.py
```

`screen.sh` runs the two screen models (gemma4-31b-it, qwen38-27b) on POI, WZ and address. It is resumable. Run it with `LIMIT` = 20 first as a pilot.

## 4. Phase-2 draw

```console
python3 -I goldset/draw.py
```

Writes `phase2/gold_sample.jsonl` (1,869 items with inclusion probability, weight, strata and fold) and the quota report.

## 5. Top-up from the final release list

```console
python3 -I goldset/topup.py draw --final-sites <final canonical_sites_after_filter.txt> --final-sha256-prefix 93bd4d30
```

Writes `topup_sample.jsonl` (18 items), `dropped_final.jsonl` (0 items) and `topup/hosts.txt`. The top-up items go through step 6 like the main items, then `topup.py merge` (below).

## 6. Same-day fetch and capture

Run both parts for one batch of items on the same UTC day.

Host list of the sample:

```console
python3 -I -c "import json,sys; [print(json.loads(l)['host']) for l in open(sys.argv[1])]" datasets/goldset/phase2/gold_sample.jsonl > datasets/goldset/hosts.txt
```

a. `ic fetch` on the crawl machine, with the release settings (model input):

```console
nohup bash goldset/fetch.sh datasets/goldset/hosts.txt datasets/goldset/fetch > datasets/goldset/fetch_driver.log 2>&1 &
```

b. Browser capture on a different machine (labeller input). It needs Playwright with Chromium in a separate environment (`<venv-render>`):

```console
PYTHONPATH=src <venv-render>/bin/python goldset/capture.py --sample datasets/goldset/phase2/gold_sample.jsonl --out datasets/goldset/gold --ip-group capture1 --workers 6
```

c. Merge the `ic fetch` output into the item folders (copy the fetch folder from the crawl machine first):

```console
python3 -I goldset/merge_fetch.py --sample datasets/goldset/phase2/gold_sample.jsonl --gold datasets/goldset/gold --fetch-dir datasets/goldset/fetch/main --fetch-dir datasets/goldset/fetch/shopify --fetch-vm crawl1 --fetch-tree <git commit of the fetcher>
```

d. Optional re-capture of failed or incomplete captures (run `capture.py` again into `datasets/goldset/recapture`, from another machine if needed), then merge:

```console
python3 -I goldset/recapture_merge.py --sample datasets/goldset/phase2/gold_sample.jsonl --gold datasets/goldset/gold --new datasets/goldset/recapture
```

A second re-capture of the items still without an imprint capture keeps the earlier capture apart and marks the items that stay incomplete (`capture_problem`):

```console
python3 -I goldset/recapture_merge.py --sample datasets/goldset/phase2/gold_sample.jsonl --gold datasets/goldset/gold --new datasets/goldset/recapture2 --archive-name capture_previous2 --only-imprint --hosts H.txt --problem-list datasets/goldset/capture_problem.txt --keep-old-manifest manifest_pre_recapture2.sha256
```

e. Top-up items: fetch and capture `topup/hosts.txt` as in a and b (capture with `--sample datasets/goldset/topup_sample.jsonl --out datasets/goldset/topup/capture`), then:

```console
python3 -I goldset/topup.py merge --capture-dir datasets/goldset/topup/capture --fetch-dir <topup fetch dir> --fetch-vm crawl1 --fetch-tree <git commit of the fetcher>
```

## 7. Labeller assignment

Three labellers L1, L2, L3; load 2:1:1; 50 calibration items; 375 second labels.

```console
PYTHONPATH=src python3 -I goldset/assign.py
python3 -I goldset/topup.py assign
```

## 8. Address suggestions (prefill)

Paid model (`anthropic/claude-haiku-5.5` via OpenRouter). The script has a cost guard (step $10, UTC day $30, run $20) and writes one row per run to the cost ledger `results/cost_ledger.csv`. Dry run first, then a 20-host pilot, then the full run:

```console
python3 -I goldset/prefill.py --ic-fetch-dir datasets/goldset/gold --out-dir datasets/goldset/gold --dry-run
python3 -I goldset/prefill.py --ic-fetch-dir datasets/goldset/gold --out-dir datasets/goldset/prefill_pilot --limit 20 --max-usd 0.20 --note pilot
python3 -I goldset/prefill.py --ic-fetch-dir datasets/goldset/gold --out-dir datasets/goldset/gold
python3 -I goldset/prefill.py --ic-fetch-dir datasets/goldset/gold --hosts datasets/goldset/topup/hosts.txt --out-dir datasets/goldset/gold --out-file prefill_topup.jsonl
```

## 9. Labelling

One tool instance per labeller (see `docs/annotation_howto.md`):

```console
PYTHONPATH=src python3 -m ic.gold.annotate --labeller L1 --port 8800 --data-dir datasets/goldset/gold
```

Labels go to `datasets/goldset/gold/labels/L<n>.jsonl`. Annotator names and the calibration date: to be set.

## Model evaluation

### 10. Candidate runs

Model inputs from the same-day `ic fetch` records:

```console
python3 -I evaluation/build_inputs.py --gold-dir datasets/goldset/gold --sample datasets/goldset/phase2/gold_sample.jsonl --out datasets/evaluation/gold_inputs.jsonl
python3 -I evaluation/build_inputs.py --gold-dir datasets/goldset/gold --sample datasets/goldset/topup_sample.jsonl --out datasets/evaluation/topup_inputs.jsonl
```

Runs per candidate (stage `pilot` uses `$EVAL/pilot_hosts.txt`, 20 hosts; `full` all main items; `topup` the top-up items). At most 2 lanes at the same time:

```console
bash evaluation/run_candidates.sh pilot gemma4-31b-it:address,gemma4-31b-it:poi_k30,gemma4-31b-it:poi_flat,gemma4-31b-it:wz
bash evaluation/run_candidates.sh full gemma4-31b-it:address,gemma4-31b-it:poi_k30,gemma4-31b-it:poi_flat,gemma4-31b-it:wz qwen38-27b:address,qwen38-27b:poi_k30,qwen38-27b:poi_flat,qwen38-27b:wz
bash evaluation/run_candidates.sh full qwen-agentworld-35b-a3b:address,qwen-agentworld-35b-a3b:poi_k30,qwen-agentworld-35b-a3b:poi_flat,qwen-agentworld-35b-a3b:wz soofi-s-isar-preview:address,soofi-s-isar-preview:poi_k30,soofi-s-isar-preview:poi_flat,soofi-s-isar-preview:wz
bash evaluation/run_candidates.sh topup <same lanes>
python3 -I evaluation/runs_table.py --eval-dir datasets/evaluation --stage full --out results/runs_full.md
```

### 11. Scoring

After labelling and adjudication:

```console
PYTHONPATH=src python3 -m ic.eval --sample datasets/goldset/phase2/gold_sample.jsonl --labels 'datasets/goldset/gold/labels/L*.jsonl' --assignment datasets/goldset/gold/assignment.jsonl --adjudication <adjudicated.jsonl> --geocodes <geocodes.jsonl> --texts datasets/evaluation/gold_inputs.jsonl --preds datasets/evaluation/preds/full --run-id main
```

Estimator check on the real design (no labels needed):

```console
PYTHONPATH=src python3 -m ic.eval.simulate --sample datasets/goldset/phase2/gold_sample.jsonl --reps 2000 --boot-reps 300 --B 1000
```

## Tests

```console
pytest tests/test_gold_*.py tests/test_goldset_*.py tests/test_eval_*.py
IC_RUN_SLOW=1 pytest tests/test_eval_simulation.py
```

No test needs the network or a model endpoint.
