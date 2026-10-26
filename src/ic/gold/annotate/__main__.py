"""python -m ic.gold.annotate --labeller L1 --port 8800"""

from __future__ import annotations

import argparse

from .server import serve
from .store import Store


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m ic.gold.annotate", description=__doc__)
    ap.add_argument("--labeller", required=True, help="your ID: L1, L2 or L3")
    ap.add_argument("--port", type=int, default=8800)
    ap.add_argument("--bind", default="127.0.0.1", help="interface (default: local only)")
    ap.add_argument("--data-dir", default="datasets/gold", help="captures, assignment, labels")
    ap.add_argument("--assignment", default=None, help="default: <data-dir>/assignment.jsonl")
    ap.add_argument(
        "--prefill",
        choices=("primary", "all", "none"),
        default="primary",
        help="show suggestions from <data-dir>/prefill.jsonl for these items (D24; default: primary labels only)",
    )
    a = ap.parse_args(argv)
    roles = {"primary": ("primary",), "all": ("primary", "second", "calibration"), "none": ()}[a.prefill]
    serve(Store(a.data_dir, a.labeller, a.assignment, prefill_roles=roles), a.bind, a.port)


if __name__ == "__main__":
    main()
