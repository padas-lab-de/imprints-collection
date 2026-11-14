"""E53 step 5: gold capture of the drawn items (docs/gold_set_design.md 3.2), a thin wrapper of
scripts/gold/e17_capture.py.

Changes against E17:
- input: datasets/E53/phase2/gold_sample.jsonl (one host per line), output: <out>/<host>/ (default datasets/E53/gold);
- Strato hosts are captured (the capture VM is not the crawl VM); the Strato flag stays in meta.json["dns"];
- meta.json gets "experiment", "capture_ip_group" (the VM name), "capture_day_utc" and the E53 sample fields.
The `ic fetch` record and its timestamp are added later by scripts/E53/merge_fetch.py.

  PYTHONPATH=src <venv-render>/bin/python scripts/E53/capture.py --sample S --out OUT --ip-group akazie [--workers 6]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "e17_capture", HERE.parent / "gold" / "e17_capture.py"
)
C = importlib.util.module_from_spec(_spec)
sys.modules["e17_capture"] = C
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
                    "e53": {k: r.get(k) for k in SAMPLE_FIELDS},
                }
            )
    return items[:limit] if limit else items


def add_e53_meta(rec: dict, item: dict, ip_group: str) -> dict:
    """E53 provenance fields for meta.json (pure)."""
    rec["experiment"] = "E53"
    rec["capture_ip_group"] = ip_group
    rec["capture_day_utc"] = (rec.get("capture_started") or "")[:10]
    rec["e53_sample"] = item.get("e53") or {}
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
    """E53 meta; with stop_on_block, the first 503/429 in a record stops the capture: later items raise StopCapture
    (no request is sent) and <out>/STOP_BLOCKED.json names the host. An item already running in another worker
    finishes."""
    state = state if state is not None else {}

    async def capture_one(browser, item, dns, out_root, versions):
        if stop_on_block and state.get("stop"):
            raise StopCapture(f"stopped after {state['stop']['host']}")
        rec = await orig(browser, item, dns, out_root, versions)
        add_e53_meta(rec, item, ip_group)
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True, help="E53 gold_sample.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--ip-group",
        required=True,
        help="name of the capture VM / IP group, e.g. akazie",
    )
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument(
        "--stop-on-block",
        action="store_true",
        help="stop at the first HTTP 503 or 429 in a record",
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
    C.capture_one = wrap_capture_one(C.capture_one, a.ip_group, a.stop_on_block)
    asyncio.run(C.run(items, dns, a.workers, out_root, a.retry_failed))


if __name__ == "__main__":
    main()
