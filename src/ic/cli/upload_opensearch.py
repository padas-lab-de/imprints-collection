import gzip
import json
import logging
import os

import click
import dotenv
import geopandas as gpd
from opensearchpy import OpenSearch
from shapely.geometry import Point
from tqdm import tqdm

from ic.config import *

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("opensearchpy").setLevel(logging.ERROR)


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
@click.argument("index_name", type=str)
def upload_opensearch(model: str, language: str, prompt_type: str, index_name: str):
    """
    Upload the imprint files to OpenSearch.
    """
    dotenv.load_dotenv()

    host = os.getenv("OPENSEARCH_HOST")
    user = os.getenv("OPENSEARCH_USER")
    password = os.getenv("OPENSEARCH_PASSWORD")

    # Initialize OpenSearch client
    client = OpenSearch(
        hosts=[host],
        http_auth=(user, password),
        use_ssl=True,
    )

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

    final_results_path = os.path.join(
        RESULTS_FOLDER, model, language, prompt_type, "final"
    )
    if not os.path.exists(final_results_path):
        click.echo(f"Geocoded results path does not exist: {final_results_path}")
        return

    for filename in sorted(os.listdir(final_results_path)):
        click.echo(f"Processing file: {filename}")

        file_path = os.path.join(final_results_path, filename)
        with gzip.open(file_path, "rt", encoding="UTF-8") as file:
            for line in tqdm(file):
                entry = json.loads(line)

                host = entry["host"]
                address = entry.get("address")
                coords = entry.get("coords")

                body = {
                    "host": host,
                    "url": entry["main"]["url"],
                    "title": entry["main"].get("title"),
                    "description": entry["main"].get("description"),
                    "keywords": entry["main"].get("keywords"),
                    "main_content": entry["main"].get("main_content"),
                    "content_language": entry["main"].get("content_language"),
                    "topic": entry.get("topic", {"thema": None})["thema"],
                }

                if address:
                    body["address"] = address

                if coords:
                    longitude = coords["longitude"]
                    latitude = coords["latitude"]

                    body["coords"] = {
                        "longitude": longitude,
                        "latitude": latitude,
                    }

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

                    body["region"] = {
                        "country": country_name,
                        "state": state_name,
                        "district": district_name,
                        "county": county_name,
                    }

                # Upload entry to OpenSearch
                client.index(
                    index=index_name,
                    body=body,
                    id=host,  # Use host as document ID to avoid duplicates
                )

                # break

        # break

    click.echo("Done")
