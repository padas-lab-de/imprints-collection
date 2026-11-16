"""Capture step: browser capture of the drawn items (docs/gold_set_design.md, capture section), a thin wrapper of
goldset/capture_lib.py.

On top of capture_lib:
- input: datasets/goldset/phase2/gold_sample.jsonl (one host per line), output: <out>/<host>/
  (normally datasets/goldset/gold, the data folder of the labelling tool);
- Strato hosts are captured (the capture machine is not the crawl machine); the Strato flag stays in meta.json["dns"];
- meta.json gets "experiment", "capture_ip_group" (a free name for the capture machine / IP group),
  "capture_day_utc" and the sample fields.
The `ic fetch` record and its timestamp are added later by goldset/merge_fetch.py.

  PYTHONPATH=src <venv-render>/bin/python goldset/capture.py --sample S --out OUT --ip-group capture1 [--workers 6]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("capture_lib", HERE / "capture_lib.py")
C = importlib.util.module_from_spec(_spec)
sys.modules["capture_lib"] = C
_spec.loader.exec_module(C)

SAMPLE_FIELDS = ("core", "stratum", "fold", "weight")


def load_sample(path: Path, limit: int | None = None) -> list[dict]:
    items = []
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            items.append(
                {
                    "item": None,
                    "host": r["host"],
                    "sample": {k: r.get(k) for k in SAMPLE_FIELDS},
                }
            )
    return items[:limit] if limit else items


def add_sample_meta(rec: dict, item: dict, ip_group: str) -> dict:
    """Provenance fields for meta.json (pure)."""
    rec["experiment"] = "goldset"
    rec["capture_ip_group"] = ip_group
    rec["capture_day_utc"] = (rec.get("capture_started") or "")[:10]
    rec["gold_sample"] = item.get("sample") or {}
    rec["strato"] = bool((rec.get("dns") or {}).get("strato"))
    return rec


STOP_CODES = (503, 429)
STOP_FILE = "STOP_BLOCKED.json"


class StopCapture(Exception):
    """Raised for every item after a stop code was seen: the item is not captured (left for later)."""


def blocked_statuses(obj, codes=STOP_CODES, path="") -> list[tuple[str, int]]:
    """All (path, code) where a key named *status (int) holds a stop code, anywhere in the record (pure)."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            if (
                str(k).endswith("status")
                and isinstance(v, int)
                and not isinstance(v, bool)
                and v in codes
            ):
                hits.append((p, v))
            else:
                hits += blocked_statuses(v, codes, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += blocked_statuses(v, codes, f"{path}[{i}]")
    return hits


def wrap_capture_one(
    orig, ip_group: str, stop_on_block: bool = False, state: dict | None = None
):
    """Sample meta; with stop_on_block, the first 503/429 in a record stops the capture: later items raise StopCapture
    (no request is sent) and <out>/STOP_BLOCKED.json names the host. An item already running in another worker
    finishes."""
    state = state if state is not None else {}

    async def capture_one(browser, item, dns, out_root, versions):
        if stop_on_block and state.get("stop"):
            raise StopCapture(f"stopped after {state['stop']['host']}")
        rec = await orig(browser, item, dns, out_root, versions)
        add_sample_meta(rec, item, ip_group)
        out = C.host_dir(item["host"], out_root)
        (out / "meta.json").write_text(
            json.dumps(rec, indent=1, ensure_ascii=False, default=str)
        )
        hits = blocked_statuses(rec)
        if stop_on_block and hits and not state.get("stop"):
            state["stop"] = {
                "host": item["host"],
                "hits": hits,
                "capture_finished": rec.get("capture_finished"),
            }
            (Path(out_root) / STOP_FILE).write_text(json.dumps(state["stop"], indent=1))
            print(f"STOP {item['host']} {hits}", flush=True)
        return rec

    return capture_one


def delayed_scheduler(
    base, delay: float, state: dict | None = None, clock=time.monotonic
):
    """GroupScheduler subclass with a rest of `delay` seconds between the end of one item and the start of the next,
    over all hosts (the base class only spaces the starts within one provider group). After a stop (state["stop"] set by
    wrap_capture_one) no host is picked any more and the pending list is dropped, so the run ends without waiting.
    """
    state = state if state is not None else {}

    class DelayedScheduler(base):
        last_end = None

        def pick(self, now=None):
            now = clock() if now is None else now
            if state.get("stop"):
                self.pending.clear()
                return None
            if self.last_end is not None and now < self.last_end + delay:
                return None
            return super().pick(now)

        def release(self, h):
            super().release(h)
            self.last_end = clock()

    return DelayedScheduler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True, help="gold_sample.jsonl of the draw")
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--ip-group",
        required=True,
        help="free name of the capture machine / IP group, e.g. capture1",
    )
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument(
        "--stop-on-block",
        action="store_true",
        help="stop at the first HTTP 503 or 429 in a record",
    )
    ap.add_argument(
        "--host-delay",
        type=float,
        default=0.0,
        help="seconds of rest between the end of one host and the start of the next (use with --workers 1)",
    )
    a = ap.parse_args()
    out_root = Path(a.out)
    out_root.mkdir(parents=True, exist_ok=True)
    items = load_sample(Path(a.sample), a.limit)
    socket.setdefaulttimeout(10)
    with ThreadPoolExecutor(max_workers=32) as ex:
        dns = {d["host"]: d for d in ex.map(C.resolve, [i["host"] for i in items])}
    print(
        f"items {len(items)}, strato {sum(d['strato'] for d in dns.values())}, ip group {a.ip_group}",
        flush=True,
    )
    (out_root / "dns.json").write_text(json.dumps(dns, indent=0))
    state: dict = {}
    C.capture_one = wrap_capture_one(C.capture_one, a.ip_group, a.stop_on_block, state)
    if a.host_delay > 0:
        C.GroupScheduler = delayed_scheduler(C.GroupScheduler, a.host_delay, state)
    asyncio.run(C.run(items, dns, a.workers, out_root, a.retry_failed))


if __name__ == "__main__":
    main()
