"""E52: one candidate x run over the gold inputs, with the E50 runner and prompts unchanged.

    python3 -I scripts/E52/run.py --http-log <file> -- <scripts/E50/e50_run.py arguments>

Calls scripts/E50/e50_run.py main() with the given arguments. Adds only a log of HTTP errors from the endpoint
(one line per failed attempt: UTC time, status code, path; never the endpoint, the key or the body), so that
429 / 503 answers that the E49 client retries (5 attempts, 5-25 s back-off) are visible. The request bodies,
retries and back-off are those of scripts/E49/client.py. Prints the start and end time (UTC).
"""

from __future__ import annotations

import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E50"))
import e50_run  # noqa: E402

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wrap_urlopen(log_path: str):
    orig = urllib.request.urlopen

    def urlopen(req, *args, **kw):
        try:
            return orig(req, *args, **kw)
        except urllib.error.HTTPError as e:
            path = (
                urllib.parse.urlparse(req.full_url).path.rsplit("/", 1)[-1]
                if hasattr(req, "full_url")
                else ""
            )
            with _LOCK, open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{_now()}\tHTTP {e.code}\t{path}\n")
            raise
        except Exception as e:  # timeouts, connection errors
            with _LOCK, open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{_now()}\t{type(e).__name__}\t\n")
            raise

    urllib.request.urlopen = urlopen


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 3 or args[0] != "--http-log" or args[2] != "--":
        sys.exit("usage: run.py --http-log FILE -- <e50_run.py arguments>")
    wrap_urlopen(args[1])
    sys.argv = ["e50_run.py"] + args[3:]
    print(f"start_utc {_now()}", flush=True)
    e50_run.main()
    print(f"end_utc {_now()}", flush=True)


if __name__ == "__main__":
    main()
