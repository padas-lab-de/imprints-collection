import json
import os

CONFIGS_FOLDER = "configs"
DATASETS_FOLDER = "datasets"
PARQUET_FOLDER = "parquet"
PROMPTS_FOLDER = "prompts"
GEOJSON_FOLDER = "geojson"
RESULTS_FOLDER = "results"
TEMP_FOLDER = "temp"
TOPICS_FOLDER = "topics"

MODELS = {
    "Qwen3-Next": {
        "local": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8",
        "remote": "qwen3-next-80b-a3b-instruct",
        "max_tokens": 32_000 - 2_000,
    },
    # innkube does not expose the HF ids of these models; "local" only serves
    # the tokenizer for input truncation, so the Qwen3 tokenizer is a proxy
    "Qwen3.8-27B": {
        "local": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8",
        "remote": "qwen38-27b",
        "max_tokens": 32_000 - 2_000,
        # reasoning otherwise exhausts the 2,000 output tokens on topic calls
        "extra_body": {"reasoning_effort": "none"},
    },
    "Gemma4-31B": {
        "local": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8",
        "remote": "gemma4-31b-it",
        "max_tokens": 32_000 - 2_000,
    },
}
TOPICS = []
with open(os.path.join(TOPICS_FOLDER, "categories.jsonl"), "r") as f:
    TOPICS = [json.loads(line)["name"] for line in f if line.strip()]
