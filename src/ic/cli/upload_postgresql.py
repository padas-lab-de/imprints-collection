import gzip
import json
import logging
import os

import click
import dotenv
import psycopg2
from tqdm import tqdm

from ic.config import *

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_table(cur, table_name: str):
    """
    Create the imprints data table.
    """
    command = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        host TEXT PRIMARY KEY,
        url TEXT,
        title TEXT,
        description TEXT,
        keywords TEXT[],
        main_content TEXT,
        content_language TEXT,
        topic TEXT,
        address_country TEXT,
        address_town TEXT,
        address_postalcode TEXT,
        address_streetname TEXT,
        address_housenumber TEXT,
        coords_longitude DOUBLE PRECISION,
        coords_latitude DOUBLE PRECISION,
        region_country TEXT,
        region_state TEXT,
        region_district TEXT,
        region_county TEXT
    );
    """
    cur.execute(command)


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
@click.argument("table_name", type=str)
def upload_postgresql(model: str, language: str, prompt_type: str, table_name: str):
    """
    Upload normalized imprint data to PostgreSQL with geo support.
    """
    dotenv.load_dotenv()

    dbname = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )
    cur = conn.cursor()

    # Create table if not exists
    create_table(cur, table_name)
    conn.commit()

    final_results_path = os.path.join(
        RESULTS_FOLDER, model, language, prompt_type, "final"
    )
    if not os.path.exists(final_results_path):
        click.echo(f"Geocoded results path does not exist: {final_results_path}")
        return

    # TODO: Add geography column and restrict to regions inside Germany

    for filename in sorted(os.listdir(final_results_path)):
        click.echo(f"Processing file: {filename}")

        file_path = os.path.join(final_results_path, filename)
        with gzip.open(file_path, "rt", encoding="UTF-8") as file:
            for line in tqdm(file):
                entry = json.loads(line)

                host = entry.get("host")
                url = entry["main"]["url"]
                title = entry["main"].get("title")
                description = entry["main"].get("description")
                keywords = entry["main"].get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]
                main_content = entry["main"].get("main_content")
                content_language = entry["main"].get("content_language")
                topic = entry.get("topic", {"thema": None})["thema"]
                address = entry.get("address")
                address_country = address.get("country") if address else None
                address_town = address.get("town") if address else None
                address_postalcode = address.get("postalcode") if address else None
                address_streetname = address.get("streetname") if address else None
                address_housenumber = address.get("housenumber") if address else None
                coords = entry.get("coords")

                coords_longitude = None
                coords_latitude = None
                region_country = None
                region_state = None
                region_district = None
                region_county = None
                if coords:
                    coords_longitude = coords["longitude"]
                    coords_latitude = coords["latitude"]

                    # TODO: Fill region fields

                command = f"""
                    INSERT INTO {table_name} (
                        host,
                        url,
                        title,
                        description,
                        keywords,
                        main_content,
                        content_language,
                        topic,
                        address_country,
                        address_town,
                        address_postalcode,
                        address_streetname,
                        address_housenumber,
                        coords_longitude,
                        coords_latitude,
                        region_country,
                        region_state,
                        region_district,
                        region_county
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (host) DO UPDATE
                    SET url = EXCLUDED.url,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        keywords = EXCLUDED.keywords,
                        main_content = EXCLUDED.main_content,
                        content_language = EXCLUDED.content_language,
                        topic = EXCLUDED.topic,
                        address_country = EXCLUDED.address_country,
                        address_town = EXCLUDED.address_town,
                        address_postalcode = EXCLUDED.address_postalcode,
                        address_streetname = EXCLUDED.address_streetname,
                        address_housenumber = EXCLUDED.address_housenumber,
                        coords_longitude = EXCLUDED.coords_longitude,
                        coords_latitude = EXCLUDED.coords_latitude,
                        region_country = EXCLUDED.region_country,
                        region_state = EXCLUDED.region_state,
                        region_district = EXCLUDED.region_district,
                        region_county = EXCLUDED.region_county;
                    """

                cur.execute(
                    command,
                    (
                        host,
                        url,
                        title,
                        description,
                        keywords,
                        main_content,
                        content_language,
                        topic,
                        address_country,
                        address_town,
                        address_postalcode,
                        address_streetname,
                        address_housenumber,
                        coords_longitude,
                        coords_latitude,
                        region_country,
                        region_state,
                        region_district,
                        region_county,
                    ),
                )

        # Commit after each file
        conn.commit()

    conn.close()
    logging.info("Done")
