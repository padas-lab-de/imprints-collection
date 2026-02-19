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
}
TOPICS = []
with open(os.path.join(TOPICS_FOLDER, "categories.jsonl"), "r") as f:
    TOPICS = [json.loads(line)["name"] for line in f if line.strip()]
