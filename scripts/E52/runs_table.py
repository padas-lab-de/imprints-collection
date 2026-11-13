"""E52: run table (efficiency, failures) and agreement between candidates without a reference.

    python3 -I scripts/E52/runs_table.py --e52 datasets/E52 --stage full --out results/E52/runs_full.md

Reads <e52>/gold_inputs.jsonl, <e52>/preds/<stage>/{address,poi3,wz}/<tag>.jsonl, <e52>/logs/<stage>/commands.txt,
*.log (start_utc / end_utc lines) and *.http.log (HTTP errors per attempt, scripts/E52/run.py). No reference labels.

Per run (one prediction file):
  items      input items of the stage (pilot: the hosts file)
  done       hosts in the prediction file
  no call    items without a model call (address: no imprint text, E50 rule)
  failed     error set (not "no_input"), plus topic answers without a valid id or KEINE (counted as malformed);
             split empty (no text in the reply) / malformed (no JSON, or no valid id) / truncated (cut at
             max_tokens) / timeout / other (HTTP or connection error after the client's 5 attempts);
             rate per 1,000 items with a call
  cut        replies that stopped at max_tokens (finish_reason length), also those that still parsed
  tok in/out prompt / completion tokens per item with a call: mean and p95 (embedding tokens not included)
  s/item     wall time per item (all calls of the item, incl. the retrieval embedding): median and p95
  window     first start_utc to last end_utc in the run log (resumed runs: several windows, all listed in the log)
  http       HTTP error attempts by status code (all retried by the client unless the item failed)
Agreement (no reference): share of items where two runs give the same answer, over items both runs answered
(topic: canonical path prefix at level L, both reach L; address: main address equal on street, number, postcode,
town after lower-case and space folding, or both without a main address).
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "E49"))
from tree import load_schema  # noqa: E402

SHORT = {
    "qwen38-27b": "qwen",
    "gemma4-31b-it": "gemma",
    "qwen-agentworld-35b-a3b": "agentworld",
}
SCREEN = {"qwen38-27b", "gemma4-31b-it"}  # phase-1 screen models (E53)
RUN_OF = [
    ("address", "address"),
    ("poi3", "retrieve"),
    ("poi3", "flat"),
    ("wz", "retrieve"),
]
RUN_NAME = {
    ("address", "address"): "address",
    ("poi3", "retrieve"): "POI k30",
    ("poi3", "flat"): "POI flat",
    ("wz", "retrieve"): "WZ k30",
}
FAIL_KINDS = ("empty", "malformed", "truncated", "timeout", "other")


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def p95(xs: list[float]) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))]


def fail_kind(p: dict) -> str | None:
    e = p.get("error")
    if e == "no_input":
        return None
    if e:
        if "cut at max_tokens" in e:
            return "truncated"
        if "no JSON object in reply" in e:
            return (
                "empty"
                if not e.split("no JSON object in reply:", 1)[1].strip()
                else "malformed"
            )
        if re.search(r"timed out|Timeout", e):
            return "timeout"
        return "other"
    if p.get("task") == "topic" and p.get("main") is None:
        tr = (p.get("trace") or [{}])[-1]
        if not tr.get("ids"):  # no valid id and no KEINE
            return "malformed"
    return None


def called(p: dict) -> bool:
    if p.get("task") == "address":
        return (p.get("usage") or {}).get("calls", 0) > 0 or bool(p.get("error"))
    return p.get("error") != "no_input"


def windows(log: Path) -> list[tuple[str, str]]:
    if not log.is_file():
        return []
    st = en = None
    out = []
    for l in log.read_text(encoding="utf-8").splitlines():
        if l.startswith("start_utc "):
            st = l.split()[1]
        elif l.startswith("end_utc ") and st:
            out.append((st, l.split()[1]))
            st = None
    if st:
        out.append((st, "running"))
    return out


def http_counts(p: Path) -> Counter:
    c = Counter()
    if p.is_file():
        for l in p.read_text(encoding="utf-8").splitlines():
            parts = l.split("\t")
            if len(parts) >= 2:
                c[parts[1]] += 1
    return c


def commands(p: Path) -> dict[tuple[str, str], str]:
    """(model, run key) -> last command line for it."""
    out = {}
    if not p.is_file():
        return out
    for l in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\S+ (python3 .*)$", l)
        if not m:
            continue
        cmd = m.group(1)
        model = re.search(r"--model (\S+)", cmd).group(1)
        log = re.search(r"--http-log \S+/(\S+)\.http\.log", cmd).group(1)
        out[(model, log[len(model) + 1 :])] = cmd
    return out


RUN_KEY = {
    ("address", "address"): "address",
    ("poi3", "retrieve"): "poi_k30",
    ("poi3", "flat"): "poi_flat",
    ("wz", "retrieve"): "wz",
}


def run_files(pred_dir: Path) -> list[tuple[str, tuple[str, str], Path]]:
    """[(model, (schema, strategy), file)] in candidate x run order."""
    out = []
    for sub in ("address", "poi3", "wz"):
        for f in sorted((pred_dir / sub).glob("*.jsonl")):
            first = json.loads(f.open(encoding="utf-8").readline())
            strat = "address" if sub == "address" else first["cfg"]["strategy"]
            out.append((first["model"], (sub, strat), f))
    order = {m: i for i, m in enumerate(SHORT)}
    return sorted(out, key=lambda t: (order.get(t[0], 9), RUN_OF.index(t[1])))


def row(model, key, f: Path, items: int, logs: Path, rel) -> dict:
    ps = load(f)
    by = {p["host"]: p for p in ps}
    cl = [p for p in by.values() if called(p)]
    kinds = Counter(k for k in map(fail_kind, by.values()) if k)
    u = lambda p, k: (p.get("usage") or {}).get(k, 0)  # noqa: E731
    tin = [u(p, "prompt_tokens") for p in cl if u(p, "calls")]
    tout = [u(p, "completion_tokens") for p in cl if u(p, "calls")]
    lat = [p["latency_s"] for p in cl]
    rk = RUN_KEY[key]
    return {
        "model": model,
        "run": RUN_NAME[key],
        "tag": f.stem,
        "file": rel(f),
        "sha256": sha256(f),
        "items": items,
        "done": len(by),
        "dupes": len(ps) - len(by),
        "no_call": len(by) - len(cl),
        "called": len(cl),
        "failed": sum(kinds.values()),
        "kinds": kinds,
        "per1000": 1000 * sum(kinds.values()) / len(cl) if cl else float("nan"),
        "cut": sum(u(p, "truncated") for p in by.values()),
        "cached": sum(u(p, "cached") for p in by.values()),
        "calls": sum(u(p, "calls") for p in by.values()),
        "abstain": sum(
            p.get("task") == "topic" and p.get("main") is None and not fail_kind(p)
            for p in by.values()
        ),
        "tin": (statistics.mean(tin) if tin else float("nan"), p95(tin)),
        "tout": (statistics.mean(tout) if tout else float("nan"), p95(tout)),
        "s": (statistics.median(lat) if lat else float("nan"), p95(lat)),
        "win": windows(logs / f"{model}_{rk}.log"),
        "http": http_counts(logs / f"{model}_{rk}.http.log"),
    }


def _addr_key(p: dict):
    i = p.get("main_index")
    if i is None or p.get("error"):
        return None
    a = p["addresses"][i]
    return tuple(
        re.sub(r"\s+", " ", (a.get(k) or "").lower()).strip()
        for k in ("street", "number", "postcode", "town")
    )


def agreement(runs: list[tuple[str, tuple[str, str], Path]]) -> list[str]:
    trees = {"poi3": load_schema("poi3"), "wz": load_schema("wz")}
    out = [
        "| run | x | y | n | agree L1 | agree L2 | agree L3 |",
        "|---|---|---|---|---|---|---|",
    ]
    groups: dict = {}
    for m, key, f in runs:
        groups.setdefault(key, []).append((m, {p["host"]: p for p in load(f)}))
    # same model, POI k30 vs POI flat
    pairs = [(RUN_NAME[k], g) for k, g in groups.items()]
    k30, flat = dict(groups.get(("poi3", "retrieve"), [])), dict(
        groups.get(("poi3", "flat"), [])
    )
    for m in k30:
        if m in flat:
            pairs.append(
                ("POI k30 vs flat", [(m + " k30", k30[m]), (m + " flat", flat[m])])
            )
    for name, g in pairs:
        for (mx, px), (my, py) in itertools.combinations(g, 2):
            hosts = sorted(set(px) & set(py))
            if name == "address":
                both = [
                    h
                    for h in hosts
                    if not px[h].get("error") and not py[h].get("error")
                ]
                same = sum(_addr_key(px[h]) == _addr_key(py[h]) for h in both)
                out.append(
                    f"| {name} | {SHORT.get(mx, mx)} | {SHORT.get(my, my)} | {len(both)} | "
                    f"{same / len(both):.3f} (main address) | | |"
                    if both
                    else f"| {name} | {mx} | {my} | 0 | | | |"
                )
                continue
            tree = trees["wz" if name.startswith("WZ") else "poi3"]
            P = lambda p: (
                tree.canonical_path(p["main"]) if p.get("main") in tree else []
            )  # noqa: E731
            both = [
                h
                for h in hosts
                if not fail_kind(px[h])
                and not fail_kind(py[h])
                and px[h].get("error") != "no_input"
            ]
            cells = []
            for L in (1, 2, 3):
                ok = [h for h in both if len(P(px[h])) >= L and len(P(py[h])) >= L]
                cells.append(
                    f"{sum(P(px[h])[:L] == P(py[h])[:L] for h in ok) / len(ok):.3f} ({len(ok)})"
                    if ok
                    else "n/a"
                )
            sx = lambda m: SHORT.get(m.split()[0], m.split()[0]) + (
                " " + m.split()[1] if " " in m else ""
            )  # noqa: E731
            out.append(
                f"| {name} | {sx(mx)} | {sx(my)} | {len(both)} | "
                + " | ".join(cells)
                + " |"
            )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e52", required=True)
    ap.add_argument("--stage", default="full", choices=["pilot", "full"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    e52 = Path(a.e52)
    rel = lambda f: "datasets/E52/" + str(
        Path(f).resolve().relative_to(e52.resolve())
    )  # noqa: E731
    inputs = load(e52 / "gold_inputs.jsonl")
    if a.stage == "pilot":
        want = {l.strip() for l in (e52 / "pilot_hosts.txt").open() if l.strip()}
        inputs = [r for r in inputs if r["host"] in want]
    no_imp = sum(not (r.get("imprint_text") or "").strip() for r in inputs)
    no_fetch = sum(bool((r.get("meta") or {}).get("no_ic_fetch")) for r in inputs)
    logs = e52 / "logs" / a.stage
    runs = run_files(e52 / "preds" / a.stage)
    rows = [row(m, k, f, len(inputs), logs, rel) for m, k, f in runs]
    cmds = commands(logs / "commands.txt")
    f1 = lambda x: f"{x:.1f}"  # noqa: E731
    L = [
        f"Stage {a.stage}: {len(inputs)} items; {no_imp} without imprint text ({no_fetch} of them without an "
        "ic_fetch.jsonl): address makes no call for them (prediction no_imprint), topics run on the landing page.",
        "",
        "| candidate | run | items | done | no call | failed (empty/malformed/truncated/timeout/other) | per 1,000 | "
        "cut | abstain | tok in mean / p95 | tok out mean / p95 | s/item median / p95 | window UTC | HTTP errors |",
        "|" + "---|" * 14,
    ]
    for r in rows:
        k = r["kinds"]
        mark = " (screen)" if r["model"] in SCREEN else ""
        win = (
            "; ".join(
                f"{s[5:16]}-{e[11:16] if e != 'running' else e}" for s, e in r["win"]
            )
            or "n/a"
        )
        http = ", ".join(f"{c} x{n}" for c, n in sorted(r["http"].items())) or "0"
        L.append(
            f"| {r['model']}{mark} | {r['run']} | {r['items']} | {r['done']} | {r['no_call']} | {r['failed']} "
            f"({'/'.join(str(k.get(x, 0)) for x in FAIL_KINDS)}) | {f1(r['per1000'])} | {r['cut']} | "
            f"{r['abstain'] if r['run'] != 'address' else '-'} | {r['tin'][0]:.0f} / {r['tin'][1]:.0f} | "
            f"{r['tout'][0]:.0f} / {r['tout'][1]:.0f} | {r['s'][0]:.2f} / {r['s'][1]:.2f} | {win} | {http} |"
        )
    L += [
        "",
        "Prediction files (sha256):",
        "",
        "| candidate | run | file | sha256 | calls | cached calls |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        L.append(
            f"| {r['model']} | {r['run']} | `{r['file']}` | `{r['sha256']}` | {r['calls']} | {r['cached']} |"
        )
    L += [
        "",
        "Commands (exact, as run from the repository root; E52 = datasets/E52):",
        "",
    ]
    for r in rows:
        c = cmds.get(
            (r["model"], RUN_KEY[next(k for k, v in RUN_NAME.items() if v == r["run"])])
        )
        if c:
            c = c.replace(str(e52.resolve()) + "/", "$E52/").replace(
                str(e52) + "/", "$E52/"
            )
        L.append(f"- {r['model']} {r['run']}: `{c}`")
    L += [
        "",
        "Agreement between candidates, **no reference** (share of items with the same answer; n in brackets = "
        "items where both reach the level):",
        "",
    ] + agreement(runs)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
