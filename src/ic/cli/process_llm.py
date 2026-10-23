import asyncio
import gzip
import json
import logging
import os
from typing import List

import click
import dotenv
from transformers import AutoTokenizer

from ic.config import *
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

BATCH_SIZE = 1_000
MAX_CONCURRENT_API_CALLS = 10


def generate_output(prompts: str | List[str], sampling_params, llm):
    """
    Generates LLM output for a list of prompts.
    """
    # Ensure prompts is a list
    if isinstance(prompts, str):
        prompts = [prompts]

    # Use llm.chat for batch processing
    outputs = llm.chat(prompts, sampling_params)

    return outputs


async def call_api_async(
    model: str,
    prompt: str,
    prompt_type: str,
    api_endpoint: str,
    api_key: str,
    temperature: float = 0.0,
    max_tokens: int = 2_000,
):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        # Uses default threadpool
        None,
        call_api,
        model,
        prompt,
        prompt_type,
        api_endpoint,
        api_key,
        temperature,
        max_tokens,
    )


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
@click.option("--topic", is_flag=True, help="Enable topic classification")
def process_llm(model: str, language: str, prompt_type: str, topic: bool):
    """
    Runs the geoparsing extraction process using LLMs to extract addresses from imprints.
    """
    asyncio.run(process_llm_async(model, language, prompt_type, topic))


async def process_llm_async(model: str, language: str, prompt_type: str, topic: bool):
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        MODELS[model]["local"], trust_remote_code=True
    )

    # Load environment variables from .env file
    dotenv.load_dotenv()

    MODEL_API_ENDPOINT = os.getenv("MODEL_API_ENDPOINT")
    assert MODEL_API_ENDPOINT is not None, "MODEL_API_ENDPOINT not set in environment variables"
    MODEL_API_KEY = os.getenv("MODEL_API_KEY")
    assert MODEL_API_KEY is not None, "MODEL_API_KEY not set in environment variables"

    # Load prompts
    system_prompt_address = load_prompt("address_extraction", language, "system")
    system_prompt_topic = load_prompt("topic_classification", language, "system")
    prompt_address = load_prompt("address_extraction", language, prompt_type)
    prompt_topic = load_prompt("topic_classification", language, prompt_type)

    for filename in sorted(os.listdir(DATASETS_FOLDER)):
        if not filename.startswith("imprints_batch") or not filename.endswith(
            ".jsonl.gz"
        ):
            continue

        logging.info(f"Processing file: {filename}")

        # Load imprints data
        file_path = os.path.join(DATASETS_FOLDER, filename)
        data = []
        with gzip.open(file_path, "rt", encoding="UTF-8") as f:
            for line in f:
                data.append(json.loads(line))
        logging.info(f"Loaded {len(data)} entries")

        # Initalize results dict
        results_address = {}
        results_topic = {}

        # Prepare prompts
        messages_address = {}
        messages_topic = {}

        results_path = os.path.join(
            RESULTS_FOLDER, model, language, prompt_type, "llm", filename
        )
        if os.path.exists(results_path):
            logging.info(f"LLM results file exists: {filename}")

            with gzip.open(results_path, "rt", encoding="UTF-8") as f:
                for llm_line, data_doc in zip(f, data):
                    data_doc.update(json.loads(llm_line))

        for index, document in enumerate(data):
            if "address" in document:
                results_address[index] = document["address"]

            else:
                if (
                    "impressum" in document
                    and document["impressum"]["main_content"].strip() != ""
                ):
                    main_content = prepare_content(
                        document["impressum"]["main_content"],
                        tokenizer,
                        MODELS[model]["max_tokens"],
                    )

                    message_address = build_address_message(
                        system_prompt_address, prompt_address, main_content
                    )
                    messages_address[index] = message_address

            if topic and document["main"]["main_content"].strip() != "":
                main_content = prepare_content(
                    document["main"]["main_content"],
                    tokenizer,
                    MODELS[model]["max_tokens"],
                )

                message_topic = build_topic_message(
                    system_prompt_topic,
                    prompt_topic,
                    url=document["main"]["url"],
                    title=document["main"]["title"],
                    description=document["main"]["description"],
                    content=main_content,
                )
                messages_topic[index] = message_topic

        # Transform dict to list for batch processing
        messages_address_indices = list(messages_address.keys())
        messages_address = list(messages_address.values())
        messages_topic_indices = list(messages_topic.keys())
        messages_topic = list(messages_topic.values())

        logging.info(f"Number of address prompts: {len(messages_address)}")
        logging.info(f"Number of topic prompts: {len(messages_topic)}")

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)

        async def process_batch(batch_messages, batch_indices, task_type):
            tasks = []
            for j, message in enumerate(batch_messages):
                tasks.append(process_one(message, batch_indices[j], task_type))

            results = await asyncio.gather(*tasks)
            return {
                batch_index: result
                for batch_index, result in results
                if result is not None
            }

        async def process_one(message, batch_index, task_type):
            async with semaphore:
                response = await call_api_async(
                    MODELS[model]["remote"], message, task_type, MODEL_API_ENDPOINT, MODEL_API_KEY
                )
                if not response:
                    return batch_index, None
                content = response.choices[0].message.content
                response_json = parse_llm_response_content(content)

                # Short pause between calls
                await asyncio.sleep(0.2)

            return batch_index, response_json

        logging.info("Starting batch processing for address extraction...")
        for i, batch_start in enumerate(range(0, len(messages_address), BATCH_SIZE)):
            batch_end = min(batch_start + BATCH_SIZE, len(messages_address))
            logging.info(
                f"Processing batch {i + 1}/{(len(messages_address) + BATCH_SIZE - 1)//BATCH_SIZE}"
            )

            # Create batch data
            batch_messages_address_indices = messages_address_indices[
                batch_start:batch_end
            ]
            batch_messages_address = messages_address[batch_start:batch_end]

            batch_results_address = await process_batch(
                batch_messages_address, batch_messages_address_indices, "address"
            )
            results_address.update(batch_results_address)

            logging.info(f"Completed batch {i + 1}")

            # break  # Process only one batch for testing

        if topic:
            logging.info("Starting batch processing for topic classification...")
            for i, batch_start in enumerate(range(0, len(messages_topic), BATCH_SIZE)):
                batch_end = min(batch_start + BATCH_SIZE, len(messages_topic))
                logging.info(
                    f"Processing batch {i + 1}/{(len(messages_topic) + BATCH_SIZE - 1)//BATCH_SIZE}"
                )

                # Create batch data
                batch_messages_topic_indices = messages_topic_indices[
                    batch_start:batch_end
                ]
                batch_messages_topic = messages_topic[batch_start:batch_end]

                batch_results_topic = await process_batch(
                    batch_messages_topic, batch_messages_topic_indices, "topic"
                )
                results_topic.update(batch_results_topic)

                logging.info(f"Completed batch {i + 1}")

        # Store new file with results
        os.makedirs(os.path.dirname(results_path), exist_ok=True)
        with gzip.open(results_path, "wt", encoding="UTF-8") as f:
            for index in range(len(data)):
                document = {}
                if index in results_address:
                    document["address"] = results_address[index]
                if index in results_topic:
                    document["topic"] = results_topic[index]
                f.write(json.dumps(document, ensure_ascii=False) + "\n")

        # break  # Process only one file for now

    click.echo("Done")
