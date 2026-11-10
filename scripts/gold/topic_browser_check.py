#!/usr/bin/env python3
"""End-to-end browser check of the topic picker (sections 5a POI v3 and 5b WZ 2025) in the gold labelling tool.

Uses a temp data dir with two tiny live-site items (no real captures needed), drives headless
Chromium via Playwright, asserts the stored JSON lines and takes screenshots of the topic section.
With --gold it also runs the old address workflow check (e18_browser_check.py) afterwards.

    PYTHONPATH=src <venv>/bin/python scripts/gold/topic_browser_check.py [--gold datasets/gold] \
        [--shots results/gold/topic_browser_check]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e18_browser_check import ROOT, free_port, last_label, ok  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

HOSTS = ["zahnarzt-beispiel.de", "baeckerei-beispiel.de"]
SELECT_POSTCODE = r"""() => { const t = document.querySelector('#txt'); const w = document.createTreeWalker(t, NodeFilter.SHOW_TEXT);
  let n; while ((n = w.nextNode())) { const m = n.data.match(/[^\n]*\n?[^\n]*\b\d{5}[ \t]+\S+/); if (m) {
    const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r); return; } } }"""


def build_data(tmp: Path) -> None:
    rows = []
    for i, h in enumerate(HOSTS, 1):
        (tmp / h).mkdir()
        (tmp / h / "imprint.txt").write_text(f"Impressum\nMusterstr. 1\n94032 Passau\n{h}\n", encoding="utf-8")
        (tmp / h / "landing.txt").write_text("Willkommen", encoding="utf-8")
        (tmp / h / "meta.json").write_text(json.dumps({"captured_at": "2026-11-05T10:12:03Z"}))
        rows.append({"item": i, "host": h, "labeller": "L1", "role": "primary", "order": i})
    (tmp / "assignment.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def node_name(base: str, sch: str, nid: str) -> str:
    """The bold name the picker shows for a node (mirrors nodeName() in page.html)."""
    url = f"{base}api/topic_search?schema={sch}&id={urllib.parse.quote(nid)}"
    n = json.load(urllib.request.urlopen(url))["results"][0]
    if sch == "wz":
        return f"{n['id']} {n['title']}"
    return f"{n['title']} / {n['de']}" if n.get("de") else n["title"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=None, help="real captures for the old e18 check (skipped if absent)")
    ap.add_argument("--shots", default=str(ROOT / "results/gold/topic_browser_check"))
    a = ap.parse_args()
    shots = Path(a.shots)
    shots.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="topiccheck_"))
    build_data(tmp)
    port = free_port()
    srv = subprocess.Popen(
        [sys.executable, "-m", "ic.gold.annotate", "--labeller", "L1", "--port", str(port), "--data-dir", str(tmp)],
        cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}/"
    labels = tmp / "labels" / "L1.jsonl"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(base + "api/state")
                break
            except Exception:
                time.sleep(0.2)
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1600, "height": 1500})
            errs: list[str] = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("dialog", lambda d: d.accept())
            pg.goto(base, wait_until="networkidle")
            pg.wait_for_selector("#f fieldset")

            def fs(sch):
                return pg.locator("#f fieldset", has=pg.locator("legend", has_text="5a." if sch == "poi" else "5b."))

            def hit(sch, query, nid):
                """Type the query, click the hit that shows node nid."""
                f = fs(sch)
                f.locator("input.q").first.fill(query)
                f.locator("button.hit").first.wait_for()
                name = re.compile("^" + re.escape(node_name(base, sch, nid)) + "$")
                f.locator("button.hit", has=pg.locator("b", has_text=name)).first.click()
                pg.wait_for_timeout(250)

            def sels(sch):
                return fs(sch).locator(".sel").all_inner_texts()

            def shot(name):
                """Screenshot of the topic section (5a + 5b); the error-box shot also includes the label pane header."""
                pg.evaluate("document.querySelector('#formbody').scrollTop = 0")
                fs("poi").scroll_into_view_if_needed()
                if name.endswith("error_box"):
                    pg.locator("#labelpane").screenshot(path=str(shots / f"{name}.png"))
                    return
                a_, b_ = fs("poi").bounding_box(), fs("wz").bounding_box()
                pad = 8
                pg.screenshot(path=str(shots / f"{name}.png"), clip={
                    "x": a_["x"] - pad, "y": a_["y"] - pad, "width": a_["width"] + 2 * pad,
                    "height": b_["y"] + b_["height"] - a_["y"] + 2 * pad})

            def clear(sch, n=0):
                fs(sch).locator(".sel button.chip").nth(n).click()
                pg.wait_for_timeout(150)

            def note():
                loc = pg.locator("#f .tpnote:not(.hint)")
                return loc.inner_text() if loc.count() else ""

            def conf(sch, v):
                fs(sch).locator(f".chip[data-v='{v}']").click()

            def pressed(sch, text):
                return fs(sch).locator("button.chip", has_text=text).get_attribute("aria-pressed") == "true"

            def save():
                pg.get_by_role("button", name="Save", exact=True).click()
                pg.wait_for_timeout(600)

            def loaded():
                pg.wait_for_function("!document.querySelector('#f').innerText.includes('loading path')")

            def basics(h):
                pg.locator("#f .chip[data-v='live']").click()
                pg.locator("#f .chip[data-v='true']").click()
                pg.locator("#f input[data-k=imprint_url]").fill(f"https://{h}/impressum")
                pg.locator("#f .chip[data-v='separate_page']").click()
                pg.locator("#textpane button", has_text="imprint").click()
                pg.get_by_role("button", name="+ add address").click()
                pg.evaluate(SELECT_POSTCODE)
                pg.locator("button.pick", has_text="split").first.click()
                pg.locator("#f .chip[data-v='corporate']").click()
                pg.locator("#f .chip[data-v='Business and Professional Services']").click()

            # ---- item 1 -------------------------------------------------------------
            h = HOSTS[0]
            ok(pg.inner_text("#host") == h, "starts at " + h)
            pg.locator("#f .chip[data-v='live']").click()
            ok(fs("poi").count() == 1 and fs("wz").count() == 1, "both topic sections (5a, 5b) shown for a live site")
            basics(h)
            shot("01_empty")

            # POI: Zahnarzt -> dentist as main
            hit("poi", "Zahnarzt", "dentist")
            s = sels("poi")
            ok(len(s) == 1 and "dentist" in s[0].lower() and "health" in s[0].lower() and "(leaf)" in s[0],
               "POI 'Zahnarzt' -> dentist is main; path and leaf shown")
            ok("add extra label (0/2" in fs("poi").inner_text().lower(), "extra search offered after main (0/2)")
            clear("poi")
            ok(len(sels("poi")) == 0 and fs("poi").locator("input.q").count() == 1, "x on main clears it, search shown again")
            # inner node as main, then replace it
            hit("poi", "restaurant", "restaurant")
            s = sels("poi")
            ok(len(s) == 1 and "(inner node)" in s[0], "POI 'restaurant' -> inner node accepted as main")
            clear("poi")
            hit("poi", "thai", "thai-restaurant")
            ok(len(sels("poi")) == 1 and "thai" in sels("poi")[0].lower() and "(leaf)" in sels("poi")[0], "inner main replaced by thai-restaurant")
            # extras
            hit("poi", "Zahnarzt", "dentist")
            ok(len(sels("poi")) == 2, "extra 1 (dentist) added")
            hit("poi", "restaurant", "restaurant")  # ancestor of the main
            ok(len(sels("poi")) == 2 and "R5" in note() and "Not added" in note(), "ancestor of main refused with R5 message: " + note())
            shot("02_r5_refused")
            hit("poi", "italian restaurant", "italian-restaurant")
            ok(len(sels("poi")) == 3 and note() == "", "extra 2 (italian-restaurant) added, note cleared")
            ok(fs("poi").locator("input.q").count() == 0, "third extra refused: no extra search offered at 2/2")
            shot("03_two_extras")
            # change main so extra 1 (dentist) becomes invalid
            clear("poi", 0)
            ok(fs("poi").locator("input.q").count() == 1, "main cleared; search shown")
            hit("poi", "Zahnarzt", "dentist")
            s = sels("poi")
            ok(len(s) == 2 and "dentist" in s[0].lower() and "italian" in s[1].lower(),
               "extra equal to the new main removed, other extra kept")
            ok("removed" in note() and "R5" in note(), "removal note shown: " + note())
            shot("04_extra_removed")
            conf("poi", "high")
            fs("poi").locator("button.chip", has_text="online only").click()
            ok(pressed("poi", "online only"), "online_only toggled on")

            # WZ: 56.1, Bäckerei / baeckerei
            f = fs("wz")
            f.locator("input.q").first.fill("56.1")
            f.locator("button.hit").first.wait_for()
            ok(f.locator("button.hit b").first.inner_text().startswith("56.1 "), "WZ '56.1' finds 56.1 first")
            f.locator("input.q").first.fill("baeckerei")
            pg.wait_for_timeout(600)
            hits_ae = f.locator("button.hit b").all_inner_texts()
            f.locator("input.q").first.fill("Bäckerei")
            pg.wait_for_timeout(600)
            hits_uml = f.locator("button.hit b").all_inner_texts()
            ok(bool(hits_ae) and hits_ae == hits_uml, "WZ 'baeckerei' and 'Bäckerei' give the same hits: " + str(hits_ae[:2]))
            hit("wz", "56.1", "56.1")
            ok(len(sels("wz")) == 1 and "(inner node)" in sels("wz")[0], "WZ main 56.1 (inner node)")
            hit("wz", "Bäckerei", "10.71.0")
            ok(len(sels("wz")) == 2 and "10.71.0" in sels("wz")[1], "WZ extra 10.71.0 added")
            conf("wz", "medium")
            ok(fs("poi").locator(".chip.on[data-v='high']").count() == 1 and fs("wz").locator(".chip.on[data-v='medium']").count() == 1,
               "confidences set (poi high, wz medium)")
            shot("05_wz_filled")
            save()
            ok(pg.locator("#errbox").is_hidden(), "save accepted, no error box")
            rec = last_label(labels, h)
            tl = (rec or {}).get("topic_labels")
            ok(bool(rec) and rec["schema_version"] == 2, "stored schema_version 2")
            want = {"poi": {"main": "dentist", "extra": ["italian-restaurant"], "confidence": "high", "note": "", "online_only": True},
                    "wz": {"main": "56.1", "extra": ["10.71.0"], "confidence": "medium", "note": ""}}
            ok(tl == want, "stored topic_labels as picked: " + json.dumps(tl))

            # reload: the picks come back
            pg.reload(wait_until="networkidle")
            pg.wait_for_selector("#f fieldset")
            if pg.inner_text("#host") != h:  # reload resumes at the next unlabelled item: go back
                pg.locator("#prev").click()
                pg.wait_for_function("document.querySelector('#host').textContent === '%s'" % h)
            loaded()
            s1, s2 = sels("poi"), sels("wz")
            ok(len(s1) == 2 and "dentist" in s1[0].lower() and "italian" in s1[1].lower()
               and len(s2) == 2 and "56.1" in s2[0] and "10.71.0" in s2[1], "saved picks shown again after reload")
            ok(fs("poi").locator(".chip.on[data-v='high']").count() == 1 and fs("wz").locator(".chip.on[data-v='medium']").count() == 1
               and pressed("poi", "online only"), "confidences and online_only restored")
            shot("06_after_reload")

            # ---- item 2: no WZ main, no note -> error; then a note -> saved ---------------
            pg.locator("#next").click()
            h = HOSTS[1]
            pg.wait_for_function("document.querySelector('#host').textContent === '%s'" % h)
            basics(h)
            hit("poi", "bakery", "bakery")
            conf("poi", "medium")
            conf("wz", "low")
            n0 = len(labels.read_text().splitlines())
            save()
            err = pg.inner_text("#errbox") if pg.locator("#errbox").is_visible() else ""
            ok("Not saved" in err and "no main label" in err, "save without WZ main and note -> error box: " + err.replace("\n", " | "))
            ok(len(labels.read_text().splitlines()) == n0, "nothing written on the rejected save")
            shot("07_error_box")
            fs("wz").locator("input[type=text]").last.fill("Webshop ohne passenden WZ-Code")
            save()
            ok(pg.locator("#errbox").is_hidden(), "error box gone once a note is given")
            rec = last_label(labels, h)
            ok(bool(rec) and rec["topic_labels"]["wz"]["main"] is None and rec["topic_labels"]["wz"]["note"].startswith("Webshop")
               and rec["topic_labels"]["poi"]["main"] == "bakery", "stored: WZ main null + note, POI main bakery")
            errs = [e for e in errs if "status of 400" not in e]
            ok(not errs, "no JS errors: " + str(errs))
            b.close()
    finally:
        srv.terminate()
        srv.wait(timeout=10)
    if a.gold:
        print("--- old e18 address workflow ---")
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("e18_browser_check.py")), "--gold", a.gold],
                           cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")))
        ok(r.returncode == 0, "old e18 address workflow check")
    print("FAILED" if ok.failed else "ALL PASSED", ok.failed)
    return 1 if ok.failed else 0


if __name__ == "__main__":
    sys.exit(main())
