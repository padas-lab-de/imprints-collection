# CLAUDE.md

## What this is
Pipeline behind the German Imprints Dataset (WebKurator.de): fetch German websites and their Impressum pages, extract postal addresses and topics with LLMs, geocode, merge, and compute statistics. Python CLI `ic` (click), packaged with Poetry. Journal-extension work (model comparison, error analysis, geocoding evaluation, larger snapshot) is in progress.

## Read first
`docs/decisions.md` is the lead record: decisions `D<n>`, actions `A<n>`, experiments `E<n>`. Read it on takeover and update it when a decision, action or experiment changes state.

## Install and run
- `poetry install` (or `python3 -m venv .venv && .venv/bin/pip install -e . pytest`). `vllm` is an optional extra (`--extras local`), not needed for API-based inference.
- Run `ic ...` from the repository root: `src/ic/config.py` reads `topics/` and `prompts/` with relative paths.
- Copy `.env.template` to `.env` (never commit it).
- Tests: `pytest` (smoke tests need no network). Formatting: `isort . && black .`.

## Layout
- `src/ic/ic.py` entry point; `src/ic/cli/` one module per command (`fetch`, `clean-hosts`, `process-llm`, `geocode`, `merge`, `stats`, `upload-*`); `src/ic/utils/`, `src/ic/parsing/` helpers; `src/ic/config.py` paths and `MODELS`.
- `prompts/`, `topics/`, `geojson/` inputs; `evaluation/gold_standard_data.jsonl` gold set; `seed_hosts.txt.gz`, `small_sample_seed_hosts.txt` seed lists (repo root).
- `datasets/` and `results/` are generated and untracked.

## Spend limits
Paid APIs: at most $20 per experiment run and $30 per UTC day. Enforce from the cost ledger `docs/cost_ledger.csv` (create it on the first paid run; log every paid run and check the day's total before starting).

## Infrastructure
- Crawling (`ic fetch`) runs from the VM in the crawling subnet.
- LLM inference uses the Uni Passau innkube endpoint (`MODEL_API_ENDPOINT`) or the FAITH Slurm cluster: https://faith.pages.fim.uni-passau.de/public-docs/slurm/

## Git
No global git identity is configured. Commit with `git -c user.name="Michael Dinzinger" -c user.email="39766249+michaeldinzinger@users.noreply.github.com" commit ...`.
