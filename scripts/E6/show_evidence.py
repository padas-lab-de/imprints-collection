"""Show which evidence pattern matches for the given hosts in an imprint dataset."""

import gzip
import json
import sys

from ic.utils.imprint_utils import _EVIDENCE_RE, _POSTCODE_RE

R = "/home/dinzinger/GitHub/imprints-collection/"
path = R + "datasets/E6/random20k/imprints_batch000000.jsonl.gz"
hosts = set(sys.argv[1:])
with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["host"] in hosts and "impressum" in r:
            t = r["impressum"]["main_content"]
            for rx in (_EVIDENCE_RE, _POSTCODE_RE):
                m = rx.search(t)
                if m:
                    print(r["host"], repr(t[max(0, m.start() - 40) : m.end() + 40]))
