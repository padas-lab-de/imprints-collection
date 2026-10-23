"""Print the E9 and E6 imprint record summary for hosts (url, route, text head)."""

import gzip
import json
import re
import sys

R = "/home/dinzinger/GitHub/imprints-collection/"
hosts = set(sys.argv[1:])
for ds in ("E6", "E9"):
    with gzip.open(R + f"datasets/{ds}/random20k/imprints_batch000000.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["host"] in hosts:
                i = r.get("impressum")
                if i:
                    print(ds, r["host"], i["url"], i["found_by"], i["found_keyword"], i["fallback_extraction"], i["candidate_rank"])
                    print("    ", re.sub(r"\s+", " ", i["main_content"][:200]))
                else:
                    print(ds, r["host"], "no imprint; main", r["main"]["url"])
