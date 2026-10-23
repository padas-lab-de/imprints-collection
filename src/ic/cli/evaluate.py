import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import click

from ic.config import *
from ic.evaluation.geocoding import (
    STREET_THRESHOLD_M,
    TOWN_THRESHOLD_KM,
    PhotonGeocoder,
)
from ic.evaluation.scoring import (
    ADDRESS_FIELDS,
    GOLD_ADDRESS_KEYS,
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
                MODELS[model]["remote"],
                messages[task],
                task,
                endpoint,
                key,
                extra_body=MODELS[model].get("extra_body"),
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


def predict_homepage_topics(
    gold, homepages_path, model, language, prompt_type, predictions_path, limit,
    retry_failed,
):
    """
    Classifies the topic of the website homepage (as production does: url, title,
    description and main content of the homepage) for every gold item with a homepage
    of non-empty content. Appends topic-only records to predictions_path.
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
    system_prompt_topic = load_prompt("topic_classification", language, "system")
    try:
        prompt_topic = load_prompt("topic_classification", language, prompt_type)
    except FileNotFoundError:
        logging.warning(f"No '{prompt_type}' topic prompt, falling back to 'simple'")
        prompt_topic = load_prompt("topic_classification", language, "simple")

    homepages = load_homepages(homepages_path)
    existing = read_predictions(predictions_path)
    done = {p["id"] for p in existing if not (retry_failed and p["topic_failed"])}
    todo = [
        item
        for item in gold
        if item["id"] in homepages and item["id"] not in done
    ]
    if limit is not None:
        todo = todo[:limit]
    logging.info(
        f"{len(done)} homepage predictions present, predicting {len(todo)} items"
    )

    def run(item):
        homepage = homepages[item["id"]]
        content = prepare_content(
            homepage["main_content"], tokenizer, MODELS[model]["max_tokens"]
        )
        messages = {
            "topic": build_topic_message(
                system_prompt_topic,
                prompt_topic,
                url=homepage["url"],
                title=homepage["title"],
                description=homepage["description"],
                content=content,
            )
        }
        record = predict_item(item, messages, model, endpoint, key)
        return {k: v for k, v in record.items() if "address" not in k}

    os.makedirs(os.path.dirname(predictions_path), exist_ok=True)
    with open(predictions_path, "a", encoding="UTF-8") as f:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_API_CALLS) as executor:
            for i, record in enumerate(executor.map(run, todo), start=1):
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                if i % 50 == 0:
                    logging.info(f"Predicted {i}/{len(todo)}")


def load_homepages(path: str) -> dict[int, dict]:
    """
    Homepages with usable content (status "ok"), by gold id.
    """
    return {h["id"]: h for h in read_jsonl(path) if h.get("status") == "ok"}


def score_homepage_topics(
    gold,
    homepages_path,
    imprint_predictions_path,
    homepage_predictions_path,
    eval_dir,
    only_predicted=False,
):
    """
    Scores the homepage topic predictions and, on the same subset of gold items with
    a homepage, the imprint-text topic predictions. Writes metrics_homepage.json.
    """
    homepages = load_homepages(homepages_path)
    subset = [item for item in gold if item["id"] in homepages]
    homepage_predictions = read_predictions(homepage_predictions_path)
    if not homepage_predictions:
        raise click.ClickException(f"No predictions found: {homepage_predictions_path}")
    if only_predicted:  # partial run (--limit)
        predicted_ids = {p["id"] for p in homepage_predictions}
        subset = [item for item in subset if item["id"] in predicted_ids]
    categories = load_categories()
    on_homepage, _ = score(subset, homepage_predictions, categories)
    on_imprint, _ = score(subset, read_predictions(imprint_predictions_path), categories)
    metrics = {
        "n_gold": len(gold),
        "n_with_homepage": len(subset),
        "n_without_homepage": len(gold) - len(subset),
        "topic_homepage_input": on_homepage["topic"],
        "topic_imprint_input_same_subset": on_imprint["topic"],
        "failed_calls_homepage": on_homepage["failed_calls"]["topic"],
    }
    with open(os.path.join(eval_dir, "metrics_homepage.json"), "w", encoding="UTF-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    click.echo(format_homepage_table(metrics))


def format_homepage_table(metrics: dict) -> str:
    """
    Renders homepage vs imprint topic metrics on the same items.
    """
    h, i = metrics["topic_homepage_input"], metrics["topic_imprint_input_same_subset"]
    lines = [
        f"Gold items: {metrics['n_gold']}   with homepage: {metrics['n_with_homepage']}"
        f"   without homepage (excluded): {metrics['n_without_homepage']}"
        f"   failed homepage calls: {metrics['failed_calls_homepage']}",
        "",
        f"{'':<38}{'homepage':>10}{'imprint':>10}",
        f"{'Topic accuracy':<38}{h['accuracy']:>10.3f}{i['accuracy']:>10.3f}",
        f"{'Topic macro-F1':<38}{h['macro_f1']:>10.3f}{i['macro_f1']:>10.3f}",
        "",
        f"{'Class F1':<38}{'homepage':>10}{'imprint':>10}{'n':>6}",
    ]
    for label, v in h["per_class"].items():
        w = i["per_class"].get(label, {"f1": 0.0})
        lines.append(f"{label:<38}{v['f1']:>10.3f}{w['f1']:>10.3f}{v['support']:>6}")
    return "\n".join(lines)


def score_predictions(
    gold,
    predictions_path,
    eval_dir,
    only_predicted=False,
    geocoder=None,
    street_m=STREET_THRESHOLD_M,
    town_km=TOWN_THRESHOLD_KM,
):
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
    if geocoder is not None:
        # fill the cache in parallel, scoring then only reads it
        addresses = [
            {f: item["output_loc"][GOLD_ADDRESS_KEYS[f]] for f in ADDRESS_FIELDS}
            for item in gold
        ] + [p.get("address") for p in predictions]
        geocoder.prefetch(addresses)
    metrics, errors = score(
        gold, predictions, load_categories(), geocoder, street_m, town_km
    )
    if geocoder is not None and geocoder.errors:
        logging.warning(f"{geocoder.errors} geocoding requests failed (not cached)")

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
@click.option(
    "--topic-input",
    type=click.Choice(["imprint", "homepage"]),
    default="imprint",
    show_default=True,
    help="homepage: classify the topic on the homepage (needs --homepages) instead "
    "of evaluating address and topic on the imprint text",
)
@click.option(
    "--homepages",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Homepages JSONL (scripts/gold_homepages.py) for --topic-input homepage",
)
@click.option(
    "--geocode/--no-geocode",
    "do_geocode",
    default=True,
    show_default=True,
    help="Geocoding-based location metric (needs GEOCODING_API_ENDPOINT)",
)
@click.option(
    "--street-threshold-m",
    type=float,
    default=STREET_THRESHOLD_M,
    show_default=True,
    help="Street-level match: maximum distance in metres",
)
@click.option(
    "--town-threshold-km",
    type=float,
    default=TOWN_THRESHOLD_KM,
    show_default=True,
    help="Town-level match: same postcode or maximum distance in km",
)
def evaluate(
    model: str,
    language: str,
    prompt_type: str,
    gold: str,
    limit: int | None,
    retry_failed: bool,
    score_only: bool,
    topic_input: str,
    homepages: str | None,
    do_geocode: bool,
    street_threshold_m: float,
    town_threshold_km: float,
):
    """
    Evaluates address extraction and topic classification against the gold standard.

    Predictions are stored in results/MODEL/LANGUAGE/PROMPT_TYPE/eval/predictions.jsonl
    (resumable), metrics in metrics.json and per-item errors in errors.jsonl.
    """
    gold_items = read_jsonl(gold)
    eval_dir = os.path.join(RESULTS_FOLDER, model, language, prompt_type, "eval")
    predictions_path = os.path.join(eval_dir, "predictions.jsonl")

    if topic_input == "homepage":
        if homepages is None:
            raise click.UsageError("--topic-input homepage needs --homepages")
        homepage_predictions_path = os.path.join(
            eval_dir, "predictions_topic_homepage.jsonl"
        )
        if not score_only:
            predict_homepage_topics(
                gold_items,
                homepages,
                model,
                language,
                prompt_type,
                homepage_predictions_path,
                limit,
                retry_failed,
            )
        score_homepage_topics(
            gold_items,
            homepages,
            predictions_path,
            homepage_predictions_path,
            eval_dir,
            only_predicted=limit is not None,
        )
        return

    geocoder = None
    if do_geocode:
        import dotenv

        dotenv.load_dotenv()
        endpoint = os.getenv("GEOCODING_API_ENDPOINT")
        assert (
            endpoint is not None
        ), "GEOCODING_API_ENDPOINT not set in environment variables"
        geocoder = PhotonGeocoder(
            endpoint, os.path.join(eval_dir, "geocode_cache.jsonl")
        )

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
        gold_items,
        predictions_path,
        eval_dir,
        only_predicted=limit is not None,
        geocoder=geocoder,
        street_m=street_threshold_m,
        town_km=town_threshold_km,
    )
