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
from typing import Any, Dict, List, Optional, Set, Tuple, Union
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
RETRY_PAUSE = 1.0  # seconds before retrying a timed-out or 5xx request
BATCH_SIZE = 100_000
KEYWORDS = ["impressum", "kontakt", "über uns", "datenschutz", "agb"]
# Terms that identify an imprint link, in priority order ("impressum" first)
IMPRINT_KEYWORDS = [
    "impressum",
    "imprint",
    "legal notice",
    "rechtliche hinweise",
    "rechtliches",
    "anbieterkennzeichnung",
]
MAX_IMPRINT_CANDIDATES = 5
# Paths probed when the landing page has no imprint link
IMPRINT_PROBE_PATHS = ["/impressum", "/impressum.html", "/imprint"]
# A probed page only counts as imprint if its text matches this pattern
IMPRINT_TEXT_PATTERN = re.compile(r"impressum|angaben gemäß|§\s*5\s*(tmg|ddg)", re.I)


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
    retry: bool = False,
    **kwargs: Any,
) -> Optional[requests.Response]:
    """
    Robust requests.get with enforced total timeout using a thread pool.

    Parameters:
    - url: The URL to request.
    - total_timeout: Max total time (seconds) for the entire operation.
    - connect_read_timeout: (connect_timeout, read_timeout) tuple passed to requests.get.
    - retry: Retry once if the request timed out.
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
    except (TimeoutError, requests.exceptions.Timeout):
        logging.debug(f"Request to {url} timed out after {total_timeout} seconds")
        if retry:
            time.sleep(RETRY_PAUSE)
            return requests_get_with_timeout(
                url, total_timeout, connect_read_timeout, retry=False, **kwargs
            )
        return None
    except Exception as e:
        logging.debug(f"Fetch failed for {url}: {e}")
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def try_fetch(
    url: str, num_redirects: int = MAX_REDIRECTS, retry: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to fetch the URL with a maximum number of redirects. Returns the final URL and the HTML content if successful, otherwise None.

    Parameters:
    - url: The URL to fetch.
    - num_redirects: Maximum number of redirects to follow.
    - retry: Retry once on timeout or HTTP 5xx.

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
        retry=retry,
        headers=HEADERS,
        allow_redirects=False,
    )
    if resp is not None and resp.status_code >= 500 and retry:
        logging.debug(f"Server error {resp.status_code} for {url}, retrying")
        time.sleep(RETRY_PAUSE)
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
        return try_fetch(abs_url, num_redirects - 1, retry)
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
        base_url, html = try_fetch(base_url, retry=True)
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

            keyword_links, external_hosts = discover_links(
                tree.body, base_url, host, base_href=get_base_href(tree)
            )

            # Append external hosts to a file called discovered_external_hosts.txt
            if external_hosts:
                with open(
                    os.path.join(DATASETS_FOLDER, "discovered_external_hosts.txt"),
                    "a",
                    encoding="UTF-8",
                ) as ext_file:
                    for ext_host in external_hosts:
                        ext_file.write(ext_host + "\n")

            for keyword, candidates in keyword_links.items():
                if keyword == "impressum":
                    continue
                # Other pages: only the shortest link, no fallback
                for url, _ in candidates[:1]:
                    sub_url, sub_html = try_fetch(url)
                    if sub_html:
                        _, parse_result = parse_html(sub_html)

                        if (
                            parse_result
                            and int(parse_result.get("content_length", 0)) > 0
                        ):
                            result[keyword] = {"url": sub_url}
                            result[keyword].update(parse_result)

            imprint = find_imprint(
                base_url,
                result["main"].get("main_content", ""),
                keyword_links.get("impressum", []),
            )
            includes_imprint = imprint is not None
            if imprint:
                result["impressum"] = imprint

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


def fetch_imprint_page(
    url: str,
) -> Tuple[Optional[str], Optional[Dict[str, Union[str, int]]], bool]:
    """
    Fetch a candidate imprint page. If the main-content extraction is empty, the
    page is re-extracted with main_content=False and kept if the body text is not empty.

    Returns:
    - Tuple (final url, parse result, used_fallback_extraction); parse result is None
      if the page is unusable.
    """
    sub_url, sub_html = try_fetch(url, retry=True)
    if not sub_html:
        return None, None, False
    _, parse_result = parse_html(sub_html)
    if not parse_result:
        return None, None, False
    if int(parse_result.get("content_length", 0)) > 0:
        return sub_url, parse_result, False
    # Main-content extraction found nothing, try the full body text
    _, full_result = parse_html(sub_html, main_content=False)
    if full_result and int(full_result.get("content_length", 0)) > 0:
        return sub_url, full_result, True
    return None, None, False


def find_imprint(
    base_url: str, landing_text: str, candidates: List[Tuple[str, str]]
) -> Optional[Dict[str, Any]]:
    """
    Find the imprint page of a host: try the discovered link candidates in order,
    then probe common paths if there was no candidate at all.

    Parameters:
    - base_url: Final URL of the landing page.
    - landing_text: Extracted text of the landing page.
    - candidates: Ordered (url, matched keyword) imprint candidates.

    Returns:
    - Imprint record with the fields of parse_html plus "url", "found_by"
      ("link" or "probe"), "found_keyword" (matched keyword or probed path),
      "candidate_rank" and "fallback_extraction", or None.
    """
    for rank, (url, keyword) in enumerate(candidates[:MAX_IMPRINT_CANDIDATES]):
        sub_url, parse_result, fallback = fetch_imprint_page(url)
        if parse_result:
            return {
                "url": sub_url,
                **parse_result,
                "found_by": "link",
                "found_keyword": keyword,
                "candidate_rank": rank,
                "fallback_extraction": fallback,
            }

    if candidates:
        return None

    # No imprint link: probe common paths on the final host
    parsed = urlparse(base_url)
    for path in IMPRINT_PROBE_PATHS:
        sub_url, parse_result, fallback = fetch_imprint_page(
            f"{parsed.scheme}://{parsed.netloc}{path}"
        )
        if not parse_result:
            continue
        text = parse_result.get("main_content", "")
        if text.strip() == (landing_text or "").strip():
            continue
        if not IMPRINT_TEXT_PATTERN.search(text):
            continue
        return {
            "url": sub_url,
            **parse_result,
            "found_by": "probe",
            "found_keyword": path,
            "candidate_rank": 0,
            "fallback_extraction": fallback,
        }
    return None


def get_base_href(tree: HTMLTree) -> Optional[str]:
    """Return the href of the first <base> element of the document, if any."""
    try:
        for node in tree.document.get_elements_by_tag_name("base"):
            href = node.getattr("href")
            if href and href.strip():
                return href.strip()
    except Exception as e:
        logging.debug(f"Error reading base href: {e}")
    return None


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


def parse_html(
    html: str, main_content: bool = True
) -> Tuple[Optional[HTMLTree], Optional[Dict[str, Union[str, int]]]]:
    """
    Parse the HTML content and extract the main text content.

    Parameters:
    - html: The HTML content to parse.
    - main_content: Extract only the main content (True) or the whole body text (False).

    Returns:
    - Tuple containing the HTML tree and the extracted plain text.
    """
    try:
        tree = HTMLTree.parse(html)

        # Parse the html
        tree = HTMLTree.parse(html)
        main_text = extract_plain_text(
            tree, preserve_formatting=True, main_content=main_content
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
        result["main_content"] = main_text
        result["content_length"] = len(main_text)
        result["content_language"] = identify_language(
            tree, result["description"], main_text
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


def get_anchor_text(elem: Any) -> str:
    """
    Return the lower-cased label of an anchor: its own text, the alt text of
    contained images, and its title and aria-label attributes.
    """
    parts = [
        elem.text or "",
        elem.getattr("title") or "",
        elem.getattr("aria-label") or "",
    ]
    try:
        for img in elem.get_elements_by_tag_name("img"):
            parts.append(img.getattr("alt") or "")
    except Exception:
        pass
    return " ".join(p.strip() for p in parts if p and p.strip()).lower()


def discover_links(
    body: HTMLTree,
    base_url: str,
    base_host: str,
    base_href: Optional[str] = None,
) -> Tuple[Dict[str, List[Tuple[str, str]]], Set[str]]:
    """
    Discover links in the HTML body and filter them based on keywords.

    Parameters:
    - body: The HTML body to search for links.
    - base_url: The base URL to resolve relative links.
    - base_host: Host of the page, used to prefer own-host imprint links.
    - base_href: Value of the <base href> element, if any; relative links are
      resolved against it.

    Returns:
    - Tuple (keyword_links, external_hosts). keyword_links maps each keyword to an
      ordered list of (url, matched term) candidates: for "impressum" (all
      IMPRINT_KEYWORDS) by keyword priority, own host first, then shortest URL;
      for the other keywords by URL length.
    """
    resolve_base = urljoin(base_url, base_href) if base_href else base_url

    # Keep every link as (url, anchor text); the same URL may appear several times
    discovered_links: Dict[str, str] = {}
    try:
        for elem in body.get_elements_by_tag_name("a"):
            href = elem.getattr("href")
            anchor_text = get_anchor_text(elem)

            # Skip if link is empty or not a valid URL
            if not href:
                continue

            abs_url = urljoin(resolve_base, href.strip(), allow_fragments=False)
            parsed_url = urlparse(abs_url)

            # Skip if link is empty
            if not parsed_url.path:
                continue

            discovered_links[abs_url] = (
                discovered_links.get(abs_url, "") + " " + anchor_text
            ).strip()

    except Exception as e:
        logging.debug(f"Error parsing {base_url}: {e}")
        return {}, set()

    # keyword -> list of (sort key, url, matched term)
    matches: Dict[str, List[Tuple[Tuple, str, str]]] = defaultdict(list)
    external_hosts = set()

    for abs_url, anchor_text in discovered_links.items():
        parsed_url = urlparse(abs_url)
        host = parsed_url.netloc.lower().strip()
        if not host:
            continue
        if not check_url(host, is_host=True):
            continue

        # Match against path + query and the anchor label
        target = (parsed_url.path + "?" + parsed_url.query).lower()

        for keyword in KEYWORDS:
            terms = IMPRINT_KEYWORDS if keyword == "impressum" else [keyword]
            for priority, term in enumerate(terms):
                if term in target or term in anchor_text:
                    if keyword == "impressum":
                        sort_key = (priority, host != base_host, len(abs_url))
                    else:
                        sort_key = (len(abs_url),)
                    matches[keyword].append((sort_key, abs_url, term))
                    break

        if host != base_host:
            external_hosts.add(host)

    keyword_links = {
        keyword: [(abs_url, term) for _, abs_url, term in sorted(found)]
        for keyword, found in matches.items()
    }

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
