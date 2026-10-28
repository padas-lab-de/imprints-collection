#!/usr/bin/env python3
"""E19 reshard (D25 option B): split the hosts of the frozen recovery input that have no final status yet.

Inputs: recovery_input.txt (one host per line, as frozen by run.sh) and the directory with the
fetch_status_batch*.tsv of the running/stopped pass. Output: remaining_shard0.txt ... remaining_shard{N-1}.txt
(disjoint, input order kept inside a shard) and one summary line on stdout.

Final status: ic fetch resumes by host (src/ic/utils/fetch_state.py read_done_hosts): ANY complete status
row (line ends with a newline, 9 columns) counts as done, whatever its status, host_not_found and error
included; those hosts are not retried on resume. "deferred" (429/503, retried after the backoff) is only an
in-memory counter in ic fetch (src/ic/cli/fetch.py, counter["deferred"], and RetryLater -> sched.retry_later):
a deferred host gets no status row until its final attempt, so it is "remaining". If a row with status
"deferred" ever existed, it is treated as not final here (never produced by the current ic fetch).

Shard of a host: int(sha1(host)[:8], 16) % N (stable across runs and machines).
Files are only read (status dir, input); the output dir is created.
"""
import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect import read_rows  # noqa: E402

NOT_FINAL = {"deferred"}


def shard_of(host, shards):
    """Stable shard index of a host (hashlib, not hash(): that one changes per process)."""
    return int(hashlib.sha1(host.encode("utf-8")).hexdigest()[:8], 16) % shards


def read_hosts(path):
    """Hosts of a list file in order, blank lines and duplicates dropped."""
    with open(path, encoding="utf-8") as f:
        return list(dict.fromkeys(l.strip() for l in f if l.strip()))


def final_hosts(status_dir):
    """Hosts with a final status row in any fetch_status_batch*.tsv of the directory."""
    done = set()
    for p in sorted(Path(status_dir).glob("fetch_status_batch*.tsv")):
        for r in read_rows(p):
            if r["status"] not in NOT_FINAL:
                done.add(r["host"])
    return done


def reshard(hosts, done, shards):
    """(remaining hosts, [hosts per shard])."""
    remaining = [h for h in hosts if h not in done]
    parts = [[] for _ in range(shards)]
    for h in remaining:
        parts[shard_of(h, shards)].append(h)
    return remaining, parts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="frozen recovery_input.txt")
    ap.add_argument("--status-dir", required=True, help="dir with fetch_status_batch*.tsv")
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    if a.shards < 1:
        ap.error("--shards must be >= 1")

    hosts = read_hosts(a.input)
    done = final_hosts(a.status_dir)
    remaining, parts = reshard(hosts, done, a.shards)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, part in enumerate(parts):
        (out / f"remaining_shard{i}.txt").write_text("".join(h + "\n" for h in part))
    n_done = len(hosts) - len(remaining)
    print(
        f"total {len(hosts)} done {n_done} remaining {len(remaining)} shards "
        + " ".join(f"{i}:{len(p)}" for i, p in enumerate(parts))
    )


if __name__ == "__main__":
    sys.exit(main())
