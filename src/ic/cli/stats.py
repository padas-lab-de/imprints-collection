import gzip
import json
import os

import click
import geopandas as gpd
import tldextract
from shapely.geometry import Point
from tqdm import tqdm

from ic.config import *

TOTAL_HOSTS = 6_560_119


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
def stats(model: str, language: str, prompt_type: str):
    """
    Compute statistics.
    """
    final_results_path = os.path.join(
        RESULTS_FOLDER, model, language, prompt_type, "final"
    )
    if not os.path.exists(final_results_path):
        click.echo(f"Final results path does not exist: {final_results_path}. Please run the merge command first.")
        return

    # TODO: Comparison between annotated structured data (address and coords) and LLM extracted address plus geocoded coords

    # Load categories
    categories = {}
    categories_path = os.path.join(TOPICS_FOLDER, "categories.jsonl")
    with open(categories_path, "r", encoding="UTF-8") as categories_file:
        for line in categories_file:
            try:
                data = json.loads(line)
                name = data["name"]
                parent = data["parent"]
                categories[name] = parent
            except json.JSONDecodeError:
                click.echo(f"Error decoding JSON: {line}")

    # Stats
    count = 0
    tld_count = {}
    data_fields_count = {}
    pages_fields_count = {
        "main": {},
        "impressum": {},
        "kontakt": {},
        "über uns": {},
        "datenschutz": {},
        "agb": {},
    }
    address_count = 0
    address_fields_count = {}
    country_counts = {}
    topic_count = 0
    topic_themas_count = {}
    top_topic_themas_count = {}
    geo_position_count = 0
    geo_position_longitudes = []
    geo_position_latitudes = []
    geo_position_num_features_count = {}
    region_country_counts = {}
    region_state_counts = {}
    region_district_counts = {}
    region_county_counts = {}

    # Loop over all results files
    for filename in sorted(os.listdir(final_results_path)):
        if filename.startswith("batch") and filename.endswith(".jsonl.gz"):
            click.echo(f"Processing file: {filename}")

            # Read file with scores
            file_path = os.path.join(final_results_path, filename)
            with gzip.open(
                file_path,
                "rt",
                encoding="UTF-8",
            ) as file:
                count_file = 0
                for line in tqdm(file):
                    try:
                        data = json.loads(line)

                        count += 1

                        host = data["host"]
                        # Extract TLD from host
                        tld_result = tldextract.extract(host)
                        tld = tld_result.suffix
                        if tld not in tld_count:
                            tld_count[tld] = 0
                        tld_count[tld] += 1

                        for key, value in data.items():
                            if key not in data_fields_count:
                                data_fields_count[key] = 0
                            if value is not None:
                                data_fields_count[key] += 1

                        for page_type in pages_fields_count.keys():
                            if page_type in data:
                                for key, value in data[page_type].items():
                                    if key not in pages_fields_count[page_type]:
                                        pages_fields_count[page_type][key] = 0
                                    if (
                                        value is not None
                                        and value != ""
                                        and value != []
                                    ):
                                        pages_fields_count[page_type][key] += 1

                        if "address" in data:
                            address_count += 1

                            for key, value in data["address"].items():
                                if key not in address_fields_count:
                                    address_fields_count[key] = 0
                                if value is not None and value != "":
                                    address_fields_count[key] += 1

                            if "country" in data["address"]:
                                country = data["address"]["country"]
                                if country is None:
                                    country = "<None>"
                                if country.strip() == "":
                                    country = "<Empty>"
                                country = country.strip().lower().capitalize()
                                if country not in country_counts:
                                    country_counts[country] = 0
                                country_counts[country] += 1

                        if "topic" in data:
                            topic_count += 1
                            thema = data["topic"]
                            if thema not in topic_themas_count:
                                topic_themas_count[thema] = 0
                            topic_themas_count[thema] += 1

                            parent_thema = thema
                            while categories.get(parent_thema) is not None:
                                parent_thema = categories[parent_thema]
                            if parent_thema not in top_topic_themas_count:
                                top_topic_themas_count[parent_thema] = 0
                            top_topic_themas_count[parent_thema] += 1

                        if "coords" in data:
                            geo_position_count += 1
                            coords = data["coords"]
                            longitude = coords["longitude"]
                            latitude = coords["latitude"]
                            geo_position_longitudes.append(longitude)
                            geo_position_latitudes.append(latitude)

                            if "num_features" in coords:
                                num_features = coords["num_features"]
                                if num_features not in geo_position_num_features_count:
                                    geo_position_num_features_count[num_features] = 0
                                geo_position_num_features_count[num_features] += 1

                        if "region" in data:
                            region_country = data["region"]["country"]
                            region_state = data["region"]["state"]
                            region_district = data["region"]["district"]
                            region_county = data["region"]["county"]

                            region_country_counts[region_country] = (
                                region_country_counts.get(region_country, 0) + 1
                            )
                            region_state_counts[region_state] = (
                                region_state_counts.get(region_state, 0) + 1
                            )
                            region_district_counts[region_district] = (
                                region_district_counts.get(region_district, 0) + 1
                            )
                            region_county_counts[region_county] = (
                                region_county_counts.get(region_county, 0) + 1
                            )

                    except json.JSONDecodeError:
                        click.echo(f"Error decoding JSON: {line}")

                    count_file += 1
                    # if count_file >= 100:
                    #     break

            click.echo(f"Processed {count_file} entries")

            # For testing, process only one file
            # break

    click.echo(
        f"Total entries processed: {count}/{TOTAL_HOSTS} ({(count / TOTAL_HOSTS * 100):.2f}%)"
    )
    click.echo("TLD counts:")
    tld_count = sorted(tld_count.items(), key=lambda item: item[1], reverse=True)
    for i, (key, value) in enumerate(tld_count):
        if value < 100 or i >= 20:
            break
        click.echo(f"  {key}: {value} ({(value / count * 100):.2f}%)")
    click.echo("Data fields counts:")
    data_fields_count = dict(
        sorted(data_fields_count.items(), key=lambda item: item[1], reverse=True)
    )
    for key, value in data_fields_count.items():
        click.echo(f"  {key}: {value} ({(value / count * 100):.2f}%)")
    click.echo("Pages fields counts:")
    for page_type, fields_count in pages_fields_count.items():
        click.echo(f"  Page type: {page_type}")
        fields_count = sorted(
            fields_count.items(), key=lambda item: item[1], reverse=True
        )
        for key, value in fields_count:
            click.echo(
                f"    {key}: {value} ({(value / data_fields_count[page_type] * 100):.2f}%)"
            )
    click.echo(f"Total addresses: {address_count}")
    click.echo("Address fields counts:")
    address_fields_count = sorted(
        address_fields_count.items(), key=lambda item: item[1], reverse=True
    )
    for key, value in address_fields_count:
        click.echo(f"  {key}: {value} ({(value / address_count * 100):.2f}%)")
    click.echo("Country counts:")
    country_counts = sorted(
        country_counts.items(), key=lambda item: item[1], reverse=True
    )
    for i, (country, value) in enumerate(country_counts):
        if value < 100 or i >= 10:
            break
        click.echo(f"  {country}: {value} ({(value / address_count * 100):.2f}%)")
    click.echo(f"Total topics found: {topic_count}")
    click.echo("Topic themas counts:")
    topic_themas_count = sorted(
        topic_themas_count.items(), key=lambda item: item[1], reverse=True
    )
    for i, (thema, value) in enumerate(topic_themas_count):
        if value < 100 or i >= 10:
            break
        click.echo(f"  {thema}: {value} ({(value / topic_count * 100):.2f}%)")
    click.echo("Top-level Topic themas counts:")
    top_topic_themas_count = sorted(
        top_topic_themas_count.items(), key=lambda item: item[1], reverse=True
    )
    for i, (thema, value) in enumerate(top_topic_themas_count):
        # if value < 100 or i >= 10:
        #     break
        click.echo(f"  {thema}: {value} ({(value / topic_count * 100):.2f}%)")
    click.echo(f"Total geocoded positions: {geo_position_count}")
    if geo_position_count > 0:
        avg_longitude = sum(geo_position_longitudes) / geo_position_count
        avg_latitude = sum(geo_position_latitudes) / geo_position_count
        click.echo(f"Average Longitude: {avg_longitude:.6f}")
        click.echo(f"Average Latitude: {avg_latitude:.6f}")
        click.echo("Geo position num_features counts:")
        geo_position_num_features_count = sorted(
            geo_position_num_features_count.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        for num_features, value in geo_position_num_features_count:
            click.echo(
                f"  {num_features}: {value} ({(value / geo_position_count * 100):.2f}%)"
            )
    click.echo("Region country counts:")
    region_country_counts = sorted(
        region_country_counts.items(), key=lambda item: item[1], reverse=True
    )
    for i, (country, value) in enumerate(region_country_counts):
        # if value < 100 or i >= 10:
        #     break
        click.echo(f"  {country}: {value} ({(value / geo_position_count * 100):.2f}%)")
    click.echo("Region state counts:")
    region_state_counts = sorted(
        region_state_counts.items(), key=lambda item: item[1], reverse=True
    )
    for i, (state, value) in enumerate(region_state_counts):
        # if value < 100 or i >= 10:
        #     break
        click.echo(f"  {state}: {value} ({(value / geo_position_count * 100):.2f}%)")
    click.echo("Region district counts:")
    region_district_counts = sorted(
        region_district_counts.items(), key=lambda item: item[1], reverse=True
    )
    for i, (district, value) in enumerate(region_district_counts):
        # if value < 100 or i >= 10:
        #     break
        click.echo(f"  {district}: {value} ({(value / geo_position_count * 100):.2f}%)")
    click.echo("Region county counts:")
    region_county_counts = sorted(
        region_county_counts.items(), key=lambda item: item[1], reverse=True
    )
    for i, (county, value) in enumerate(region_county_counts):
        # if value < 100 or i >= 10:
        #     break
        click.echo(f"  {county}: {value} ({(value / geo_position_count * 100):.2f}%)")

    click.echo("Done")
