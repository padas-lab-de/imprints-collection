"""
E7: download the homepages of the gold-standard hosts with the production logic
(ic.cli.fetch: try_fetch with UA/timeouts/redirects, parse_html with resiliparse
main-content extraction), without the link discovery.

Usage: python scripts/gold_homepages.py GOLD OUT [WORKERS<=16]
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

from ic.cli.fetch import parse_html, try_fetch
from ic.utils.filter_utils import check_url


def homepage(item: dict) -> dict:
    host = urlparse(item["url"]).netloc.lower()
    record = {
        "id": item["id"],
        "host": host,
        "url": None,
        "status": "host_not_found",
        "title": None,
        "description": None,
        "main_content": "",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not check_url(host, is_host=True):
        record["status"] = "filtered"
        return record
    for scheme in ("https://", "http://"):
        url, html = try_fetch(scheme + host)
        if not (url and html):
            continue
        record["url"] = url
        if not check_url(url):
            record["status"] = "filtered"
            continue
        tree, parsed = parse_html(html)
        if not tree or not tree.body or not parsed:
            record["status"] = "no_valid_html_tree"
            return record
        record["title"] = parsed["title"]
        record["description"] = parsed["description"]
        record["main_content"] = parsed["main_content"]
        record["status"] = "ok" if parsed["main_content"].strip() else "empty_content"
        return record
    return record


def main():
    gold_path, out_path = sys.argv[1], sys.argv[2]
    workers = min(int(sys.argv[3]) if len(sys.argv) > 3 else 16, 16)
    with open(gold_path, encoding="UTF-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    with ThreadPoolExecutor(max_workers=workers) as ex, open(
        out_path, "w", encoding="UTF-8"
    ) as out:
        for i, rec in enumerate(ex.map(homepage, items), 1):
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            if i % 100 == 0:
                print(i, flush=True)


if __name__ == "__main__":
    main()
