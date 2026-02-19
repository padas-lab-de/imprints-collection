import gzip
import json
import logging
import os
import random
import re
import threading
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from typing import Any, Dict, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse

import click
import extruct
import requests
from charset_normalizer import from_bytes
from resiliparse.extract.html2text import extract_plain_text
from resiliparse.parse.html import HTMLTree
from tqdm import tqdm

from ic.config import *
from ic.utils.filter_utils import check_url
from ic.parsing.language import identify_language
from ic.parsing.location import process_extruct_result

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de",
}
NUM_WORKERS = 64  # 8
TIMEOUT = 10  # 5
MAX_REDIRECTS = 10
BATCH_SIZE = 100_000
KEYWORDS = ["impressum", "kontakt", "über uns", "datenschutz", "agb"]


# Create enum for crawl status
class CrawlStatus:
    IMPRINT_FOUND = "imprint_found"
    IMPRINT_NOT_FOUND = "imprint_not_found"
    NO_VALID_HTML_TREE = "no_valid_html_tree"
    HOST_NOT_FOUND = "host_not_found"
    FILTERED = "filtered"


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("urllib3").setLevel(logging.ERROR)


def requests_get_with_timeout(
    url: str,
    total_timeout: float,
    connect_read_timeout: Optional[Tuple[float, float]] = (3.0, 10.0),
    **kwargs: Any,
) -> Optional[requests.Response]:
    """
    Robust requests.get with enforced total timeout using a thread pool.

    Parameters:
    - url: The URL to request.
    - total_timeout: Max total time (seconds) for the entire operation.
    - connect_read_timeout: (connect_timeout, read_timeout) tuple passed to requests.get.
    - kwargs: Additional arguments passed to requests.get.

    Returns:
    - requests.Response if successful within timeout.
    - None if timeout or error occurs.
    """

    def _request():
        return requests.get(url, timeout=connect_read_timeout, **kwargs)

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_request)
        return future.result(timeout=total_timeout)
    except TimeoutError:
        logging.debug(f"Request to {url} timed out after {total_timeout} seconds")
        return None
    except Exception as e:
        logging.debug(f"Fetch failed for {url}: {e}")
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def try_fetch(
    url: str, num_redirects: int = MAX_REDIRECTS
) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to fetch the URL with a maximum number of redirects. Returns the final URL and the HTML content if successful, otherwise None.

    Parameters:
    - url: The URL to fetch.
    - num_redirects: Maximum number of redirects to follow.

    Returns:
    - Tuple containing the final URL and HTML content if successful, otherwise (None, None).
    """
    if num_redirects <= 0:
        logging.debug(f"Max redirects reached for {url}")
        return None, None

    resp = requests_get_with_timeout(
        url,
        TIMEOUT * 2,
        connect_read_timeout=(3.0, 10.0),
        headers=HEADERS,
        allow_redirects=False,
    )
    if resp is None:
        return None, None
    if resp.status_code == 200 and resp.content:
        # Detect encoding with charset_normalizer
        detection = from_bytes(resp.content).best()
        text = str(detection)
        return url, text.strip()
    if 300 <= resp.status_code < 400 and resp.headers.get("Location"):
        logging.debug(f"Redirected {url} to {resp.headers.get('Location')}")
        abs_url = urljoin(url, resp.headers.get("Location"))
        return try_fetch(abs_url, num_redirects - 1)
    return None, None


def process_host(
    host: str,
    output_file: Any,
    output_lock: threading.Lock,
    pbar: tqdm,
    hosts_dict: dict,
) -> str:
    """
    Fetch the base URL for a given host using both HTTP and HTTPS schemes.
    If successful, write the result to the output file.

    Parameters:
    - host: The host to fetch.
    - output_file: The file to write the results to.

    Returns:
    - Message indicating success or failure.
    """
    assert (
        output_file is not None
    ), "Output file must be initialized before processing hosts"
    assert (
        output_lock is not None
    ), "Output lock must be initialized before processing hosts"
    assert pbar is not None, "Progress bar must be initialized before processing hosts"

    hosts_dict[host]["start_time"] = time.time()

    if not check_url(host, is_host=True):
        logging.debug(f"Skipping host {host} due to filter: {filter}")

        # Update progress bar
        pbar.update(1)

        hosts_dict[host]["end_time"] = time.time()

        return CrawlStatus.FILTERED

    status = CrawlStatus.HOST_NOT_FOUND
    for scheme in ["https://", "http://"]:
        base_url = scheme + host
        base_url, html = try_fetch(base_url)
        if base_url and html:
            # Skip if the new base URL is from the filter list
            if not check_url(base_url):
                status = CrawlStatus.FILTERED
                continue

            tree, parse_result = parse_html(html)

            # Update progress bar
            pbar.update(1)

            hosts_dict[host]["end_time"] = time.time()

            if not tree or not tree.body:
                # logging.warning(f"No valid HTML tree for {base_url} ({host})")
                return CrawlStatus.NO_VALID_HTML_TREE

            result = {
                "host": host,
                "main": {"url": base_url},
            }
            result["main"].update(parse_result)

            keyword_links, external_hosts = discover_links(tree.body, base_url, host)

            # Append external hosts to a file called discovered_external_hosts.txt
            if external_hosts:
                with open(
                    os.path.join(DATASETS_FOLDER, "discovered_external_hosts.txt"),
                    "a",
                    encoding="UTF-8",
                ) as ext_file:
                    for ext_host in external_hosts:
                        ext_file.write(ext_host + "\n")

            includes_imprint = False
            for keyword, url in keyword_links.items():
                if url:
                    sub_url, sub_html = try_fetch(url)
                    if sub_html:
                        _, parse_result = parse_html(sub_html)

                        if (
                            parse_result
                            and int(parse_result.get("content_length", 0)) > 0
                        ):
                            result[keyword] = {"url": sub_url}
                            result[keyword].update(parse_result)

                            if keyword == "impressum":
                                includes_imprint = True

            with output_lock:
                output_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                output_file.flush()

            if includes_imprint:
                return CrawlStatus.IMPRINT_FOUND
            else:
                return CrawlStatus.IMPRINT_NOT_FOUND

    logging.debug(f"Failed to fetch {host} with both HTTP schemes")

    # Update progress bar
    pbar.update(1)

    hosts_dict[host]["end_time"] = time.time()

    return status


def apply_extruct_extractors(html: str) -> Dict:
    try:
        # Turn the resulting nested dictionary into a string for compatability with arrow
        extruct_result = extruct.extract(
            html, syntaxes=["json-ld", "microdata", "opengraph"]
        )
        return {
            k.replace("-", "_"): (v if len(v) > 0 else None)
            for k, v in extruct_result.items()
        }
    except:
        return {"json_ld": None, "microdata": None, "opengraph": None}


def parse_html(html: str) -> Tuple[Optional[HTMLTree], Optional[Dict[str, Union[str, int]]]]:
    """
    Parse the HTML content and extract the main text content.

    Parameters:
    - html: The HTML content to parse.

    Returns:
    - Tuple containing the HTML tree and the extracted plain text.
    """
    try:
        tree = HTMLTree.parse(html)

        # Parse the html
        tree = HTMLTree.parse(html)
        main_content = extract_plain_text(
            tree, preserve_formatting=True, main_content=True
        )

        # Get content from meta tags
        def _parse_meta_tag_content(meta_node):
            content = meta_node.getattr("content") or meta_node.text
            if content is None:
                return None
            else:
                return None if len(content) == 0 else content

        # Get the nodes with meta content
        title_node = tree.head.query_selector("[name=Title i]")
        if title_node is None:
            title_nodes = tree.head.get_elements_by_tag_name("title")
            title_node = title_nodes[0] if len(title_nodes) > 0 else None
        desc_node = tree.head.query_selector("[name=Description i]")
        keyword_node = tree.head.query_selector("[name=Keywords i]")
        author_node = tree.head.query_selector("[name=Author i]")

        # Create the result
        result = {}
        for key, node in [
            ("title", title_node),
            ("description", desc_node),
            ("keywords", keyword_node),
            ("author", author_node),
        ]:
            result[key] = _parse_meta_tag_content(node) if node is not None else None
        result["main_content"] = main_content
        result["content_length"] = len(main_content)
        result["content_language"] = identify_language(
            tree, result["description"], main_content
        )

        # Extract address from structured data (JSON-LD, etc.)
        extruct_result = apply_extruct_extractors(html)
        list_address, list_coords = process_extruct_result(**extruct_result)
        results_address = [
            dict(t)
            for t in {
                tuple(sorted(d.items())) for d in list_address if d and len(d) > 0
            }
        ]
        results_coords = [
            dict(t)
            for t in {tuple(sorted(d.items())) for d in list_coords if d and len(d) > 0}
        ]
        result["address"] = results_address
        result["coords"] = results_coords

        return tree, result

    except Exception as e:
        logging.warning(f"HTML extraction failed: {e}")
        return None, None


def discover_links(
    body: HTMLTree, base_url: str, base_host: str
) -> Tuple[Dict[str, Optional[str]], Set[str]]:
    """
    Discover links in the HTML body and filter them based on keywords.

    Parameters:
    - body: The HTML body to search for links.
    - base_url: The base URL to resolve relative links.

    Returns:
    - Dictionary mapping keywords to the shortest discovered link for that keyword.
    """
    discovered_links = {}
    try:
        for elem in body.get_elements_by_tag_name("a"):
            href = elem.getattr("href")
            anchor_text = (elem.text or "").strip().lower()

            # Skip if link is empty or not a valid URL
            if not href:
                continue

            abs_url = urljoin(base_url, href, allow_fragments=False)
            parsed_url = urlparse(abs_url)
            host = parsed_url.netloc.lower()

            # Skip if link is empty
            if not parsed_url.path:
                continue

            discovered_links[parsed_url.path] = (anchor_text, abs_url, host)

    except Exception as e:
        logging.debug(f"Error parsing {base_url}: {e}")
        return {}, set()

    keyword_links = {}
    external_hosts = set()

    for link, (anchor_text, abs_url, host) in discovered_links.items():
        if not host:
            continue

        host = host.lower().strip()
        if not check_url(host, is_host=True):
            continue

        for keyword in KEYWORDS:
            if keyword in link.lower() or keyword in anchor_text.lower():
                # Store the shortest link for each keyword
                if keyword not in keyword_links or len(abs_url) < len(
                    keyword_links[keyword]
                ):
                    keyword_links[keyword] = abs_url

        if host != base_host:
            external_hosts.add(host)

    return keyword_links, external_hosts


@click.command()
@click.argument("input_file_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("batch_size", default=BATCH_SIZE, type=int)
@click.argument("start_batch", default=0, type=int)
@click.argument("end_batch", default=-1, type=int)
@click.argument("num_workers", default=NUM_WORKERS, type=int)
def fetch(input_file_path: str, start_batch: int, end_batch: int, batch_size: int, num_workers: int) -> None:
    """
    Fetch all relevant pages for the hosts included in the input file and extract imprint information.

    Parameters:
    - input_file_path: The path to the file containing the list of hosts to crawl.
    - start_batch: The batch number to start processing from.
    - end_batch: The batch number to stop processing at (-1 for all).
    - batch_size: The number of hosts to process in each batch.
    - num_workers: The number of worker threads to use for processing.
    """
    with open(input_file_path, "r", encoding="UTF-8") as f:
        hosts = [line.strip() for line in f if line.strip()]

    # Shuffle hosts for better load balancing
    random.seed(42)
    random.shuffle(hosts)

    total_batches = (len(hosts) + batch_size - 1) // batch_size
    logging.info(f"Total hosts: {len(hosts)} across {total_batches} batches")

    for batch_id in range(start_batch, total_batches):
        if end_batch != -1 and batch_id > end_batch:
            break

        start = batch_id * batch_size
        end = min(start + batch_size, len(hosts))
        batch_hosts = [host.strip() for host in hosts[start:end]]

        logging.info(f"Processing batch {batch_id} ({len(batch_hosts)} hosts)")

        # Initialize output file and lock for the batch
        output_path = os.path.join(
            DATASETS_FOLDER, f"imprints_batch{batch_id:06d}.jsonl.gz"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_file = gzip.open(output_path, "wt", encoding="UTF-8")
        output_lock = threading.Lock()

        # Initialize progress bar
        pbar = tqdm(total=len(batch_hosts), desc=f"Processing batch {batch_id}")

        # DEBUGGING
        hosts_dict = defaultdict(dict)
        for host in batch_hosts:
            hosts_dict[host] = {"start_time": None, "end_time": None}

        # Start executor service
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Initialize counter for processed hosts
            counter = {}

            # Wait for all tasks to complete
            futures = {
                executor.submit(
                    process_host, host, output_file, output_lock, pbar, hosts_dict
                ): host
                for host in batch_hosts
                if host is not None
            }
            for future in as_completed(futures):
                host = futures[future]
                try:
                    status = future.result(timeout=60 * 60 * 2)  # 2 hours timeout
                    counter[status] = counter.get(status, 0) + 1
                except TimeoutError:
                    logging.warning(f"Crawl of {host} timed out after 1 hour")
                except Exception as e:
                    logging.error(f"Error processing {host}: {e}")
                    traceback.print_exc()

            # Shutdown the executor
            executor.shutdown(wait=True)

        # Close the output file and progress bar
        pbar.close()
        output_file.flush()
        output_file.close()

        # Log statistics for the batch
        logging.info(f"Batch {batch_id} statistics:")
        total = sum(counter.values())
        for status, count in counter.items():
            logging.info(f"  {status}: {count} ({count / total:.2%})")
        logging.info(f"  Total processed: {total}")
        # break

    logging.info("Done")

    # Kill the process to avoid clean up of dangling threads
    os._exit(0)


if __name__ == "__main__":
    print("Starting test...")

    # Initialize output file and lock for test batch
    output_path = os.path.join(TEMP_FOLDER, "test.jsonl.gz")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_file = gzip.open(output_path, "wt", encoding="UTF-8")
    output_lock = threading.Lock()

    # Initialize progress bar
    pbar = tqdm(total=1, desc="Processing test batch")

    hosts_dict = defaultdict(dict)

    process_host(
        "www.bestattungen-d-schulz.de", output_file, output_lock, pbar, hosts_dict
    )

    # Allow some time for the fetcher to start
    time.sleep(2)

    pbar.close()
    output_file.flush()
    output_file.close()

    print("Hosts dict:")
    for host in sorted(hosts_dict):
        infos = hosts_dict[host]
        print(f"{host:30} - {infos}")

    print("Completed test")

    # Kill the process to avoid clean up of dangling threads
    os._exit(0)
