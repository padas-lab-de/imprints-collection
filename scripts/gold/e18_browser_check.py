#!/usr/bin/env python3
"""End-to-end browser check of the labelling tool (headless Chromium via Playwright).

Builds a scratch data dir (symlinks to a few real captures under datasets/gold plus
a scratch assignment), starts the tool on it, clicks through four items and asserts
the saved JSON lines. Never writes into datasets/gold/labels.

Run from the repo root with a Python that has playwright and a headless Chromium:

    PYTHONPATH=src LD_LIBRARY_PATH=... FONTCONFIG_PATH=... \
        <venv>/bin/python scripts/gold/e18_browser_check.py [--gold datasets/gold]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
POSTCODE = re.compile(r"\b\d{5}\s+[A-ZÄÖÜ][^\n]*")


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def pick_hosts(gold: Path):
    """Choose real captured hosts: with imprint, no imprint, not live, multi-address."""
    rows = [json.loads(line) for line in open(gold / "assignment.jsonl") if line.strip()]
    seen, hosts = set(), []
    for r in rows:
        if r["labeller"] == "L1" and r["host"] not in seen:
            seen.add(r["host"])
            hosts.append(r["host"])
    out = {}
    for h in hosts:
        d = gold / h
        imp = d / "imprint.txt"
        land = d / "landing.txt"
        if not d.is_dir():
            continue
        if imp.is_file() and imp.stat().st_size > 200:
            n = len(POSTCODE.findall(imp.read_text(errors="replace")))
            if n == 1 and "plain" not in out:
                out["plain"] = h
            if n >= 2 and "multi" not in out:
                out["multi"] = h
        elif land.is_file() and land.stat().st_size > 200 and not imp.exists() and "noimp" not in out:
            out["noimp"] = h
        elif not land.exists() and "dead" not in out:
            out["dead"] = h
    return out


def select_postcode_block(pg) -> str | None:
    """Select 'street\\n12345 Town' (or the line with a postcode) in the text pane."""
    return pg.evaluate(
        r"""() => {
      const t = document.querySelector('#txt'); const w = document.createTreeWalker(t, NodeFilter.SHOW_TEXT);
      let n; while ((n = w.nextNode())) {
        const m = n.data.match(/[^\n]*\n?[^\n]*\b\d{5}[ \t]+\S+/);
        if (m) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
                 const s = getSelection(); s.removeAllRanges(); s.addRange(r); return m[0]; } }
      return null; }"""
    )


def last_label(path: Path, host: str):
    rec = None
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if r["host"] == host:
            rec = r
    return rec


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        ok.failed += 1


ok.failed = 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=str(ROOT / "datasets/gold"))
    a = ap.parse_args()
    gold = Path(a.gold)
    picks = pick_hosts(gold)
    print("hosts:", picks)
    need = {"plain", "noimp", "dead", "multi"}
    if need - set(picks):
        print("missing real hosts for:", need - set(picks))
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="e18check_"))
    order = ["plain", "noimp", "dead", "multi"]
    with open(tmp / "assignment.jsonl", "w") as f:
        for i, k in enumerate(order, 1):
            f.write(json.dumps({"item": i, "host": picks[k], "labeller": "L1", "role": "primary", "order": i}) + "\n")
            (tmp / picks[k]).symlink_to(gold / picks[k])
    port = free_port()
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    srv = subprocess.Popen(
        [sys.executable, "-m", "ic.gold.annotate", "--labeller", "L1", "--port", str(port), "--data-dir", str(tmp)],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}/"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(base + "api/state")
                break
            except Exception:
                time.sleep(0.2)
        labels = tmp / "labels" / "L1.jsonl"
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1600, "height": 1400})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            dialogs = []
            pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
            pg.goto(base, wait_until="networkidle")
            pg.wait_for_selector("#f fieldset")

            def save(next_=False):
                pg.get_by_role("button", name="Save & next (Ctrl+Enter)" if next_ else "Save", exact=True).click()
                pg.wait_for_timeout(600)

            # ---- item 1: plain imprint, one address via selection + split -----------
            h = picks["plain"]
            ok(pg.inner_text("#host") == h, "starts at first unlabelled item " + h)
            pg.get_by_label("live", exact=True).check()
            pg.get_by_label("yes", exact=True).check()
            pg.locator("#textpane button", has_text="imprint").click()
            pg.get_by_role("button", name="+ add address").click()
            sel = select_postcode_block(pg)
            ok(sel is not None, "selected an address block: " + repr(sel))
            pg.locator("button.pick", has_text="split").first.click()
            ok(pg.locator("input[name=main]").first.is_checked(), "first address is main by default")
            ok(not pg.get_by_label("none of these", exact=False).is_checked(), "'none of these' unchecked")
            pc = pg.locator(".addr .row:has(span.k:text-is('postcode')) input").input_value()
            ok(re.fullmatch(r"\d{5}", pc) is not None, "postcode filled by split: " + pc)
            pg.get_by_label("corporate", exact=True).check()
            pg.locator("#f select").last.select_option("Business and Professional Services")
            # rejected save: URL / where empty -> visible message
            save()
            ok(pg.locator("#errbox").is_visible() and "Not saved" in pg.inner_text("#errbox"), "rejected save shows a message")
            ok(not labels.exists(), "nothing written on rejected save")
            pg.locator("#f input[type=text]").first.fill(f"https://{h}/impressum")
            pg.locator("#f fieldset:has(legend:has-text('2. Imprint')) select").select_option("separate_page")
            pg.locator("input[name=main]").first.check()
            save()
            ok(not pg.locator("#errbox").is_visible(), "message cleared after good save")
            rec = last_label(labels, h)
            ok(rec is not None and rec["main_address_index"] == 0 and rec["no_address_reason"] is None, "label saved with main address")
            ok(rec and rec["addresses"][0]["postcode"] == pc and rec["addresses"][0]["evidence"], "address fields + evidence saved")
            ok(rec and rec["operator_type"] == "corporate" and rec["annotator"] == "L1" and rec["capture_id"], "operator, annotator, capture_id saved")
            pg.get_by_role("button", name="Next", exact=False).first.click()

            # ---- item 2: live site without imprint (negative) -----------------------
            h = picks["noimp"]
            pg.wait_for_function("document.querySelector('#host').textContent === '%s'" % h)
            pg.get_by_label("live", exact=True).check()
            pg.get_by_label("no", exact=True).check()
            ok("no_imprint" in pg.inner_text("#f"), "form shows automatic reason no_imprint")
            pg.get_by_label("unclear", exact=True).check()
            pg.locator("#f select").last.select_option("Retail")
            save()
            rec = last_label(labels, h)
            ok(rec and rec["no_address_reason"] == "no_imprint" and rec["addresses"] == [] and rec["imprint_location"] == "none", "negative saved: " + str(rec and rec["no_address_reason"]))
            pg.get_by_role("button", name="Next", exact=False).first.click()

            # ---- item 3: not live ---------------------------------------------------
            h = picks["dead"]
            pg.wait_for_function("document.querySelector('#host').textContent === '%s'" % h)
            pg.get_by_label("unreachable", exact=True).check()
            ok(pg.locator("fieldset", has_text="Operator type").count() == 0, "operator/topic hidden for dead site")
            save()
            rec = last_label(labels, h)
            ok(rec and rec["no_address_reason"] == "site_dead" and rec["site_status"] == "unreachable", "dead site saved")
            pg.get_by_role("button", name="Next", exact=False).first.click()

            # ---- item 4: multi-address ---------------------------------------------
            h = picks["multi"]
            pg.wait_for_function("document.querySelector('#host').textContent === '%s'" % h)
            pg.get_by_label("live", exact=True).check()
            pg.get_by_label("yes", exact=True).check()
            pg.locator("#textpane button", has_text="imprint").click()
            for i in range(2):
                pg.get_by_role("button", name="+ add address").click()
                sel = select_postcode_block(pg)
                if i == 1:  # second address: take the next postcode block
                    pg.evaluate(
                        r"""() => {
                      const t = document.querySelector('#txt'); const w = document.createTreeWalker(t, NodeFilter.SHOW_TEXT);
                      let n, k = 0; while ((n = w.nextNode())) { const re = /[^\n]*\n?[^\n]*\b\d{5}[ \t]+\S+/g; let m;
                        while ((m = re.exec(n.data))) { if (++k === 2) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
                          const s = getSelection(); s.removeAllRanges(); s.addRange(r); return; } } } }"""
                    )
                pg.locator("button.pick", has_text="split").nth(i).click()
            ok(pg.locator(".addr").count() == 2, "two address cards")
            pg.locator("input[name=main]").nth(1).check()
            ok(pg.locator("input[name=main]").nth(1).is_checked(), "main radio can be moved to address 2")
            pg.locator("input[name=main]").nth(0).check()
            ok(pg.get_by_label("multi_address", exact=True).is_checked(), "multi_address flag auto-ticked for two operator addresses")
            pg.locator("#f input[type=text]").first.fill(f"https://{h}/impressum")
            pg.locator("#f fieldset:has(legend:has-text('2. Imprint')) select").select_option("separate_page")
            pg.get_by_label("corporate", exact=True).check()
            pg.locator("#f select").last.select_option("Business and Professional Services")
            save()
            rec = last_label(labels, h)
            ok(rec and len(rec["addresses"]) == 2 and rec["main_address_index"] == 0 and "multi_address" in rec["flags"], "multi-address label saved with flag")
            ok(not [d for d in dialogs if "Discard" in d], "no unexpected discard dialog")
            errs = [e for e in errs if "status of 400" not in e]  # the deliberately rejected save
            ok(not errs, "no JS errors: " + str(errs))
            # reload resumes after the last labelled item and keeps labels
            n_done = len({json.loads(l)["host"] for l in labels.read_text().splitlines()})
            ok(n_done == 4, f"{n_done} items labelled")
            b.close()
    finally:
        srv.terminate()
    print("FAILED" if ok.failed else "ALL PASSED", ok.failed)
    return 1 if ok.failed else 0


if __name__ == "__main__":
    sys.exit(main())
