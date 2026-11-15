# German Imprints Collection

This repository holds the pipeline behind the **German Imprints Dataset**, the base of the
WebKurator.de platform. The pipeline fetches German websites and their legal imprint pages
(*Impressum*), extracts the postal address and the topic of each site with a Large Language Model
(LLM), geocodes the addresses and merges everything into one dataset.

The dataset can be used for regional web analysis, web curation and selective web archiving.

## Repository layout

| Path | Content |
| --- | --- |
| `src/ic/` | the `ic` command line tool (one module per command in `src/ic/cli/`) |
| `prompts/` | prompts for address extraction and topic classification |
| `topics/` | topic taxonomy |
| `geojson/` | boundaries of European countries and German states, counties and districts (used by `ic merge`) |
| `evaluation/gold_standard_data.jsonl` | 1,000 manually annotated pages |
| `collection/` | scripts that compute the published site count from the crawl output |
| `goldset/` | scripts that build the gold set (frame, screen, draw, top-up, capture, assignment, prefill) |
| `evaluation/` (scripts) | model runs of the candidates on the gold inputs |
| `src/ic/gold/`, `src/ic/eval/` | gold-set library and labelling tool; scorer (`python3 -m ic.eval`) |
| `docs/` | reproduction guides, gold-set design, model evaluation protocol, annotation guideline |
| `seed_hosts.txt.gz` | seed list, 6.56 million hosts (filtered for spam, adult content, crawler traps and redirects to large platforms) |
| `small_sample_seed_hosts.txt` | 1,000 hosts to test the pipeline |
| `tests/` | unit tests (no network needed) |

`ic` writes its outputs to `datasets/` and `results/`. Both folders are created on demand and are
not part of the repository.

## Install

Python 3.10 to 3.12.

With [Poetry](https://python-poetry.org/):

```console
poetry install
poetry run ic --help
```

With pip:

```console
python3 -m venv .venv
.venv/bin/pip install -e . pytest
.venv/bin/ic --help
```

`vllm` is only needed for local inference and is an optional extra (`poetry install --extras local`).

Copy `.env.template` to `.env` and fill in the LLM endpoint (`MODEL_API_ENDPOINT`, `MODEL_API_KEY`,
any OpenAI-compatible API) and the geocoding endpoint (`GEOCODING_API_ENDPOINT`, for example a local
[Photon](https://github.com/komoot/photon) instance). Do not commit `.env`.

Run `ic` from the repository root: it reads `prompts/` and `topics/` with relative paths.

Tests: `pytest`. Formatting: `isort . && black .`.

## Run the pipeline

```console
# 1. fetch the home page, imprint, privacy and contact page of each host
ic fetch small_sample_seed_hosts.txt
# 2. extract addresses (and topics with --topic) with an LLM
ic process-llm MODEL --topic
# 3. geocode the addresses
ic geocode MODEL
# 4. merge the LLM output and the coordinates
ic merge MODEL
# 5. compute statistics
ic stats MODEL
# 6. score address extraction and topic classification against the gold standard
ic evaluate MODEL
```

- `ic fetch HOSTS [BATCH_SIZE START_BATCH END_BATCH NUM_WORKERS]` reads an uncompressed host list
  (one host per line) and writes `datasets/imprints_batchN.jsonl.gz` and
  `datasets/fetch_status_batchN.tsv`. A second run resumes. `--output-dir` sets another folder;
  `ic fetch --help` lists the politeness options. For the full seed list:
  `zcat seed_hosts.txt.gz > datasets/seed_hosts.txt`, then optionally
  `ic clean-hosts datasets/seed_hosts.txt`, then `ic fetch` on the result.
- `MODEL` is a key of `MODELS` in `src/ic/config.py`. The optional arguments `LANGUAGE`
  (`german` or `english`) and `PROMPT_TYPE` (`simple` or `expert`) follow `MODEL` in steps 2 to 6.
- The final dataset is in `results/MODEL/LANGUAGE/PROMPT_TYPE/final/*.jsonl.gz`, one JSON object per
  host with the fetched pages, the topic, the address and the coordinates.
- `ic evaluate` writes `predictions.jsonl`, `metrics.json` and `errors.jsonl` to
  `results/MODEL/LANGUAGE/PROMPT_TYPE/eval/`. `--score-only` re-scores stored predictions.
- `ic upload-postgresql` and `ic upload-opensearch` load the final dataset into a database (connection
  settings in `.env`).

## Reproduce the site count

The 2026 snapshot has **3,945,356** canonical sites with an imprint. A canonical site is a host
without `www.`, after redirects to another crawled host are followed; parked domains, domains for
sale and hoster placeholder pages are removed.

The count can be reproduced from the published crawl tables in about 10 minutes, with no crawling:

```console
collection/download_release_data.sh data/collection
collection/reproduce_final_count.sh data/collection out
```

The script prints the line count and the sha256 of the final site list and compares every output
with the published checksums. See [docs/reproduce_collection.md](docs/reproduce_collection.md) for
the steps and for how to build the crawl tables from your own `ic fetch` output.

## Gold set and model evaluation

The gold set is a two-phase probability sample of the released sites: 1,869 items, plus 18 items
from the sites added in the final list. Every item has a known inclusion probability, so each score
is a population estimate with a confidence interval for the release. Three labellers (L1, L2, L3)
label the site status, the imprint, the main address and two topics (POI v3, WZ 2025) from a frozen
browser capture. The candidate models get the same-day `ic fetch` text as input.

- Method: [docs/gold_set_design.md](docs/gold_set_design.md)
- Scoring and decision rule: [docs/model_eval_protocol.md](docs/model_eval_protocol.md)
- Labelling: [docs/annotation_guideline.md](docs/annotation_guideline.md), [docs/annotation_howto.md](docs/annotation_howto.md)
- Commands, one per step: [docs/reproduce_goldset.md](docs/reproduce_goldset.md)

The gold data (captures, labels) and the predictions are not part of the repository. Annotator
names and the labelling dates are to be set.

## Data location

The data package of the 2026 snapshot is on the Uni Passau innkube S3 storage
(`https://share.innkube.fim.uni-passau.de`, bucket `datasets`, prefix `imprints/20261109/`).
It holds the crawl output, the crawl tables, the page scans and the checksums (`MANIFEST.sha256`).
Ask the maintainers for a read key.

## License

MIT, see `LICENSE`.
