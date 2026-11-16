"""
Crash-safe bookkeeping for `ic fetch`: a per-batch status log (one TSV line per
finished host) and recovery of a batch output file that was cut off by a crash.
"""

import gzip
import json
import os
import zlib
from typing import Iterator, Set

STATUS_COLUMNS = [
    "host",
    "status",
    "detail",
    "provider",
    "attempts",
    "requests",
    "throttled",
    "seconds",
    "end_time",
]


def read_done_hosts(status_path: str) -> Set[str]:
    """Hosts with a complete line in the status log (a cut-off last line is ignored)."""
    done: Set[str] = set()
    if not os.path.exists(status_path):
        return done
    with open(status_path, "r", encoding="UTF-8", errors="replace") as f:
        for line in f:
            if not line.endswith("\n"):
                break
            fields = line.rstrip("\n").split("\t")
            if len(fields) == len(STATUS_COLUMNS) and fields[0] != "host":
                done.add(fields[0])
    return done


def iter_gzip_lines_tolerant(path: str, chunk_size: int = 1 << 20) -> Iterator[str]:
    """
    Yield the complete lines of a (possibly multi-member) gzip file, stopping
    silently at a truncated or corrupt end, as left by a killed writer.
    """
    decomp = zlib.decompressobj(16 + zlib.MAX_WBITS)
    buf = b""
    with open(path, "rb") as f:
        while True:
            raw = f.read(chunk_size)
            if not raw:
                break
            while raw:
                try:
                    piece = decomp.decompress(raw)
                except zlib.error:
                    # Corrupt data: buf holds no complete line any more
                    return
                buf += piece
                if b"\n" in buf:
                    *lines, buf = buf.split(b"\n")
                    for line in lines:
                        yield line.decode("UTF-8", errors="replace")
                if decomp.eof:
                    raw = decomp.unused_data
                    decomp = zlib.decompressobj(16 + zlib.MAX_WBITS)
                else:
                    raw = b""
    # A last line without newline is incomplete and dropped


def salvage_batch_output(output_path: str, done_hosts: Set[str]) -> int:
    """
    Rewrite a batch output file so that it is a valid gzip file holding only the
    records of hosts in `done_hosts` (records written after the last status line
    are dropped; their hosts are fetched again). Returns the number of records kept.
    """
    if not os.path.exists(output_path):
        return 0
    tmp_path = output_path + ".salvage"
    kept = 0
    seen: Set[str] = set()
    with gzip.open(tmp_path, "wt", encoding="UTF-8") as out:
        for line in iter_gzip_lines_tolerant(output_path):
            try:
                host = json.loads(line).get("host")
            except (json.JSONDecodeError, AttributeError):
                continue
            if host in done_hosts and host not in seen:
                seen.add(host)
                out.write(line + "\n")
                kept += 1
    os.replace(tmp_path, output_path)
    return kept
