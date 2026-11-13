"""``ic score``: score E52 candidates against the gold reference and apply the decision rule.

Example (from the repository root)::

    ic score --sample datasets/E53/phase2/gold_sample.jsonl \\
        --labels 'datasets/gold/labels/L*.jsonl' --assignment datasets/E53/gold/assignment.jsonl \\
        --preds 'datasets/E52/preds/full/*/*.jsonl' --geocodes results/E52/geocodes.jsonl \\
        --run-id first --set method=bootstrap --set margin=se
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from dataclasses import fields

import click

from ic.eval import io as IO
from ic.eval import report
from ic.eval.agreement import agreement
from ic.eval.reference import build_reference, refs_from_e49, refs_from_gold
from ic.eval.score import Params, Scorer


def _coerce(name: str, raw: str):
    ftypes = {f.name: f for f in fields(Params)}
    if name not in ftypes:
        raise click.BadParameter(
            f"unknown parameter {name!r}; known: {', '.join(sorted(ftypes))}"
        )
    default = getattr(Params(), name)
    try:
        val = json.loads(raw)
    except json.JSONDecodeError:
        val = raw
    if isinstance(default, bool):
        return (
            val if isinstance(val, bool) else str(val).lower() in ("1", "true", "yes")
        )
    if (
        isinstance(default, int)
        and not isinstance(default, bool)
        and isinstance(val, (int, float))
    ):
        return int(val)
    if isinstance(default, float) and isinstance(val, (int, float)):
        return float(val)
    if isinstance(default, tuple) and isinstance(val, str):
        return tuple(x for x in val.split(",") if x)
    if name == "ens2_pairs" and isinstance(val, str) and "+" in val:
        return [x for x in val.split(",") if x]
    return val


def make_params(params_file: str | None, sets: tuple[str, ...]) -> Params:
    kw = {}
    if params_file:
        with open(params_file, encoding="utf-8") as f:
            kw.update(json.load(f))
    for s in sets:
        if "=" not in s:
            raise click.BadParameter(f"--set needs key=value, got {s!r}")
        k, v = s.split("=", 1)
        kw[k.strip()] = _coerce(k.strip(), v.strip())
    if "screen_models" in kw:
        kw["screen_models"] = tuple(kw["screen_models"])
    return Params(**kw)


def run(
    sample,
    preds=(),
    manifest=None,
    labels=(),
    assignment=None,
    adjudication=None,
    refs_file=None,
    refs_schema=None,
    gold_file=None,
    geocodes=None,
    texts=None,
    params: Params | None = None,
    out_root="results/E52/score",
    run_id=None,
    label_noise=True,
) -> tuple[str, dict]:
    p = params or Params()
    smp = IO.load_sample(sample)
    keys = [it["key"] for it in smp.items]
    lab = IO.load_labels(labels) if labels else {}
    asg = IO.load_assignment(assignment)
    adj = IO.load_adjudication(adjudication)
    alt, stats, agr = {}, None, None
    geo = IO.load_geocodes(geocodes) if geocodes else {}
    if refs_file:
        refs = refs_from_e49(refs_file, refs_schema or "poi")
    elif gold_file:
        refs = refs_from_gold(gold_file)
    else:
        kw = dict(
            depth_rule=p.depth_rule,
            adjudication_scope=p.adjudication_scope,
            unresolved_topic=p.unresolved_topic,
            unresolved_other=p.unresolved_other,
        )
        refs, stats = build_reference(keys, lab, asg, adj, **kw)
        agr = agreement(keys, lab, asg, geo)
        if label_noise and any((r or {}).get("double") for r in refs.values()):
            for use in ("first", "second"):
                alt[use] = build_reference(keys, lab, asg, adj, use=use, **kw)[0]
    ps = IO.load_predictions(list(preds), manifest)
    if not ps:
        raise click.UsageError("no prediction files found")
    tx = IO.load_texts(texts) if texts else {}
    res = Scorer(smp, refs, ps, p, geocodes=geo, texts=tx, alt_refs=alt).run()
    res["inputs"] = {
        "sample": str(sample),
        "preds": [x.path for x in ps],
        "labels": list(labels),
        "assignment": assignment,
        "adjudication": adjudication,
        "refs": refs_file,
        "gold": gold_file,
        "geocodes": geocodes,
        "texts": texts,
        "manifest": manifest,
    }
    rid = run_id or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = os.path.join(out_root, rid)
    report.write(res, out, refs, stats, agr)
    return out, res


@click.command("score")
@click.option(
    "--sample",
    required=True,
    help="gold_sample.jsonl or results/E52/split.json (weights, strata, folds).",
)
@click.option(
    "--preds",
    multiple=True,
    help="Prediction files, globs or directories (E50 run format). Repeatable.",
)
@click.option(
    "--manifest",
    default=None,
    help="JSON/JSONL list of prediction sets with names and cost fields.",
)
@click.option(
    "--labels",
    multiple=True,
    help="Label files datasets/gold/labels/L<n>.jsonl (globs ok). Repeatable.",
)
@click.option(
    "--assignment", default=None, help="assignment.jsonl (host, labeller, role)."
)
@click.option(
    "--adjudication",
    default=None,
    help="Adjudicated records (host + label fields [+ parts]).",
)
@click.option(
    "--refs",
    "refs_file",
    default=None,
    help="Pre-built E49 topic reference instead of labels.",
)
@click.option("--refs-schema", default="poi", help="Schema of --refs (poi or wz).")
@click.option(
    "--gold",
    "gold_file",
    default=None,
    help="One adjudicated v3 label per host instead of labels.",
)
@click.option(
    "--geocodes",
    default=None,
    help="JSONL {key|address, lat, lon} for the 100 m match.",
)
@click.option(
    "--texts",
    default=None,
    help="JSONL with page texts for the evidence check (E52 gold_inputs).",
)
@click.option(
    "--params", "params_file", default=None, help="JSON file with Params fields."
)
@click.option(
    "--set",
    "sets",
    multiple=True,
    help="Override one Params field: key=value (JSON value). Repeatable.",
)
@click.option("--out-root", default="results/E52/score", show_default=True)
@click.option(
    "--run-id", default=None, help="Output folder name (default: UTC timestamp)."
)
@click.option(
    "--no-label-noise",
    is_flag=True,
    help="Skip the first/second-label decision variants.",
)
def score(
    sample,
    preds,
    manifest,
    labels,
    assignment,
    adjudication,
    refs_file,
    refs_schema,
    gold_file,
    geocodes,
    texts,
    params_file,
    sets,
    out_root,
    run_id,
    no_label_noise,
):
    """Score E52 candidates (protocol sections 5-8) and write results/E52/score/<run-id>/."""
    p = make_params(params_file, sets)
    if not (labels or refs_file or gold_file):
        raise click.UsageError("give --labels, --refs or --gold")
    out, res = run(
        sample,
        preds,
        manifest,
        labels,
        assignment,
        adjudication,
        refs_file,
        refs_schema,
        gold_file,
        geocodes,
        texts,
        p,
        out_root,
        run_id,
        not no_label_noise,
    )
    for g, r in res["groups"].items():
        click.echo(
            f"{g}: choice {r['final']['choice']} (best {r['decision']['best']}; Q = {r['q_metric']}; "
            f"shifts {r['final']['shifts'] or 'none'})"
        )
    click.echo(f"wrote {out}")
