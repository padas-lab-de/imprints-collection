# D2-llm-access (2026-10-23)
Options: Uni Passau cluster · local vLLM on own GPUs · paid APIs.
Answer (verbatim): "Uni Passau cluster (open models)", "Paid APIs (Claude, GPT, …)", "We can also use this Slurm cluster: https://faith.pages.fim.uni-passau.de/public-docs/slurm/ for running LLM on our own GPUs. The repository is currently not running on the login node of the Slurm cluster, but we can move it there when necessary. At the moment, the VM we are currently using, is in the crawling subnet, hence, we can use it for web crawling/scraping."
Implication: crawl on this VM (crawling subnet); LLM inference on innkube or Slurm; paid APIs as baselines under $20/run, $30/UTC day.
