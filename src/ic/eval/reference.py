"""Reference (final label per item) from up to three labellers plus adjudication (protocol 2.2, 2.3).

Parts decided separately: ``status`` (site_status + imprint_present), ``address`` (main address or
no address), ``poi`` and ``wz`` (main node, extras, online_only).

Rules per item and part:
- one label: taken as is;
- two labels that agree: taken (address: same street, number, postcode, town after E50 normalisation;
  topics: same canonical path);
- two topic paths where one is a prefix of the other (labellers stop at different depths): an
  adjudicated label if there is one in scope, else ``depth_rule`` ("lcp" = shorter, the longest common
  prefix, protocol default; "deeper" = the longer path);
- two labels that differ otherwise: the adjudicated label if there is one in scope; else the
  ``unresolved`` rule (topics: "lcp" = longest common prefix, may be empty; address and status:
  "primary" = the primary labeller's label; "drop" = no reference for that part);
- calibration items (three labels): the adjudication record is the consensus after discussion; without
  one, a part value shared by two of three labels; topics fall back to the level majority of the three.

``adjudication_scope`` (protocol open item 3): which adjudication records are used.
"disagreements" (default): only where the labels of a part differ; "double": on every item with two or
more labels; "all": on every item, single-labelled ones too (an override file).

``use``: "final" (default) or "first" / "second" = the primary / second raw label on double-labelled
items (single-labelled items keep their label), for the label-noise check of protocol section 6.
"""

from __future__ import annotations

from collections import Counter

from ic.eval._legacy import addr, get_tree, vote
from ic.eval.io import hkey

LIVE_LIKE = ("live", "redirect_other_domain")
PARTS = ("status", "address", "poi", "wz")
TOPIC = ("poi", "wz")
ROLE_ORDER = {"primary": 0, "second": 1, "calibration": 2}


# ---------------------------------------------------------------------------------------------
# Part values
# ---------------------------------------------------------------------------------------------


def status_of(label: dict) -> tuple:
    return (label.get("site_status"), label.get("imprint_present"))


def address_of(label: dict) -> dict:
    """E50 record of the label's main address (``main_index`` None = no address)."""
    AS = addr()
    rec = AS.to_record(
        {
            "addresses": label.get("addresses") or [],
            "main_address_index": label.get("main_address_index"),
            "no_address_reason": label.get("no_address_reason"),
        }
    )
    rec["flags"] = sorted(label.get("flags") or [])
    return rec


def main_address(rec: dict | None) -> dict | None:
    if not rec or rec.get("main_index") is None:
        return None
    return rec["addresses"][rec["main_index"]]


def topic_of(label: dict, schema: str) -> dict | None:
    t = (label.get("topic_labels") or {}).get(schema)
    if t is None:
        return None
    return {
        "main": t.get("main"),
        "extra": list(t.get("extra") or []),
        "online_only": bool(t.get("online_only")),
        "confidence": t.get("confidence"),
    }


def is_live(label: dict) -> bool:
    return label.get("site_status") in LIVE_LIKE


def addr_equal(a: dict, b: dict) -> bool:
    ma, mb = main_address(a), main_address(b)
    if ma is None or mb is None:
        return ma is None and mb is None
    AS = addr()
    return all(
        AS.field_eq(f, ma[f], mb[f]) for f in ("street", "number", "postcode", "town")
    )


def _path(tree, node) -> list:
    return tree.canonical_path(node) if node in tree else []


def lcp(a: list, b: list) -> list:
    out = []
    for x, y in zip(a, b):
        if x != y:
            break
        out.append(x)
    return out


def _topic_from_path(tree, path: list, base: dict | None, others: list) -> dict:
    main = path[-1] if path else None
    extra = []
    for t in [base] + others:
        for e in (t or {}).get("extra", []):
            if e not in extra and e != main:
                extra.append(e)
    return {
        "main": main,
        "extra": extra,
        "online_only": bool((base or {}).get("online_only")),
    }


# ---------------------------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------------------------


def _ordered_labels(
    key: str, labels: dict, assignment: dict
) -> list[tuple[str, str, dict]]:
    """[(labeller, role, label)] ordered primary, second, calibration, then by labeller name."""
    roles = assignment.get(key, {})
    out = []
    for lab, by_host in labels.items():
        if key in by_host:
            out.append(
                (
                    lab,
                    roles.get(lab, "calibration" if len(roles) >= 3 else "primary"),
                    by_host[key],
                )
            )
    out.sort(key=lambda t: (ROLE_ORDER.get(t[1], 3), t[0]))
    if not roles and len(out) == 2:
        out[1] = (out[1][0], "second", out[1][2])
    if not roles and len(out) >= 3:
        out = [(lab, "calibration", lb) for lab, _, lb in out]
    return out


def _adj_part(adj: dict | None, part: str):
    """Part value of an adjudication record, or None if the record does not decide this part."""
    if not adj:
        return None
    parts = adj.get("parts")
    if parts is not None and part not in parts:
        return None
    if part == "status":
        return status_of(adj) if adj.get("site_status") is not None else None
    if part == "address":
        if "addresses" not in adj and "no_address_reason" not in adj:
            return None
        return address_of(adj)
    t = topic_of(adj, part)
    return t


def build_reference(
    keys,
    labels: dict,
    assignment: dict | None = None,
    adjudication: dict | None = None,
    depth_rule: str = "lcp",
    adjudication_scope: str = "disagreements",
    unresolved_topic: str = "lcp",
    unresolved_other: str = "primary",
    use: str = "final",
) -> tuple[dict, dict]:
    """Returns (refs, stats). refs: hkey -> {host, live, status, address, poi, wz, how, labellers,
    double, calibration}. A part is None when it has no reference (no label, dropped, or a topic on a
    site that is not live)."""
    assert depth_rule in ("lcp", "deeper")
    assert adjudication_scope in ("disagreements", "double", "all")
    assert unresolved_topic in ("lcp", "primary", "drop")
    assert unresolved_other in ("primary", "drop")
    assert use in ("final", "first", "second")
    assignment = assignment or {}
    adjudication = adjudication or {}
    trees = {s: get_tree(s) for s in TOPIC}
    stats = {p: Counter() for p in PARTS}
    refs = {}
    for key in keys:
        key = hkey(key)
        labs = _ordered_labels(key, labels, assignment)
        if not labs:
            continue
        calib = any(r == "calibration" for _, r, _ in labs) or len(labs) >= 3
        double = len(labs) >= 2
        if use in ("first", "second") and double and not calib:
            pick = (
                labs[0]
                if use == "first"
                else next((t for t in labs if t[1] == "second"), labs[1])
            )
            labs = [pick]
            double = False
        adj = adjudication.get(key)
        ref = {
            "host": labs[0][2].get("host", key),
            "labellers": [lab for lab, _, _ in labs],
            "double": double,
            "calibration": calib,
            "how": {},
        }
        raw = [lb for _, _, lb in labs]
        for part in PARTS:
            if part == "status":
                vals = [status_of(lb) for lb in raw]
                eq = lambda a, b: a == b  # noqa: E731
            elif part == "address":
                vals = [address_of(lb) for lb in raw]
                eq = addr_equal
            else:
                vals = [topic_of(lb, part) for lb in raw]
                tree = trees[part]
                eq = lambda a, b, t=tree: _path(t, (a or {}).get("main")) == _path(
                    t, (b or {}).get("main")
                )  # noqa
            adj_v = _adj_part(adj, part) if use == "final" else None
            if calib and use == "final":
                val, how = _consensus(part, vals, adj_v, eq, trees.get(part))
            elif len(vals) == 1:
                val, how = vals[0], "single"
                if adj_v is not None and adjudication_scope == "all":
                    val, how = adj_v, "adjudicated"
            else:
                a, b = vals[0], vals[1]
                if eq(a, b):
                    val, how = a, "agree"
                    if adj_v is not None and adjudication_scope in ("double", "all"):
                        val, how = adj_v, "adjudicated"
                elif adj_v is not None:
                    val, how = adj_v, "adjudicated"
                elif part in TOPIC:
                    tree = trees[part]
                    pa, pb = _path(tree, (a or {}).get("main")), _path(
                        tree, (b or {}).get("main")
                    )
                    common = lcp(pa, pb)
                    if common == pa or common == pb:  # one stops above the other
                        p = (
                            common
                            if depth_rule == "lcp"
                            else (pa if len(pa) > len(pb) else pb)
                        )
                        val, how = (
                            _topic_from_path(tree, p, a, [b]),
                            f"depth_{depth_rule}",
                        )
                    elif unresolved_topic == "lcp":
                        val, how = (
                            _topic_from_path(tree, common, a, [b]),
                            "unresolved_lcp",
                        )
                    elif unresolved_topic == "primary":
                        val, how = a, "unresolved_primary"
                    else:
                        val, how = None, "unresolved_drop"
                elif unresolved_other == "primary":
                    val, how = a, "unresolved_primary"
                else:
                    val, how = None, "unresolved_drop"
            ref[part] = val
            ref["how"][part] = how
            stats[part][how] += 1
        st = ref["status"]
        ref["live"] = None if st is None else st[0] in LIVE_LIKE
        for part in TOPIC:
            if ref["live"] is False and ref[part] is not None:
                ref[part] = None
                ref["how"][part] = "not_live"
        refs[key] = ref
    return refs, {p: dict(c) for p, c in stats.items()}


def _consensus(part, vals, adj_v, eq, tree):
    if adj_v is not None:
        return adj_v, "consensus"
    for i in range(len(vals)):
        if sum(eq(vals[i], vals[j]) for j in range(len(vals))) * 2 > len(vals):
            return vals[i], "majority"
    if part in TOPIC:
        node = vote().level_majority(tree, [(v or {}).get("main") for v in vals])
        return (
            _topic_from_path(tree, _path(tree, node), vals[0], vals[1:]),
            "level_majority",
        )
    return vals[0], "unresolved_primary"


def refs_from_e49(path_or_rows, schema: str) -> dict:
    """Pre-built E49 reference file ({host, main, extra, online_only}) -> refs for one schema."""
    from ic.eval.io import read_jsonl

    rows = (
        read_jsonl(path_or_rows) if not isinstance(path_or_rows, list) else path_or_rows
    )
    out = {}
    for r in rows:
        t = {
            "main": r.get("main"),
            "extra": list(r.get("extra") or []),
            "online_only": bool(r.get("online_only")),
        }
        out[hkey(r["host"])] = {
            "host": r["host"],
            "live": True,
            "status": None,
            "address": None,
            "poi": None,
            "wz": None,
            schema: t,
            "how": {schema: "given"},
            "labellers": [],
            "double": False,
            "calibration": False,
        }
    return out


def refs_from_gold(path) -> dict:
    """An already adjudicated gold file (one v3 label per host) -> refs."""
    from ic.eval.io import read_jsonl

    labels = {"gold": {hkey(r["host"]): r for r in read_jsonl(path)}}
    refs, _ = build_reference(list(labels["gold"]), labels)
    return refs
