import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import click

from ic.config import *
from ic.evaluation.scoring import (
    ADDRESS_FIELDS,
    format_table,
    load_categories,
    score,
)
from ic.utils.model_run_service import call_api
from ic.utils.parsing_utils import parse_llm_response_content
from ic.utils.prompt_utils import (
    build_address_message,
    build_topic_message,
    load_prompt,
    prepare_content,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

GOLD_PATH = os.path.join("evaluation", "gold_standard_data.jsonl")
MAX_CONCURRENT_API_CALLS = 10


def read_jsonl(path: str) -> list[dict]:
    """
    Reads all records of a JSONL file.
    """
    with open(path, "r", encoding="UTF-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_address(content: str | None) -> dict | None:
    """
    Extracts the five address fields (lower-case keys) from a raw LLM response.
    Returns None if the response contains no usable address.
    """
    parsed = parse_llm_response_content(content)
    if not all(field in parsed for field in ADDRESS_FIELDS):
        return None
    address = {field: str(parsed[field]) for field in ADDRESS_FIELDS}
    if all(value.strip() == "" for value in address.values()):
        return None
    return address


def parse_topic(content: str | None) -> str | None:
    """
    Extracts the predicted category ("thema") from a raw LLM response.
    """
    thema = parse_llm_response_content(content).get("thema")
    return thema if isinstance(thema, str) else None


def usage_of(response) -> dict | None:
    """
    Token usage of a ChatCompletion, if the API reports it.
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
    }


def predict_item(item: dict, messages: dict, model: str, endpoint: str, key: str):
    """
    Runs the address and topic prompt for one gold item and builds its prediction record.
    """
    record = {"id": item["id"]}
    for task, parse, field in (
        ("address", parse_address, "address"),
        ("topic", parse_topic, "topic"),
    ):
        response = None
        if task in messages:
            response = call_api(
                MODELS[model]["remote"], messages[task], task, endpoint, key
            )
        raw = response.choices[0].message.content if response else None
        result = parse(raw) if raw else None
        record[field] = result
        record[f"raw_{task}"] = raw
        record[f"usage_{task}"] = usage_of(response) if response else None
        record[f"{task}_failed"] = result is None
    return record


def read_predictions(path: str) -> list[dict]:
    """
    Reads predictions; later records of the same id replace earlier ones.
    """
    if not os.path.exists(path):
        return []
    return list({p["id"]: p for p in read_jsonl(path)}.values())


def predict(gold, model, language, prompt_type, predictions_path, limit, retry_failed):
    """
    Predicts address and topic for the gold items and appends them to predictions_path.
    """
    import dotenv
    from transformers import AutoTokenizer

    dotenv.load_dotenv()
    endpoint = os.getenv("MODEL_API_ENDPOINT")
    assert endpoint is not None, "MODEL_API_ENDPOINT not set in environment variables"
    key = os.getenv("MODEL_API_KEY")
    assert key is not None, "MODEL_API_KEY not set in environment variables"

    tokenizer = AutoTokenizer.from_pretrained(
        MODELS[model]["local"], trust_remote_code=True
    )

    system_prompt_address = load_prompt("address_extraction", language, "system")
    system_prompt_topic = load_prompt("topic_classification", language, "system")
    prompt_address = load_prompt("address_extraction", language, prompt_type)
    try:
        prompt_topic = load_prompt("topic_classification", language, prompt_type)
    except FileNotFoundError:
        logging.warning(f"No '{prompt_type}' topic prompt, falling back to 'simple'")
        prompt_topic = load_prompt("topic_classification", language, "simple")

    # Resume: skip ids that already have a prediction
    existing = read_predictions(predictions_path)
    done = {
        p["id"]
        for p in existing
        if not (retry_failed and (p["address_failed"] or p["topic_failed"]))
    }
    todo = [item for item in gold if item["id"] not in done]
    if limit is not None:
        todo = todo[:limit]
    logging.info(f"{len(done)} predictions present, predicting {len(todo)} items")

    def run(item):
        messages = {}
        if item["plain_text"].strip() != "":
            content = prepare_content(
                item["plain_text"], tokenizer, MODELS[model]["max_tokens"]
            )
            messages["address"] = build_address_message(
                system_prompt_address, prompt_address, content
            )
            messages["topic"] = build_topic_message(
                system_prompt_topic,
                prompt_topic,
                url=item["url"],
                title=item["title"],
                description="",  # the gold standard has no description field
                content=content,
            )
        return predict_item(item, messages, model, endpoint, key)

    os.makedirs(os.path.dirname(predictions_path), exist_ok=True)
    with open(predictions_path, "a", encoding="UTF-8") as f:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_API_CALLS) as executor:
            for i, record in enumerate(executor.map(run, todo), start=1):
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                if i % 50 == 0:
                    logging.info(f"Predicted {i}/{len(todo)}")


def score_predictions(gold, predictions_path, eval_dir, only_predicted=False):
    """
    Scores the stored predictions and writes metrics.json and errors.jsonl.
    With only_predicted, gold items without a prediction record are left out.
    """
    predictions = read_predictions(predictions_path)
    if not predictions:
        raise click.ClickException(f"No predictions found: {predictions_path}")
    if only_predicted:
        predicted_ids = {p["id"] for p in predictions}
        gold = [item for item in gold if item["id"] in predicted_ids]
    metrics, errors = score(gold, predictions, load_categories())

    with open(os.path.join(eval_dir, "metrics.json"), "w", encoding="UTF-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    with open(os.path.join(eval_dir, "errors.jsonl"), "w", encoding="UTF-8") as f:
        for error in errors:
            f.write(json.dumps(error, ensure_ascii=False) + "\n")

    click.echo(format_table(metrics))


@click.command()
@click.argument("model", type=click.Choice(list(MODELS.keys())))
@click.argument(
    "language",
    type=click.Choice(["english", "german"]),
    default="german",
)
@click.argument(
    "prompt_type",
    type=click.Choice(["simple", "expert"]),
    default="simple",
)
@click.option(
    "--gold",
    type=click.Path(exists=True, dir_okay=False),
    default=GOLD_PATH,
    show_default=True,
    help="Gold standard JSONL file",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Predict at most N new items (scores only predicted items)",
)
@click.option(
    "--retry-failed", is_flag=True, help="Re-run items whose earlier calls failed"
)
@click.option(
    "--score-only", is_flag=True, help="Skip predicting, only score stored predictions"
)
def evaluate(
    model: str,
    language: str,
    prompt_type: str,
    gold: str,
    limit: int | None,
    retry_failed: bool,
    score_only: bool,
):
    """
    Evaluates address extraction and topic classification against the gold standard.

    Predictions are stored in results/MODEL/LANGUAGE/PROMPT_TYPE/eval/predictions.jsonl
    (resumable), metrics in metrics.json and per-item errors in errors.jsonl.
    """
    gold_items = read_jsonl(gold)
    eval_dir = os.path.join(RESULTS_FOLDER, model, language, prompt_type, "eval")
    predictions_path = os.path.join(eval_dir, "predictions.jsonl")

    if not score_only:
        predict(
            gold_items,
            model,
            language,
            prompt_type,
            predictions_path,
            limit,
            retry_failed,
        )

    # A partial run (--limit) is scored on the predicted subset only
    score_predictions(
        gold_items, predictions_path, eval_dir, only_predicted=limit is not None
    )
