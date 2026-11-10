"""E50: build the dev 500 (or held-out 300) input, reference and part files.

    python3 -I scripts/E50/build_sets.py --set dev        # E49 dev 200 + E51 dev2 300
    python3 -I scripts/E50/build_sets.py --set heldout    # E49 held-out 100 + E51 heldout2 200 (stage F only)

Inputs (read only): <main>/datasets/E49/{dev,heldout}_inputs.jsonl (rendered DOM), datasets/E51/{dev2,heldout2}_inputs.jsonl
(static HTML, copied from the main checkout). References: results/E49/refs/{poi_v3,wz}.jsonl (dev),
results/E49/heldout/refs/{poi_v3,wz}.jsonl (held-out), results/E51/refs/addr_e49.jsonl (both E49 sets),
results/E51/refs/{poi_v3,wz,addr}_{dev2,heldout2}.jsonl.
Outputs:
  datasets/E50/<set>_inputs.jsonl                     E49 part first, then E51 part
  results/E50/refs/{poi3,wz,addr}_<set>.jsonl         references of the hosts of the set only
  results/E50/parts/<set>_{e49,e49_noimprint,e51}.txt  host lists (e49_noimprint = E49 hosts with an empty imprint text)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MAIN = Path("/home/dinzinger/GitLab/fim/imprints-collection")
SETS = {
    "dev": {"e49_in": MAIN / "datasets/E49/dev_inputs.jsonl", "e51_in": Path("datasets/E51/dev2_inputs.jsonl"),
            "e49_poi": Path("results/E49/refs/poi_v3.jsonl"), "e49_wz": Path("results/E49/refs/wz.jsonl"),
            "e51": "dev2"},
    "heldout": {"e49_in": MAIN / "datasets/E49/heldout_inputs.jsonl",
                "e51_in": Path("datasets/E51/heldout2_inputs.jsonl"),
                "e49_poi": Path("results/E49/heldout/refs/poi_v3.jsonl"),
                "e49_wz": Path("results/E49/heldout/refs/wz.jsonl"), "e51": "heldout2"},
}
NAME = {"dev": "dev500", "heldout": "heldout300"}


def rows(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as f:  # not splitlines(): texts can hold U+2028 and other line separators
        return [json.loads(l) for l in f if l.strip()]


def write(p: Path, rs: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8")


def build(which: str) -> dict:
    s = SETS[which]
    name = NAME[which]
    e49, e51 = rows(s["e49_in"]), rows(s["e51_in"])
    h49, h51 = [r["host"] for r in e49], [r["host"] for r in e51]
    if set(h49) & set(h51):
        raise SystemExit("host overlap between the E49 and E51 parts")
    write(Path(f"datasets/E50/{name}_inputs.jsonl"), e49 + e51)
    want = set(h49) | set(h51)
    refs = {
        "poi3": rows(s["e49_poi"]) + rows(Path(f"results/E51/refs/poi_v3_{s['e51']}.jsonl")),
        "wz": rows(s["e49_wz"]) + rows(Path(f"results/E51/refs/wz_{s['e51']}.jsonl")),
        "addr": rows(Path("results/E51/refs/addr_e49.jsonl")) + rows(Path(f"results/E51/refs/addr_{s['e51']}.jsonl")),
    }
    n = {}
    for k, rs in refs.items():
        keep = [r for r in rs if r["host"] in want]
        missing = want - {r["host"] for r in keep}
        if missing:
            raise SystemExit(f"{k}: {len(missing)} hosts of the set have no reference")
        write(Path(f"results/E50/refs/{k}_{name}.jsonl"), keep)
        n[k] = len(keep)
    noimp = [r["host"] for r in e49 if not (r.get("imprint_text") or "").strip()]
    parts = {"e49": h49, "e49_noimprint": noimp, "e51": h51}
    for k, hs in parts.items():
        p = Path(f"results/E50/parts/{name}_{k}.txt")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(h + "\n" for h in hs), encoding="utf-8")
    return {"set": name, "inputs": len(e49) + len(e51), **{f"refs_{k}": v for k, v in n.items()},
            **{f"part_{k}": len(v) for k, v in parts.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=list(SETS))
    print(json.dumps(build(ap.parse_args().set)))


if __name__ == "__main__":
    main()
