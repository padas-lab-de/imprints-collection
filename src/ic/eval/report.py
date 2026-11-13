"""Write the scorer result to results/E52/score/<run-id>/ (protocol section 8, tables A-D).

Files: params.json, summary.json, summary.md, agreement.md, reference/{status,address,poi,wz}.jsonl +
reference/stats.json, scores/{topics_<schema>,addresses,efficiency}.{md,csv}, scores/per_stratum.md,
paired.md, pareto_<task>.csv, depth_<schema>.md. CSV files are long format (one estimate per row).
"""

from __future__ import annotations

import csv
import json
import os


def _f(x, d=3) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{d}f}"
    return str(x)


def _ci(e: dict | None, d=3) -> str:
    if not e or e.get("est") is None:
        return "-"
    if e.get("lo") is None:
        return _f(e["est"], d)
    return f"{e['est']:.{d}f} [{e['lo']:.{d}f}, {e['hi']:.{d}f}]"


def _md_table(head: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def _dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=_default)


def _default(o):
    try:
        import numpy as np

        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:  # pragma: no cover
        pass
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def _csv_rows(res: dict):
    for g, r in res["groups"].items():
        for name, c in r["candidates"].items():
            for block in ("weighted", "core"):
                for metric, e in (c.get(block) or {}).items():
                    yield [
                        g,
                        name,
                        block,
                        metric,
                        e.get("est"),
                        e.get("se"),
                        e.get("lo"),
                        e.get("hi"),
                        e.get("n"),
                    ]
            for sub, tab in (c.get("subsets") or {}).items():
                for metric, e in tab.items():
                    yield [
                        g,
                        name,
                        sub,
                        metric,
                        e.get("est"),
                        e.get("se"),
                        e.get("lo"),
                        e.get("hi"),
                        e.get("n"),
                    ]
            for block in ("weighted", "core"):
                for metric, e in ((c.get("oof") or {}).get(block) or {}).items():
                    yield [
                        g,
                        name,
                        f"oof_{block}",
                        metric,
                        e.get("est"),
                        e.get("se"),
                        e.get("lo"),
                        e.get("hi"),
                        e.get("n"),
                    ]


def _write_csv(path, head, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)


HEAD = ["group", "candidate", "block", "metric", "est", "se", "lo", "hi", "n"]


def topics_md(g: str, r: dict, Lmax: int) -> str:
    out = [
        f"# Topics: {g}\n",
        f"Q = {r['q_metric']}; weighted Hajek estimates with "
        f"{r.get('method', '')} CIs. Core = unweighted core items, Wilson CI.\n",
    ]
    for title, block in (
        ("Weighted population", "weighted"),
        ("Unweighted core check", "core"),
    ):
        out.append(f"\n## {title}\n")
        head = ["candidate", "screen"] + [
            f"{m}@{L}" for L in range(1, Lmax + 1) for m in ("P", "acc", "cov")
        ]
        head += ["no_label", "failed"]
        rows = []
        for name, c in r["candidates"].items():
            t = c.get(block) or {}
            row = [name, "yes" if c.get("screen") else ""]
            row += [
                _ci(t.get(f"{m}@{L}"))
                for L in range(1, Lmax + 1)
                for m in ("P", "acc", "cov")
            ]
            row += [_ci(t.get("no_label")), _ci(t.get("failed"))]
            rows.append(row)
        out.append(_md_table(head, rows))
    out.append(
        "\n## Truncated accuracy (E49 summary 'acc') and lenient precision, weighted\n"
    )
    head = (
        ["candidate"]
        + [f"acc_trunc@{L}" for L in range(1, Lmax + 1)]
        + [f"lenient@{L}" for L in range(1, Lmax + 1)]
    )
    rows = [
        [n]
        + [_ci(c["weighted"].get(f"acc_trunc@{L}")) for L in range(1, Lmax + 1)]
        + [_ci(c["weighted"].get(f"lenient@{L}")) for L in range(1, Lmax + 1)]
        for n, c in r["candidates"].items()
    ]
    out.append(_md_table(head, rows))
    out.append("\n## Offline vs online-only items (weighted)\n")
    head = ["candidate", "subset"] + [f"acc@{L}" for L in range(1, Lmax + 1)]
    rows = []
    for n, c in r["candidates"].items():
        for sub, t in (c.get("subsets") or {}).items():
            rows.append([n, sub] + [_ci(t.get(f"acc@{L}")) for L in range(1, Lmax + 1)])
    out.append(_md_table(head, rows))
    out.append("\n## Counts\n")
    rows = [
        [
            n,
            *[c["counts"].get(k) for k in ("scored", "ref_none", "no_label", "failed")],
            " ".join(f"{d}:{k}" for d, k in c.get("depth_hist", {}).items()),
        ]
        for n, c in r["candidates"].items()
    ]
    out.append(
        _md_table(
            [
                "candidate",
                "scored",
                "ref_none",
                "no_label",
                "failed",
                "depth histogram",
            ],
            rows,
        )
    )
    return "".join(out)


def depth_md(g: str, r: dict, Lmax: int) -> str:
    out = [f"# Publish depth by 5-fold cross-fitting: {g}\n\n"]
    head = ["candidate", "cut-off per fold", "cut-off (all)"] + [
        f"oof_P@{L}" for L in range(1, Lmax + 1)
    ]
    head += ["published", "P(published)", "correct levels", "depth"]
    rows = []
    for n, c in r["candidates"].items():
        o = c.get("oof") or {}
        w = o.get("weighted") or {}
        rows.append(
            [
                n,
                " ".join(f"{k}:{v}" for k, v in (o.get("cuts") or {}).items()),
                o.get("cut_full"),
            ]
            + [_ci(w.get(f"oof_P@{L}")) for L in range(1, Lmax + 1)]
            + [
                _ci(w.get(k))
                for k in (
                    "oof_published",
                    "oof_published_P",
                    "oof_correct_levels",
                    "oof_depth",
                )
            ]
        )
    out.append(_md_table(head, rows))
    c0 = next(iter(r["candidates"].values()), {})
    if c0.get("oof"):
        out.append(
            f"\nCriterion: {c0['oof']['criterion']}; threshold P >= {c0['oof']['min_precision']}.\n"
        )
    return "".join(out)


def addresses_md(r: dict) -> str:
    keys = [
        "loc100_all",
        "loc100",
        "loc1km_all",
        "addr_P",
        "exact",
        "field_F1",
        "noaddr_P",
        "noaddr_R",
        "false_address_rate",
        "missed_address_rate",
        "hallucination",
        "geocode_missing",
        "failed",
    ]
    out = ["# Addresses\n", f"Q = {r['q_metric']}.\n"]
    for title, block in (
        ("Weighted population", "weighted"),
        ("Unweighted core check", "core"),
    ):
        out.append(f"\n## {title}\n")
        rows = [
            [n, "yes" if c.get("screen") else ""]
            + [_ci((c.get(block) or {}).get(k)) for k in keys]
            for n, c in r["candidates"].items()
        ]
        out.append(_md_table(["candidate", "screen"] + keys, rows))
    out.append("\n## Fields (weighted)\n")
    fk = sorted(
        {
            k
            for c in r["candidates"].values()
            for k in c["weighted"]
            if k.startswith("field_")
        }
    )
    rows = [
        [n] + [_ci(c["weighted"].get(k)) for k in fk]
        for n, c in r["candidates"].items()
    ]
    out.append(_md_table(["candidate"] + fk, rows))
    out.append("\n## Counts\n")
    ck = ["ref", "ref_main", "pred_main", "failed", "geocoded_pairs", "geocode_missing"]
    rows = [[n] + [c["counts"].get(k) for k in ck] for n, c in r["candidates"].items()]
    out.append(_md_table(["candidate"] + ck, rows))
    return "".join(out)


EFF_KEYS = [
    "failed_rate",
    "failed_per_1000_calls",
    "failed_rate_items",
    "calls_mean",
    "tok_in_mean",
    "tok_out_mean",
    "reasoning_mean",
    "C_mean",
    "C_p95",
    "s_median",
    "s_p95",
    "truncated_rate",
    "C_per_1M",
    "usd_per_1M",
    "gpu_hours_per_1M",
]


def efficiency_md(res: dict) -> str:
    out = [
        "# Efficiency\n\nWeighted means per host; cost per 1M hosts = weighted mean x 1e6.\n"
    ]
    for g, r in res["groups"].items():
        out.append(f"\n## {g} (cost axis for the decision: {r['cost_axis']})\n")
        rows = [
            [n] + [_f(c["efficiency"].get(k), 4) for k in EFF_KEYS]
            for n, c in r["candidates"].items()
        ]
        out.append(_md_table(["candidate"] + EFF_KEYS, rows))
    return "".join(out)


def paired_md(res: dict) -> str:
    out = [
        "# Paired differences vs the best candidate\n\n",
        f"CI method: {res['params']['method']}. Same items for both members of a pair (paired).\n"
        "p: two-sided normal test; Holm-adjusted over the primary (Q) tests of all tasks.\n",
    ]
    for g, r in res["groups"].items():
        out.append(f"\n## {g}\n")
        rows = []
        for d in r["paired"]:
            key = f"{g}:{d['x']} vs {d['y']}"
            adj = res["holm"].get(key) if d["metric"] == r["q_metric"] else None
            rows.append(
                [
                    d["x"],
                    d["y"],
                    d["metric"],
                    _ci(d),
                    _f((d.get("extra") or {}).get("p") or d.get("p")),
                    _f(adj),
                ]
            )
        out.append(
            _md_table(["x", "best", "metric", "x - best [CI]", "p", "p Holm"], rows)
        )
    return "".join(out)


def per_stratum_md(res: dict) -> str:
    out = [
        "# Per true stratum (unweighted, Wilson CI; n >= min_stratum_n)\n\n"
        "True stratum = class of the reference (poi: level-2 node, wz: level-3 node, address: main/flag/none). "
        "Screen models (marked *) chose part of the strata (protocol 6); their numbers there are not neutral.\n"
    ]
    for g, r in res["groups"].items():
        names = list(r["candidates"])
        out.append(
            f"\n## {g} ({r['q_metric'] if res['params']['target'] != 'depth' else 'acc'})\n"
        )
        rows = []
        for cls, row in r["per_stratum"].items():
            cells = []
            for n in names:
                e = row.get(n) or {}
                cells.append(
                    f"{e['rate']:.2f} [{e['lo']:.2f}, {e['hi']:.2f}] (n={e['n']})"
                    if "rate" in e
                    else f"n={e.get('n', 0)}"
                )
            rows.append([cls] + cells)
        out.append(
            _md_table(
                ["stratum"]
                + [
                    n + ("*" if r["candidates"][n].get("screen") else "") for n in names
                ],
                rows,
            )
        )
    return "".join(out)


def agreement_md(agr: dict | None) -> str:
    if not agr:
        return "# Agreement\n\nNo double-labelled items.\n"
    out = ["# Agreement between the two labellers (table A)\n\n"]
    rows = []

    def walk(prefix, d):
        for k, v in d.items():
            if isinstance(v, dict):
                walk(f"{prefix}{k}.", v)
            else:
                rows.append([f"{prefix}{k}", _f(v)])

    walk("", agr)
    out.append(_md_table(["statistic", "value"], rows))
    return "".join(out)


def pareto_rows(r: dict):
    d = r["decision"]
    for n, c in r["candidates"].items():
        yield [
            n,
            c["Q"]["est"],
            c["Q"]["lo"],
            c["Q"]["hi"],
            c.get("C"),
            r["cost_axis"],
            c["efficiency"]["failed_rate"],
            c.get("p1"),
            n in d["front"],
            n not in d["filtered_out"],
            n in d["eligible"],
            n == r["final"]["choice"],
            c.get("screen"),
        ]


def summary_md(res: dict) -> str:
    p = res["params"]
    out = [
        "# E52 scoring summary\n\n",
        f"Items: {res['n_items']} (core {res['n_core']}, double-labelled {res['n_double']}); Kish n_eff "
        f"{res['kish_n']}; variance strata {res['variance_strata']}. CI method {p['method']}"
        f"{' (B=%d)' % p['B'] if p['method'] == 'bootstrap' else ''}, level {p['level']}.\n\n"
        f"Decision rule (protocol 7): failed rate <= {p['max_fail']}, P first level >= {p['p_floor']}, "
        f"Pareto front, cheapest within margin {p['margin']} of the best (point and paired CI lower bound), "
        f"tie rule '{p['tie_rule']}'.\n",
    ]
    for g, r in res["groups"].items():
        d, fz = r["decision"], r["final"]
        out.append(f"\n## {g}\n\n")
        out.append(f"- Q = {r['q_metric']}; cost axis {r['cost_axis']}.\n")
        out.append(
            f"- Best: {d['best']} (Q {_ci(r['candidates'][d['best']]['Q']) if d['best'] else '-'}).\n"
        )
        out.append(f"- Pareto front: {', '.join(d['front']) or '-'}.\n")
        out.append(
            f"- Eligible within margin {_f(d['margin'])}: {', '.join(d['eligible']) or '-'}.\n"
        )
        out.append(
            f"- **Choice: {fz['choice']}**"
            + (
                f" (main rule: {fz['main_choice']})"
                if fz["choice"] != fz["main_choice"]
                else ""
            )
            + ".\n"
        )
        if d["filtered_out"]:
            out.append(
                "- Filtered out: "
                + "; ".join(
                    f"{k} ({', '.join(v)})" for k, v in d["filtered_out"].items()
                )
                + ".\n"
            )
        if fz["shifts"]:
            out.append(
                "- **Choice shifts** (lead decides): "
                + "; ".join(f"{k} -> {v}" for k, v in fz["shifts"].items())
                + ".\n"
            )
        else:
            out.append(
                f"- No shift under: {', '.join(r['variants']) or 'no variants'}.\n"
            )
        if fz["choice"] and r["candidates"][fz["choice"]].get("screen"):
            out.append("- Note: the choice is a screen model (protocol 6).\n")
        rows = [
            [
                n,
                _ci(c["Q"]),
                _ci(c.get("Q_core")),
                _f(c.get("C"), 2),
                _f(c["efficiency"]["failed_rate"]),
                _f(c.get("p1")),
            ]
            for n, c in r["candidates"].items()
        ]
        out.append(
            "\n"
            + _md_table(
                ["candidate", "Q weighted", "Q core", "C", "failed", "P first"], rows
            )
        )
    out.append(
        "\nCaveats: weights are design weights of the two-phase sample; strata with one sampled item are "
        "collapsed for the variance (see params.json). Screen models helped choose strata.\n"
    )
    return "".join(out)


def write(
    res: dict,
    out_dir: str,
    refs: dict | None = None,
    ref_stats: dict | None = None,
    agreement: dict | None = None,
) -> str:
    os.makedirs(os.path.join(out_dir, "scores"), exist_ok=True)
    _dump(os.path.join(out_dir, "params.json"), res["params"])
    full = dict(res, agreement=agreement, reference_stats=ref_stats)
    _dump(os.path.join(out_dir, "summary.json"), full)
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary_md(res))
    with open(os.path.join(out_dir, "agreement.md"), "w", encoding="utf-8") as f:
        f.write(agreement_md(agreement))
    if refs is not None:
        os.makedirs(os.path.join(out_dir, "reference"), exist_ok=True)
        for part in ("status", "address", "poi", "wz"):
            with open(
                os.path.join(out_dir, "reference", f"{part}.jsonl"),
                "w",
                encoding="utf-8",
            ) as f:
                for k, r in refs.items():
                    rec = {
                        "host": r.get("host", k),
                        "key": k,
                        part: r.get(part),
                        "how": (
                            (r.get("how") or {}).get(part)
                            if isinstance(r.get("how"), dict)
                            else r.get("how")
                        ),
                        "labellers": r.get("labellers"),
                        "double": r.get("double"),
                    }
                    f.write(
                        json.dumps(rec, ensure_ascii=False, default=_default) + "\n"
                    )
        _dump(os.path.join(out_dir, "reference", "stats.json"), ref_stats or {})
    _write_csv(os.path.join(out_dir, "scores", "all.csv"), HEAD, list(_csv_rows(res)))
    for g, r in res["groups"].items():
        r["method"] = res["params"]["method"]
        if g == "address":
            with open(
                os.path.join(out_dir, "scores", "addresses.md"), "w", encoding="utf-8"
            ) as f:
                f.write(addresses_md(r))
            _write_csv(
                os.path.join(out_dir, "scores", "addresses.csv"),
                HEAD,
                [x for x in _csv_rows({"groups": {g: r}})],
            )
        else:
            Lmax = max(
                (
                    int(k.split("@")[1])
                    for c in r["candidates"].values()
                    for k in c["weighted"]
                    if k.startswith("P@")
                ),
                default=0,
            )
            with open(
                os.path.join(out_dir, "scores", f"topics_{g}.md"), "w", encoding="utf-8"
            ) as f:
                f.write(topics_md(g, r, Lmax))
            _write_csv(
                os.path.join(out_dir, "scores", f"topics_{g}.csv"),
                HEAD,
                [x for x in _csv_rows({"groups": {g: r}})],
            )
            with open(
                os.path.join(out_dir, f"depth_{g}.md"), "w", encoding="utf-8"
            ) as f:
                f.write(depth_md(g, r, Lmax))
        _write_csv(
            os.path.join(out_dir, f"pareto_{g}.csv"),
            [
                "candidate",
                "Q",
                "Q_lo",
                "Q_hi",
                "C",
                "cost_axis",
                "failed_rate",
                "p_first",
                "front",
                "passes_filter",
                "eligible",
                "chosen",
                "screen",
            ],
            list(pareto_rows(r)),
        )
    with open(
        os.path.join(out_dir, "scores", "efficiency.md"), "w", encoding="utf-8"
    ) as f:
        f.write(efficiency_md(res))
    _write_csv(
        os.path.join(out_dir, "scores", "efficiency.csv"),
        ["group", "candidate"] + EFF_KEYS,
        [
            [g, n] + [c["efficiency"].get(k) for k in EFF_KEYS]
            for g, r in res["groups"].items()
            for n, c in r["candidates"].items()
        ],
    )
    with open(
        os.path.join(out_dir, "scores", "per_stratum.md"), "w", encoding="utf-8"
    ) as f:
        f.write(per_stratum_md(res))
    with open(os.path.join(out_dir, "paired.md"), "w", encoding="utf-8") as f:
        f.write(paired_md(res))
    return out_dir
