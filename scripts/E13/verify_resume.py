"""E13 resume test check: status logs vs. outputs vs. input hosts.

Usage: verify_resume.py RUN_DIR HOSTS_FILE [--strict]
--strict additionally reads every output with the plain gzip module (fails on a cut-off file).
"""

import collections
import glob
import gzip
import json
import sys

sys.path.insert(0, sys.path[0] + "/../../src")
from ic.utils.fetch_state import iter_gzip_lines_tolerant  # noqa: E402

run_dir, hosts_file = sys.argv[1:3]
strict = "--strict" in sys.argv
hosts = {line.strip() for line in open(hosts_file) if line.strip()}

status = collections.Counter()
logged = []
for path in sorted(glob.glob(f"{run_dir}/fetch_status_batch*.tsv")):
    with open(path) as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9:
                print("cut status line:", path, repr(line[:80]))
                continue
            logged.append(parts[0])
            status[parts[1]] += 1
dups = [h for h, c in collections.Counter(logged).items() if c > 1]
print(f"status lines {len(logged)}, unique {len(set(logged))}, duplicates {len(dups)}, "
      f"input hosts {len(hosts)}, missing {len(hosts - set(logged))}, foreign {len(set(logged) - hosts)}")
print("statuses", dict(status))

records = []
for path in sorted(glob.glob(f"{run_dir}/imprints_batch*.jsonl.gz")):
    reader = (gzip.open(path, "rt") if strict else iter_gzip_lines_tolerant(path))
    n = 0
    for line in reader:
        if isinstance(line, bytes):
            line = line.decode()
        records.append(json.loads(line)["host"] if line.strip() else None)
        n += 1
    print(path.rsplit("/", 1)[1], "records", n, "(strict gzip read ok)" if strict else "(tolerant)")
reachable = status["imprint_found"] + status["imprint_not_found"]  # hosts that write a record
rdups = [h for h, c in collections.Counter(records).items() if c > 1]
print(f"output records {len(records)}, found+not_found in status {reachable}, duplicate records {len(rdups)}, "
      f"records of unlogged hosts {len(set(records) - set(logged))}")
