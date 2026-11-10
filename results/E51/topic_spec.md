# E51 topic labelling: changes to the E49 spec

The rules are in `results/E49/labelling_spec.md` (sections "How to pick the main category", "Checks", and the adjudication rules R1 to R7). Apply R1 to R7 directly in each pass. This file gives only what is different in E51.

## Input
- Hosts: `results/E51/dev2_hosts.txt` (300) and `results/E51/heldout2_hosts.txt` (200).
- Text: `datasets/E51/{dev2,heldout2}_inputs.jsonl` (homepage text, imprint text, title, meta description). These are crawl texts from `ic fetch` (static HTML, main-content extraction), not the rendered gold captures. There is no screenshot.
- Show a host: `python3 -I scripts/E51/show.py <inputs> <host> ...`.
- Label from these texts only. Do not open the web. Do not use model predictions.

## Schemas
- POI: `topics/poi_v3.jsonl`. The node id is the field `id` (English slug, for example `italian-restaurant`). Schema name in the output: `poi3`.
- WZ 2025: `topics/wz2025.jsonl`. The node id is the field `code` (for example `56.11.1`). Schema name: `wz`.
- Search: `python3 -I scripts/E51/nodes.py poi <words>`, `python3 -I scripts/E51/nodes.py wz <words>`; one node with its children: `--node <id>`; WZ includes/excludes: `--node <code> --full`; roots: `--roots`.

## Output (raw pass files)
One JSON line per host and schema. No `path` field (the build script computes it).

```json
{"host": "example.de", "schema": "poi3", "main": "italian-restaurant", "extra": ["restaurant"], "confidence": "high", "note": "", "online_only": false}
{"host": "example.de", "schema": "wz", "main": "56.11.1", "extra": [], "confidence": "high", "note": ""}
```

- `online_only` (POI lines only): rule R4.
- `main` = null only for R1 (no coherent content) or no usable content (parked page, error page, empty template, homepage and imprint both empty). Then `extra` = [] and a note.
- Crawl texts can be empty or short. If the homepage text is empty, use the title, the description and the imprint text. If none of them shows an activity, set main = null with the note "no content".
- Check: `python3 -I scripts/E51/check_part.py poi|wz <part hosts> <part file>`.

## Final reference files
`results/E51/refs/{poi_v3,wz}_{dev2,heldout2}.jsonl`, same fields as `results/E49/heldout/refs/` (adds `path` and `agree_ab`; adjudicated lines have the note "adjudicated: A|B|new; <reason>").
