import gzip
import json
import os
import time

import click
import geopandas as gpd
from shapely.geometry import Point
from tqdm import tqdm

from ic.config import *
from ic.utils.address_utils import has_address


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
def merge(model: str, language: str, prompt_type: str):
    """
    Merge results from fetching, LLM and geocoding into final results.
    """
    llm_results_path = os.path.join(RESULTS_FOLDER, model, language, prompt_type, "llm")
    if not os.path.exists(llm_results_path):
        click.echo(f"LLM results path does not exist: {llm_results_path}. Please run the process-llm command first.")
        return

    geocoded_results_path = os.path.join(
        RESULTS_FOLDER, model, language, prompt_type, "geocoded"
    )
    if not os.path.exists(geocoded_results_path):
        click.echo(f"Geocoded results path does not exist: {geocoded_results_path}. Please run the geocode command first.")
        return

    # Load European countries (FeatureCollection of MultiPolygons)
    eu_countries_path = os.path.join(GEOJSON_FOLDER, "europe.geojson")
    eu_countries = gpd.read_file(eu_countries_path)

    # Make sure CRS is WGS84 (EPSG:4326 = lon/lat)
    if eu_countries.crs is None:
        eu_countries.set_crs(epsg=4326, inplace=True)
    elif eu_countries.crs.to_epsg() != 4326:
        eu_countries = eu_countries.to_crs(epsg=4326)

    # Load German states (Bundeslaender)
    germany_states_path = os.path.join(GEOJSON_FOLDER, "germany_states.geojson")
    germany_states = gpd.read_file(germany_states_path)

    # Make sure CRS is WGS84 (EPSG:4326 = lon/lat)
    if germany_states.crs is None:
        germany_states.set_crs(epsg=4326, inplace=True)
    elif germany_states.crs.to_epsg() != 4326:
        germany_states = germany_states.to_crs(epsg=4326)

    # Load German districts (Regierungsbezirke)
    germany_districts_path = os.path.join(GEOJSON_FOLDER, "germany_districts.geojson")
    germany_districts = gpd.read_file(germany_districts_path)

    # Make sure CRS is WGS84 (EPSG:4326 = lon/lat)
    if germany_districts.crs is None:
        germany_districts.set_crs(epsg=4326, inplace=True)
    elif germany_districts.crs.to_epsg() != 4326:
        germany_districts = germany_districts.to_crs(epsg=4326)

    # Load German counties (Kreise)
    germany_counties_path = os.path.join(GEOJSON_FOLDER, "germany_counties.geojson")
    germany_counties = gpd.read_file(germany_counties_path)

    # Make sure CRS is WGS84 (EPSG:4326 = lon/lat)
    if germany_counties.crs is None:
        germany_counties.set_crs(epsg=4326, inplace=True)
    elif germany_counties.crs.to_epsg() != 4326:
        germany_counties = germany_counties.to_crs(epsg=4326)

    # Loop over all results files
    data = {}
    for filename in sorted(os.listdir(DATASETS_FOLDER)):
        if filename.startswith("imprints_batch") and filename.endswith(".jsonl.gz"):
            click.echo(f"Processing file: {filename}")

            # Read file with scores
            file_path = os.path.join(DATASETS_FOLDER, filename)
            llm_file_path = os.path.join(llm_results_path, filename)
            geocoded_file_path = os.path.join(geocoded_results_path, filename)
            with gzip.open(
                file_path,
                "rt",
                encoding="UTF-8",
            ) as file, gzip.open(
                llm_file_path,
                "rt",
                encoding="UTF-8",
            ) as llm_file, gzip.open(
                geocoded_file_path,
                "rt",
                encoding="UTF-8",
            ) as geocoded_file:
                for line, llm_line, geocoded_line in tqdm(
                    zip(file, llm_file, geocoded_file),
                ):
                    try:
                        record = json.loads(line)
                        llm_record = json.loads(llm_line)
                        geocoded_record = json.loads(geocoded_line)

                        host = record["host"]
                        if host in data:
                            click.echo(f"Duplicate host found: {host}")
                            continue

                        # Remove invalid pages
                        main_content = record["main"].get("main_content")
                        if main_content is None or len(main_content.strip()) < 5:
                            continue

                        # Shorten main content to first 500k characters
                        if main_content and len(main_content) > 500_000:
                            click.echo(
                                f"Truncating main content for host {host} from {len(main_content):,} to 500,000 characters"
                            )
                            record["main"]["main_content"] = main_content[:500_000]

                        # Extract topic
                        topic = llm_record.get("topic", {"thema": None})["thema"]
                        if topic:
                            record["topic"] = topic

                        address = llm_record.get("address")
                        if has_address(address):
                            record["address"] = address

                        coords = geocoded_record.get("coords")
                        if coords:
                            longitude = coords["longitude"]
                            latitude = coords["latitude"]

                            # Check against country polygons
                            pt = Point(longitude, latitude)

                            # Find the country that contains the point
                            mask = eu_countries.contains(pt)
                            hit = eu_countries[mask]

                            country_name = "None"
                            if not hit.empty:
                                country_name = hit.iloc[0]["NAME"]

                            state_name = country_name
                            district_name = country_name
                            county_name = country_name

                            if country_name == "Germany":
                                # Find the state that contains the point
                                mask = germany_states.contains(pt)
                                hit = germany_states[mask]

                                if not hit.empty:
                                    state_name = hit.iloc[0]["gen"]

                                district_name = state_name
                                county_name = state_name

                                # Find the district that contains the point
                                mask = germany_districts.contains(pt)
                                hit = germany_districts[mask]

                                if not hit.empty:
                                    district_name = hit.iloc[0]["gen"]

                                county_name = district_name

                                # Find the county that contains the point
                                mask = germany_counties.contains(pt)
                                hit = germany_counties[mask]

                                if not hit.empty:
                                    county_name = hit.iloc[0]["gen"]

                                if county_name.endswith(", Landkreis"):
                                    county_name = county_name[:-11].strip()
                                    county_name = "Landkreis " + county_name

                            record["coords"] = coords
                            record["region"] = {
                                "country": country_name,
                                "state": state_name,
                                "district": district_name,
                                "county": county_name,
                            }

                        data[host] = record

                    except json.JSONDecodeError:
                        click.echo(f"Error decoding JSON: {line}")

            # Test with one file only
            # break

    # Sort data by host
    click.echo("Sorting data by host...")
    start = time.time()
    hosts = list(data.keys())
    hosts.sort()
    click.echo(f"Sorting took {time.time() - start:.2f} seconds")

    # Write merged results
    click.echo("Writing merged results...")
    output_path = os.path.join(RESULTS_FOLDER, model, language, prompt_type, "final")
    os.makedirs(output_path, exist_ok=True)

    batch_size = 1_000_000
    i = 0
    while i < len(hosts):
        output_file_path = os.path.join(
            output_path, f"batch{(i // batch_size):06}.jsonl.gz"
        )
        with gzip.open(
            output_file_path,
            "wt",
            encoding="UTF-8",
        ) as output_file:
            for host in hosts[i : i + batch_size]:
                output_file.write(json.dumps(data[host]) + "\n")
        i += batch_size

    click.echo("Done")
