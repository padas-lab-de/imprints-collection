# E49 labelling spec: reference topic labels for the dev sample

Scope: the 200 hosts in `results/E49/dev_hosts.txt`. Input per host: `datasets/E49/dev_inputs.jsonl`
(homepage text, imprint text, title, meta description). You can also open the capture in
`datasets/gold/<host>/` (landing.txt, imprint.txt, landing.png). Label each host once per schema:
POI (`topics/poi_v2.jsonl`) and WZ 2025 (`topics/wz2025.jsonl`).

## Output format
One JSON line per host and schema, in `results/E49/refs/<schema>.jsonl`:

```json
{"host": "example.de", "schema": "poi", "main": "Italienisches Restaurant", "extra": ["Restaurant"],
 "path": ["Essen und Trinken", "Italienisches Restaurant"], "confidence": "high", "note": ""}
```

- `schema`: `poi` or `wz`.
- `main`: node id. POI: the exact `name`. WZ: the `code` (for example `56.11.1`). `null` only if no node fits at all
  (also not a root), or if the site has no usable content (parking page, error page, empty shop template).
- `extra`: at most 2 other node ids that a careful labeller would also accept (see below). Empty list if none.
- `path`: the node ids from the root to `main` (the scorer recomputes it from the schema; it is a check).
- `confidence`: `high` (clear from the text), `medium` (likely, some doubt), `low` (a guess).
- `note`: one short sentence when you stop above a leaf, use `null`, or decide a hard case.

## How to pick the main category
1. Ask: what does the operator of this website primarily do or offer? The site's purpose decides, not
   a topic that the site mentions in passing, not the web designer, hoster or the imprint's legal boilerplate.
   - A company site: the company's main business. A shop: what it sells. An association: its purpose.
     A municipality: the public body. A blog or private homepage: what it is mainly about (POI) and the
     activity (WZ, for example publishing or private household if nothing commercial).
   - Several activities: the one the homepage puts first or gives the most space.
2. Go down the tree from the root and take the deepest node that clearly fits.
   - Prefer the most specific node: "Italienisches Restaurant" over "Restaurant" when the cuisine is clear.
     In POI, general and specific classes are often siblings (Restaurant / Italienisches Restaurant,
     Arzt / Kardiologe, Bar / Cocktailbar). Put the other acceptable sibling in `extra`.
3. Stop at a higher level (an inner node or a root) when the text does not decide between the children,
   or when no child fits. Write why in `note`. Do not guess a leaf.
   - WZ: if a node has exactly one child (for example 56.1 and 56.11 with the same title), either is fine;
     the scorer treats them as the same decision.
4. `extra`: up to 2 alternatives that are also defensible (a second main activity, a general/specific
   sibling, the neighbouring WZ class when the activity sits on a boundary). Do not list loosely related nodes.

## Checks before you hand in
- Every `main` and `extra` id exists in the schema file (run `python3 scripts/E49/score.py` with the refs on any
  prediction file: it reports `unresolved_refs`).
- Exactly one line per host and schema.
- Labels come only from the captured texts and screenshot, not from model predictions of this experiment.
