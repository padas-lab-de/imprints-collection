# Labelling how-to (half page)

Read `docs/annotation_guideline.md` once before you start. This page is only the mechanics.

## Start the tool

From the repository root, with your own ID (L1, L2 or L3):

```
PYTHONPATH=src python -m ic.gold.annotate --labeller L1 --port 8800
```

(or `ic` installed with `pip install -e .`, then without `PYTHONPATH`). Open http://127.0.0.1:8800/ in a browser. The tool reads captures and your assignment from `datasets/gold/` and writes only to `datasets/gold/labels/<your ID>.jsonl`. It opens at your first unlabelled item. If you work on a remote machine, forward the port (`ssh -L 8800:127.0.0.1:8800 host`); do not bind it to a public interface.

## Per item

1. Look at the screenshot (left; tabs landing / imprint; click to zoom) and the DOM text (middle).
2. Fill the form (right) top to bottom: site status, imprint, addresses, operator type, topic, flags, comment.
3. For address fields: select the text in the middle pane, then press the arrow button beside the field. Use "split selection into fields" for a whole address, then check each field. Type only for addresses that exist only in an image.
4. Press **Save & next** (Ctrl+Enter). Errors are shown in red and nothing is saved until they are fixed. Orange warnings (a field is not found in the DOM text) are only hints.
5. Use the live site (header link) only as a fallback; the link ticks `used_live_site` for you. Say why in the comment.

## Good to know

- The first 50 items are the calibration round, the same for all three of us. Do not discuss them until all three are done.
- Go back with Prev or the item list; saving again replaces your earlier label (the file keeps the history). Time is counted while the tab is in focus.
- Close the tool with Ctrl+C; nothing is lost, saves are immediate. Restart it to continue.
- You never see anyone else's labels or any model output. Do not look at them elsewhere.
- Do not edit the files in `datasets/gold/` by hand. Tool problems or guideline questions: write them in the item's comment and tell the project lead.
