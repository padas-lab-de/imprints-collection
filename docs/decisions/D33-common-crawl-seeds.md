# D33-common-crawl-seeds · Add Common Crawl as a new seed source: pilot 20k now, or later?

Issued 2026-11-03 by the data-collection lead, after the user asked: "Would [Common Crawl web graph / DuckDB data lake on Hugging Face] allow us to pull more seed websites?"

## Context
- Original seed sources (WebSci demo paper arXiv 2609.03971, Sec. 3.1): Open Web Index, Common Crawl, Curlie; hosts selected by imprint URL paths (/impressum, /imprint). No counts per source, no crawl dates. The repo states no source.
- Common Crawl URL index (Parquet, data.commoncrawl.org), DuckDB over HTTPS, no credentials: one crawl, .de/.at/.ch hosts with a 200 page and the content-language flag, reads ~0.9 GB, ~9 s on lorbeer. Free.
- CC-MAIN-2026-43: 3.05M DACH hosts with a 200 page; 2.69M with a German page. Not in seeds or any E22 frontier (www-collapsed, lead recount): 622,665 (.de 440,230, .at 69,843, .ch 112,592). Candidate file tmp research/cc43_dach_hosts.parquet.
- Web graph (cc-main-2026-aug-sep-oct): 8.85M .de host vertices, but includes uncrawled and spam hosts, no language -> weak alone.
- HF: host index commoncrawl/host-index-testing-v2 (latest CC-MAIN-2025-18, "testing"), experimental HF bucket with 2026 crawls; FineWeb-2 deu_Latn. No single "data lake"; the URL index is the main route.
- Imprint yield on these hosts unknown (E22 link-expansion hosts ~10%; E16 seeds 49.6%).

## Options
- **A** Build E23-cc-seed-candidates from the last 3 crawls (2026-34/-39/-43), apply clean-hosts + E10 platform filter, drop all known hosts, pilot 20k random on lorbeer now (alongside depth2R, PCONC 8, Shopify skipped). Measured yield decides the full crawl. Cost: one VM IP shared with depth2R; no money.
- **B** Same list now, pilot after depth2R finishes. Cost: VMs stay on one job at a time.
- **C** Not now: keep the snapshot to seeds + link expansion.

**Recommend A:** the list costs nothing to build, and the pilot gives the yield number that decides whether Common Crawl is worth a full pass.

## Answer
(open)
