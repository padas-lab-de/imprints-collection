"""Loaders: gold sample (weights, strata, folds), labels per labeller, assignment, adjudication,
prediction files (any number), geocodes and input texts.

Hosts are matched by ``hkey``: lower case, no trailing dot, no leading "www.".
"""

from __future__ import annotations

import glob
import json
from dataclasses import dataclass, field
from pathlib import Path

from ic.eval._legacy import schema_key

SHORT = {
    "qwen38-27b": "qwen",
    "gemma4-31b-it": "gemma",
    "qwen-agentworld-35b-a3b": "agentworld",
    "soofi-s-isar-preview": "soofi",
}


def hkey(host: str) -> str:
    h = (host or "").strip().lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def read_jsonl(path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------------------------


@dataclass
class Sample:
    items: list[
        dict
    ]  # one dict per item: host, key, item, weight, pi, stratum, M_h, m_h, core, fold, fold_group
    index: dict = field(default_factory=dict)  # hkey -> position

    def __len__(self) -> int:
        return len(self.items)

    def col(self, name: str) -> list:
        return [it.get(name) for it in self.items]

    def design(self, **kw):
        from ic.eval.estimators import Design

        return Design(
            self.col("weight"),
            self.col("stratum"),
            self.col("M_h"),
            self.col("m_h"),
            self.col("core"),
            self.col("fold"),
            **kw,
        )


def _sample_rows(path) -> list[dict]:
    p = Path(path)
    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("items") or data.get("sample") or list(data.values())[0]
        return list(data)
    return read_jsonl(p)


def load_sample(path) -> Sample:
    """Gold sample (``gold_sample.jsonl``) or split file (``results/E52/split.json``)."""
    items = []
    for i, r in enumerate(_sample_rows(path)):
        w = r.get("weight", r.get("design_weight"))
        pi = r.get("pi")
        if w is None and pi:
            w = 1.0 / pi
        if w is None:
            w = 1.0
        it = {
            "host": r["host"],
            "key": hkey(r["host"]),
            "item": r.get("item", i),
            "weight": float(w),
            "pi": pi,
            "stratum": r.get("stratum", r.get("priority_stratum", "all")),
            "M_h": r.get("M_h"),
            "m_h": r.get("m_h"),
            "core": bool(r.get("core", r.get("in_core", False))),
            "fold": r.get("fold"),
            "fold_group": r.get("fold_group"),
        }
        items.append(it)
    counts = {}
    for it in items:
        counts[it["stratum"]] = counts.get(it["stratum"], 0) + 1
    for it in items:
        if it["m_h"] is None:
            it["m_h"] = counts[it["stratum"]]
    return Sample(items, {it["key"]: i for i, it in enumerate(items)})


def unit_sample(hosts, core: bool = True) -> Sample:
    """Equal weights, one stratum, no fpc (unweighted scoring, e.g. the E49 reproduction)."""
    items = [
        {
            "host": h,
            "key": hkey(h),
            "item": i,
            "weight": 1.0,
            "pi": None,
            "stratum": "all",
            "M_h": None,
            "m_h": None,
            "core": core,
            "fold": i % 5,
            "fold_group": "all",
        }
        for i, h in enumerate(hosts)
    ]
    for it in items:
        it["m_h"] = len(items)
    return Sample(items, {it["key"]: i for i, it in enumerate(items)})


# ---------------------------------------------------------------------------------------------
# Labels, assignment, adjudication
# ---------------------------------------------------------------------------------------------


def load_labels(paths) -> dict[str, dict[str, dict]]:
    """labeller -> hkey -> label. The last line per host wins (the tool appends one line per save).
    The labeller is the record's ``annotator`` or else the file stem (L1.jsonl -> L1).
    """
    out: dict[str, dict[str, dict]] = {}
    for p in _expand(paths):
        for r in read_jsonl(p):
            if not r.get("host"):
                continue
            lab = r.get("annotator") or Path(p).stem
            out.setdefault(lab, {})[hkey(r["host"])] = r
    return out


def load_assignment(path) -> dict[str, dict[str, str]]:
    """hkey -> labeller -> role (calibration | primary | second)."""
    out: dict[str, dict[str, str]] = {}
    if not path:
        return out
    for r in read_jsonl(path):
        out.setdefault(hkey(r["host"]), {})[r["labeller"]] = r.get("role", "primary")
    return out


def load_adjudication(path) -> dict[str, dict]:
    """hkey -> adjudicated record (label fields; optional ``parts`` = which parts it decides:
    status, address, poi, wz; default all parts present in the record)."""
    if not path:
        return {}
    return {hkey(r["host"]): r for r in read_jsonl(path)}


# ---------------------------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------------------------


@dataclass
class PredSet:
    name: str
    task: str  # "topic" | "address"
    schema: str | None  # "poi" | "wz" | None (address)
    model: str
    variant: str
    rows: dict  # hkey -> row
    path: str = ""
    meta: dict = field(
        default_factory=dict
    )  # cost fields, screen / suggestion flags, members (ens2)

    @property
    def group(self) -> str:
        return self.schema if self.task == "topic" else "address"


def _expand(paths) -> list[str]:
    if isinstance(paths, (str, Path)):
        paths = [paths]
    out = []
    for p in paths:
        p = str(p)
        if any(c in p for c in "*?["):
            out += sorted(glob.glob(p, recursive=True))
        elif Path(p).is_dir():
            out += sorted(str(x) for x in Path(p).rglob("*.jsonl"))
        else:
            out.append(p)
    return out


def _infer(path: str, row: dict) -> dict:
    p = Path(path)
    task = row.get("task")
    schema = row.get("schema")
    if task is None:
        task = (
            "address"
            if ("addresses" in row or "main_index" in row or schema == "address")
            else "topic"
        )
    if task == "topic" and schema is None:
        schema = p.parent.name
    if task == "address":
        schema = None
    else:
        schema = schema_key(schema)
    model = row.get("model") or ""
    tag = row.get("tag") or p.stem
    parts = tag.split("__")
    short = SHORT.get(model, model)
    if len(parts) >= 2 and (not short or short in ("ensemble",)):
        short = parts[1]
    # layout preds/<task>/<model>/<variant>.jsonl (protocol section 8)
    if not row.get("tag") and p.parent.parent.name in ("topic", "address", "poi", "wz"):
        short, tag = p.parent.name, p.stem
    elif len(parts) >= 2 and parts[1] == short:
        tag = "__".join([parts[0]] + parts[2:])
    return {"task": task, "schema": schema, "model": short or "model", "variant": tag}


def load_predictions(paths=None, manifest=None) -> list[PredSet]:
    """Prediction files in the scripts/E50/e50_run.py format (one JSON line per host).

    ``manifest``: JSON list (or {"predictions": [...]}) of entries with ``path`` (relative to the
    manifest) and optional ``name``, ``model``, ``variant``, ``task``, ``schema``, ``screen``,
    ``suggestion``, cost fields (``usd_per_mtok_in``, ``usd_per_mtok_cached``, ``usd_per_mtok_out``,
    ``gpu_hours_per_mhost``, ``usd_per_gpu_hour``). Without a manifest, model and variant come from the
    line (``model``, ``tag``, ``task``, ``schema``) or from the path layout.
    """
    entries = []
    if manifest:
        m = json.loads(Path(manifest).read_text(encoding="utf-8"))
        m = m.get("predictions", m) if isinstance(m, dict) else m
        base = Path(manifest).parent
        for e in m:
            for p in _expand(
                str(base / e["path"])
                if not Path(e["path"]).is_absolute()
                else e["path"]
            ):
                entries.append((p, e))
    for p in _expand(paths or []):
        entries.append((p, {}))
    out, names = [], set()
    for p, e in entries:
        rows = read_jsonl(p)
        if not rows:
            continue
        inf = _infer(p, rows[0])
        task = e.get("task", inf["task"])
        schema = (
            None
            if task == "address"
            else schema_key(e.get("schema", inf["schema"] or ""))
        )
        model = e.get("model", inf["model"])
        variant = e.get("variant", inf["variant"])
        name = e.get("name") or f"{model}/{variant}"
        base, k = name, 2
        while (name, schema, task) in names:
            name, k = f"{base}#{k}", k + 1
        names.add((name, schema, task))
        meta = {
            k: v
            for k, v in e.items()
            if k not in ("path", "name", "model", "variant", "task", "schema")
        }
        out.append(
            PredSet(
                name,
                task,
                schema,
                model,
                variant,
                {hkey(r["host"]): r for r in rows if r.get("host")},
                str(p),
                meta,
            )
        )
    return out


# ---------------------------------------------------------------------------------------------
# Geocodes and texts
# ---------------------------------------------------------------------------------------------


def addr_key(a: dict | None) -> str | None:
    """Model-independent geocode key: normalised postcode|street|number|town."""
    if not a:
        return None
    from ic.eval._legacy import addr

    AS = addr()
    return "|".join(
        AS.norm(f, a.get(f, "") or "") for f in ("postcode", "street", "number", "town")
    )


def load_geocodes(path) -> dict[str, tuple | None]:
    """addr_key -> (lat, lon) or None (geocoding failed). Rows: {street, number, postcode, town, lat, lon}
    or {key, lat, lon}. A key absent from the file means "not geocoded yet"."""
    out: dict[str, tuple | None] = {}
    if not path:
        return out
    for r in read_jsonl(path):
        k = r.get("key") or addr_key(r)
        lat, lon = r.get("lat"), r.get("lon")
        out[k] = (
            (float(lat), float(lon)) if lat is not None and lon is not None else None
        )
    return out


def load_texts(path) -> dict[str, str]:
    """hkey -> model input text (imprint + homepage) for the evidence check."""
    out = {}
    if not path:
        return out
    for r in read_jsonl(path):
        out[hkey(r["host"])] = "\n".join(
            str(r.get(k) or "") for k in ("imprint_text", "homepage_text", "text")
        )
    return out
