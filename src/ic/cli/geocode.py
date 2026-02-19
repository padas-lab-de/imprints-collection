import gzip
import json
import logging
import os
import time
import dotenv
import urllib.parse

import click
import requests
from tqdm import tqdm

from ic.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
def geocode(model: str, language: str, prompt_type: str):
    """
    Geocode locations.
    """
    # Load environment variables from .env file
    dotenv.load_dotenv()

    # Check if geocoding API endpoint is set
    GEOCODING_API_ENDPOINT = os.getenv("GEOCODING_API_ENDPOINT")
    assert GEOCODING_API_ENDPOINT is not None, "GEOCODING_API_ENDPOINT not set in environment variables"

    # Check if results path exists
    results_path = os.path.join(RESULTS_FOLDER, model, language, prompt_type, "llm")
    if not os.path.exists(results_path):
        click.echo(f"Results path does not exist: {results_path}. Please run the process-llm command first.")
        return

    # Loop over all results files
    for filename in sorted(os.listdir(results_path)):
        
        if not filename.startswith("imprints_batch") or not filename.endswith(".jsonl.gz"):
            continue

        logger.info(f"Processing file: {filename}")

        # Load imprints data
        file_path = os.path.join(results_path, filename)
        data = []
        with gzip.open(file_path, "rt", encoding="UTF-8") as f:
            for line in f:
                data.append(json.loads(line))
        logger.info(f"Loaded {len(data)} entries")

        # Results dict
        results_address = {}
        count_found = 0
        count_not_found = 0
        no_address_output = 0
        empty_address_count = 0

        for index, document in tqdm(
            enumerate(data), total=len(data), desc="Geocoding locations"
        ):
            if not "address" in document:
                no_address_output += 1
                continue

            address_data = document["address"]
            country = address_data["country"]
            town = address_data["town"]
            plz = address_data["postalcode"]
            streetname = address_data["streetname"]
            housenumber = address_data["housenumber"]
            full_address = f"{country} {town} {plz} {streetname} {housenumber}".strip().replace(
                "  ", " "
            )
            if full_address == "":
                empty_address_count += 1
                continue

            encoded_address = urllib.parse.quote(full_address)

            try:
                response_data = None
                response = None
                recount = 0
                while recount < 3:
                    api_link = f"{GEOCODING_API_ENDPOINT}?q={encoded_address}"
                    response = requests.get(api_link, timeout=10)
                    if response.status_code == 200:
                        response_data = response.json()
                        break
                    recount += 1
                    time.sleep(1)

                if response is None:
                    logger.warning(f"No response for: {full_address}")
                    continue

                if response_data is None:
                    logger.warning(
                        f"Failed to get response for: {full_address} (status code: {response.status_code}; recount: {recount})"
                    )
                    continue

                if len(response_data["features"]) == 0:
                    # logger.warn(f"No geocode found for: {full_address}")
                    count_not_found += 1
                    continue

                response_tuple = response_data["features"][0]["geometry"][
                    "coordinates"
                ]
                results_address[index] = {
                    "longitude": response_tuple[0],
                    "latitude": response_tuple[1],
                    "num_features": len(response_data["features"]),
                    "features": response_data["features"],
                }
                count_found += 1

            except Exception as e:
                logger.error(f"Exception caught when geocoding {full_address}: {e}")

        log_output = "Geocoding results:\n"
        log_output += f"  No address: {no_address_output}\n"
        log_output += f"  Empty address: {empty_address_count}\n"
        log_output += f"  Found: {count_found}\n"
        log_output += f"  Not found: {count_not_found}\n"
        log_output += f"  Unknown errors: {len(data) - (no_address_output + empty_address_count + count_found + count_not_found)}\n"
        logger.info(log_output)

        # Store new file with results
        geocoded_results_path = os.path.join(
            RESULTS_FOLDER, model, language, prompt_type, "geocoded", filename
        )
        os.makedirs(os.path.dirname(geocoded_results_path), exist_ok=True)
        with gzip.open(geocoded_results_path, "wt", encoding="UTF-8") as f:
            for index in range(len(data)):
                document = data[index]
                if index in results_address:
                    document["coords"] = results_address[index]
                f.write(json.dumps(document, ensure_ascii=False) + "\n")

    click.echo("Done")
