"""E8-gold-strata-pilot: measure gold-set stratum prevalences on 1,000 random hosts.

Stages (each caches its output, so a stage can be re-run without repeating work):
  sample   draw 1,000 hosts (seed 20261023) from datasets/E4/random20k_seed_hosts.txt
  static   plain HTTP fetch of landing + imprint (requests), headers, redirect chain
  render   headless Chromium: rendered DOM, inner text, screenshots of landing + imprint
  wayback  first capture year from the Wayback CDX API (<= 1 request/s, backoff on 429)
  llm      innkube model judgements (operator type, topic, address in text;
           vision check of imprint screenshots where text has no address)
  features combine everything with src/ic/gold/detectors.py -> results/E8/pilot_features.jsonl

Run from the repository root with a Python that has requests, resiliparse,
playwright, pillow, openai, python-dotenv, e.g.
  PYTHONPATH=src .venv-render/bin/python scripts/gold/e8_pilot.py static
Playwright's Chromium needs system libraries (see docs/gold_set_design.md, "Archive").
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import gzip
import io
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

from ic.gold import detectors as D

ROOT = Path(os.environ.get("IC_DATA_ROOT", "/home/dinzinger/GitHub/imprints-collection"))
DATA = ROOT / "datasets" / "E8"
RES = ROOT / "results" / "E8"
SEED_FILE = ROOT / "datasets" / "E4" / "random20k_seed_hosts.txt"
E4_FILE = ROOT / "datasets" / "E4" / "random20k" / "imprints_batch000000.jsonl.gz"
SEED = 20261023
N = 1000

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 (research crawl, Uni Passau imprints project)"
)
HDRS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Language": "de,en;q=0.5"}
PROBE_PATHS = ["/impressum", "/impressum.html", "/impressum.php", "/imprint"]
TOPICS11 = [
    "Arts and Entertainment", "Business and Professional Services", "Community and Government",
    "Dining and Drinking", "Event", "Health and Medicine", "Landmarks and Outdoors", "Nightlife Spot",
    "Retail", "Sports and Recreation", "Travel and Transportation",
]
OPERATOR_TYPES = ["corporate", "association", "public_body", "sole_trader", "private_person", "unknown"]


def safe(host: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.\-]", "_", host)


def hosts() -> list:
    return [l.strip() for l in open(DATA / "hosts.txt") if l.strip()]


def visible_text(html: str) -> str:
    from resiliparse.extract.html2text import extract_plain_text
    from resiliparse.parse.html import HTMLTree

    try:
        return extract_plain_text(HTMLTree.parse(html), preserve_formatting=True, main_content=False)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
def stage_sample(_args):
    all_hosts = [l.strip() for l in open(SEED_FILE) if l.strip()]
    random.seed(SEED)
    sample = random.sample(all_hosts, N)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "hosts.txt").write_text("\n".join(sample) + "\n")
    print(f"sampled {len(sample)} of {len(all_hosts)}")


# ---------------------------------------------------------------------------
def _get(session, url, timeout=(6, 15)):
    import requests

    try:
        r = session.get(url, headers=HDRS, timeout=timeout, allow_redirects=True, stream=True)
        content = r.raw.read(5_000_000, decode_content=True)
        r._content = content
        return r, None
    except requests.RequestException as e:
        return None, type(e).__name__
    except Exception as e:  # noqa: BLE001
        return None, type(e).__name__


def _decode(r) -> str:
    from charset_normalizer import from_bytes

    if r is None or not r.content:
        return ""
    ctype = r.headers.get("content-type", "")
    if "html" not in ctype and "text" not in ctype and ctype:
        return ""
    try:
        best = from_bytes(r.content[:2_000_000]).best()
        return str(best) if best else r.content.decode("utf-8", "replace")
    except Exception:
        return r.content.decode("utf-8", "replace")


_META_REFRESH = re.compile(
    r"<meta[^>]+http-equiv=[\"']?refresh[^>]+content=[\"']?\s*\d*\s*;?\s*url\s*=\s*[\"']?([^\"'>\s]+)", re.I
)


def static_one(host: str, force: bool = False) -> dict:
    import requests

    out_dir = DATA / "static" / safe(host)
    meta_path = out_dir / "meta.json"
    if meta_path.exists() and not force:
        return json.loads(meta_path.read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.iterdir():  # forced re-fetch: drop old artifacts
        stale.unlink()
    s = requests.Session()
    s.max_redirects = 10
    rec = {"host": host, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    r, err = None, None
    for scheme in ("https://", "http://"):
        r, err = _get(s, scheme + host + "/")
        if r is not None and r.status_code < 500:
            break
    if r is None:
        rec.update(final_url=None, status=None, error=err)
        meta_path.write_text(json.dumps(rec))
        return rec
    html = _decode(r)
    # follow one <meta http-equiv="refresh"> hop, as a browser would
    mr = _META_REFRESH.search(html[:20000]) if len(visible_text(html).strip()) < 1500 else None
    if mr and r.status_code < 400:
        from urllib.parse import urljoin

        r2, _err2 = _get(s, urljoin(r.url, mr.group(1)))
        if r2 is not None and r2.status_code < 400:
            rec["meta_refresh"] = r2.url
            r = r2
            html = _decode(r)
    rec.update(
        final_url=r.url, status=r.status_code, error=None,
        redirects=[h.url for h in r.history],
        headers={k: v for k, v in r.headers.items() if k.lower() in (
            "server", "x-powered-by", "x-generator", "last-modified", "content-type", "set-cookie",
            "x-wix-request-id", "x-shopify-stage", "x-drupal-cache", "x-jimdo-instance", "x-aspnet-version")},
        landing_bytes=len(r.content or b""),
    )
    (out_dir / "landing.html").write_text(html)
    scan = D.scan_html(html, r.url)
    cands = D.find_imprint_links(scan, r.url)
    rec["imprint_candidates"] = [c.__dict__ for c in cands[:5]]
    tried = []
    imprint = None
    fallback = None
    for c in [c for c in cands if c.kind in ("same_host", "other_host")][:4]:
        ri, e = _get(s, c.url)
        tried.append({"url": c.url, "status": ri.status_code if ri is not None else e})
        if ri is not None and ri.status_code == 200:
            ctype = ri.headers.get("content-type", "")
            if "pdf" in ctype:
                imprint = {"url": ri.url, "via": "link", "content_type": ctype, "pdf": True}
                break
            t = _decode(ri)
            if t:
                vt = visible_text(t)
                cand = {"url": ri.url, "via": "link", "content_type": ctype, "pdf": False}
                if D.is_imprint_text(vt) or D.find_addresses(vt):
                    imprint = cand
                    (out_dir / "imprint.html").write_text(t)
                    break
                if fallback is None:
                    fallback = (dict(cand, not_imprint_like=True), t)
    if imprint is None and fallback is not None:
        imprint = fallback[0]
        (out_dir / "imprint.html").write_text(fallback[1])
    if imprint is None and not [c for c in cands if c.kind in ("same_host", "other_host")]:
        base = f"{urlparse(r.url).scheme}://{urlparse(r.url).netloc}"
        for p in PROBE_PATHS:
            ri, e = _get(s, base + p)
            tried.append({"url": base + p, "status": ri.status_code if ri is not None else e})
            if ri is not None and ri.status_code == 200 and ri.url.rstrip("/") != r.url.rstrip("/"):
                t = _decode(ri)
                if t and D.is_imprint_text(visible_text(t)):
                    imprint = {"url": ri.url, "via": "probe", "content_type": ri.headers.get("content-type", ""), "pdf": False}
                    (out_dir / "imprint.html").write_text(t)
                    break
    rec["imprint_tried"] = tried
    rec["imprint"] = imprint
    meta_path.write_text(json.dumps(rec))
    return rec


def retry_hosts() -> list:
    """Hosts whose static landing fetch failed or returned HTTP >= 400."""
    out = []
    for h in hosts():
        p = DATA / "static" / safe(h) / "meta.json"
        st = json.loads(p.read_text()).get("status") if p.exists() else None
        lp = DATA / "static" / safe(h) / "landing.html"
        refresh = lp.exists() and bool(_META_REFRESH.search(lp.read_text(errors="replace")[:20000]))
        if st is None or st >= 400 or refresh:
            out.append(h)
    return out


def stage_static(args):
    hs = retry_hosts() if args.retry else hosts()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(static_one, h, args.retry): h for h in hs}
        for f in as_completed(futs):
            done += 1
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                print("ERR", futs[f], e, file=sys.stderr)
            if done % 100 == 0:
                print(f"static {done}/{len(hs)}", flush=True)


# ---------------------------------------------------------------------------
async def _shot(page, path: Path, max_h=6000):
    try:
        h = await page.evaluate("() => Math.max(document.body ? document.body.scrollHeight : 0, document.documentElement.scrollHeight)")
        h = int(h or 900)
        if h > max_h:
            await page.screenshot(path=str(path), type="jpeg", quality=70, full_page=True, clip={"x": 0, "y": 0, "width": 1280, "height": max_h}, timeout=20000)
        else:
            await page.screenshot(path=str(path), type="jpeg", quality=70, full_page=True, timeout=20000)
        return h
    except Exception as e:  # noqa: BLE001
        return f"err:{type(e).__name__}"


async def _settle(page):
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    await page.wait_for_timeout(800)


async def _text(page) -> str:
    try:
        return await page.inner_text("body", timeout=5000)
    except Exception:
        return ""


def render_retry_hosts() -> list:
    """Hosts whose render failed (no final URL, timeout) or got HTTP >= 400."""
    out = []
    for h in hosts():
        p = DATA / "render" / safe(h) / "meta.json"
        m = json.loads(p.read_text()) if p.exists() else {}
        if not m.get("final_url") or (m.get("status") or 0) >= 400:
            out.append(h)
    return out


async def render_one(browser, host: str, force: bool = False) -> dict:
    out_dir = DATA / "render" / safe(host)
    meta_path = out_dir / "meta.json"
    if meta_path.exists() and not force:
        return json.loads(meta_path.read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.iterdir():  # forced re-render: drop old artifacts
        stale.unlink()
    rec = {"host": host, "rendered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    ctx = await browser.new_context(user_agent=UA, locale="de-DE", viewport={"width": 1280, "height": 900}, ignore_https_errors=True)
    page = await ctx.new_page()
    try:
        resp = None
        for scheme in ("https://", "http://"):
            try:
                resp = await page.goto(scheme + host + "/", wait_until="load", timeout=25000)
                break
            except Exception as e:  # noqa: BLE001
                rec["goto_error"] = type(e).__name__ + ":" + str(e)[:80]
                resp = None
                if "ERR_NAME_NOT_RESOLVED" in str(e):
                    break
        if resp is None and page.url in ("about:blank", ""):
            rec["final_url"] = None
            meta_path.write_text(json.dumps(rec))
            return rec
        await _settle(page)
        rec["final_url"] = page.url
        rec["status"] = resp.status if resp else None
        html = await page.content()
        (out_dir / "landing.html").write_text(html)
        txt = await _text(page)
        (out_dir / "landing.txt").write_text(txt)
        rec["landing_height"] = await _shot(page, out_dir / "landing.jpg")
        scan = D.scan_html(html, page.url)
        cands = D.find_imprint_links(scan, page.url)
        rec["imprint_candidates"] = [c.__dict__ for c in cands[:5]]
        imprint = None
        landing_url = page.url
        fallback = None  # first page that loaded but did not look like an imprint
        on_landing = True
        for c in cands[:4]:
            try:
                if c.kind in ("same_host", "other_host"):
                    if re.search(r"\.pdf($|\?)", c.url, re.I):
                        imprint = {"url": c.url, "via": "link", "kind": c.kind, "pdf": True}
                        break
                    r2 = await page.goto(c.url, wait_until="load", timeout=20000)
                    on_landing = False
                    await _settle(page)
                    if r2 is not None and r2.status < 400:
                        cand = {"url": page.url, "via": "link", "kind": c.kind, "pdf": False, "status": r2.status}
                        t2 = await _text(page)
                        if D.is_imprint_text(t2) or D.find_addresses(t2):
                            imprint = cand
                            break
                        fallback = fallback or cand
                else:  # fragment / javascript: click it (modal or in-page)
                    if not on_landing:
                        await page.goto(landing_url, wait_until="load", timeout=20000)
                        await _settle(page)
                        on_landing = True
                    loc = page.locator("a", has_text=re.compile(r"impressum|imprint", re.I)).first
                    await loc.click(timeout=5000)
                    on_landing = False
                    await page.wait_for_timeout(1500)
                    imprint = {"url": page.url, "via": "click", "kind": c.kind, "pdf": False}
                    break
            except Exception as e:  # noqa: BLE001
                rec.setdefault("imprint_errors", []).append(type(e).__name__)
        if imprint is None and fallback is not None:
            try:
                await page.goto(fallback["url"], wait_until="load", timeout=20000)
                await _settle(page)
                imprint = dict(fallback, not_imprint_like=True)
            except Exception as e:  # noqa: BLE001
                rec.setdefault("imprint_errors", []).append(type(e).__name__)
        if imprint is None and not [c for c in cands if c.kind in ("same_host", "other_host")]:
            base = f"{urlparse(landing_url).scheme}://{urlparse(landing_url).netloc}"
            for p in PROBE_PATHS[:2]:
                try:
                    r2 = await page.goto(base + p, wait_until="load", timeout=15000)
                    await _settle(page)
                    if r2 is not None and r2.status == 200 and D.is_imprint_text(await _text(page)):
                        imprint = {"url": page.url, "via": "probe", "kind": "probe", "pdf": False}
                        break
                except Exception:
                    pass
        rec["imprint"] = imprint
        if imprint and not imprint.get("pdf"):
            (out_dir / "imprint.html").write_text(await page.content())
            (out_dir / "imprint.txt").write_text(await _text(page))
            rec["imprint_height"] = await _shot(page, out_dir / "imprint.jpg")
    except Exception as e:  # noqa: BLE001
        rec["error"] = type(e).__name__ + ":" + str(e)[:120]
    finally:
        await ctx.close()
    meta_path.write_text(json.dumps(rec))
    return rec


async def _render_all(hs, workers, force=False):
    from playwright.async_api import async_playwright

    sem = asyncio.Semaphore(workers)
    done = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--disable-dev-shm-usage"])

        async def run(h):
            nonlocal done, browser
            async with sem:
                try:
                    await asyncio.wait_for(render_one(browser, h, force), timeout=150)
                except Exception as e:  # noqa: BLE001
                    d = DATA / "render" / safe(h)
                    d.mkdir(parents=True, exist_ok=True)
                    if force or not (d / "meta.json").exists():
                        (d / "meta.json").write_text(json.dumps({"host": h, "error": "timeout:" + type(e).__name__}))
                done += 1
                if done % 50 == 0:
                    print(f"render {done}/{len(hs)}", flush=True)

        await asyncio.gather(*(run(h) for h in hs))
        await browser.close()


def stage_render(args):
    if args.retry:
        asyncio.run(_render_all(render_retry_hosts(), args.workers, force=True))
    else:
        asyncio.run(_render_all(hosts(), args.workers))


# ---------------------------------------------------------------------------
def _cdx(session, url):
    q = f"https://web.archive.org/cdx/search/cdx?url={url}&limit=1&output=json&fl=timestamp"
    for attempt in range(5):
        try:
            r = session.get(q, timeout=40, headers={"User-Agent": "imprints-collection research (Uni Passau)"})
        except Exception as e:  # noqa: BLE001
            time.sleep(10 * (attempt + 1))
            err = type(e).__name__
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(30 * (attempt + 1))
            err = f"http{r.status_code}"
            continue
        try:
            rows = r.json()
        except Exception:
            return None, "badjson"
        return (rows[1][0] if len(rows) > 1 else ""), None
    return None, err


def stage_wayback(_args):
    import requests

    path = DATA / "wayback.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(l)["host"] for l in open(path) if l.strip() and json.loads(l).get("error") is None}
    s = requests.Session()
    with open(path, "a") as f:
        for i, h in enumerate(hosts()):
            if h in done:
                continue
            t0 = time.time()
            ts, err = _cdx(s, h)
            queried = [h]
            if ts == "" and err is None:
                alt = h[4:] if h.startswith("www.") else "www." + h
                time.sleep(max(0, 1.05 - (time.time() - t0)))
                t0 = time.time()
                ts, err = _cdx(s, alt)
                queried.append(alt)
            f.write(json.dumps({"host": h, "first_capture": ts, "queried": queried, "error": err}) + "\n")
            f.flush()
            if i % 100 == 0:
                print(f"wayback {i}", flush=True)
            time.sleep(max(0, 1.05 - (time.time() - t0)))


# ---------------------------------------------------------------------------
TEXT_PROMPT = """Du bekommst den Text einer Website (Startseite und, falls gefunden, Impressum).
Antworte nur mit JSON:
{{"imprint_present": true|false,      // enthält der Impressum-Text eine Anbieterkennzeichnung?
 "addresses": [{{"street": "", "number": "", "postcode": "", "town": "", "country": ""}}],  // alle Postanschriften im Impressum-Text, wörtlich
 "operator_name": "",
 "operator_type": one of {ops},
 "topic": one of {topics}}}
operator_type: corporate = Firma/Kapitalgesellschaft/Personengesellschaft; association = Verein, Verband, Stiftung; public_body = Behörde, Kommune, Kirche, Schule, Hochschule; sole_trader = Einzelunternehmer, Freiberufler, Praxis einer Person; private_person = private, nicht-kommerzielle Seite einer Person.
topic: Thema der Website als Ganzes.

STARTSEITE ({landing_url}):
{landing}

IMPRESSUM ({imprint_url}):
{imprint}
"""

VISION_PROMPT = """Dies ist ein Screenshot einer Impressum-Seite. Ist darauf eine Postanschrift (Straße, PLZ, Ort) des Website-Betreibers zu sehen?
Antworte nur mit JSON: {"address_visible": true|false, "address": {"street": "", "number": "", "postcode": "", "town": ""}, "in_image": true|false}
in_image = true, wenn die Anschrift als Bild/Grafik dargestellt ist (nicht als normaler Text)."""


VISION_ALL_PROMPT = """Die Bilder sind aufeinanderfolgende Ausschnitte (von oben nach unten) eines Screenshots einer Impressum-Seite.
Liste ALLE Postanschriften auf, die darauf zu lesen sind (Betreiber, Verantwortliche, Hoster usw.), genau wie geschrieben.
Antworte nur mit JSON: {"addresses": [{"street": "", "number": "", "postcode": "", "town": "", "country": ""}]}
Keine Anschrift zu sehen: {"addresses": []}"""


def _tiles_b64(p: Path, tile_h=1600, max_tiles=3) -> list:
    """Cut a full-page screenshot into up to max_tiles tiles of tile_h px."""
    from PIL import Image

    im = Image.open(p).convert("RGB")
    out = []
    for i in range(max_tiles):
        top = i * tile_h
        if top >= im.height:
            break
        tile = im.crop((0, top, im.width, min(im.height, top + tile_h)))
        buf = io.BytesIO()
        tile.save(buf, format="JPEG", quality=80)
        out.append(base64.b64encode(buf.getvalue()).decode())
    return out


def vision_all_one(client, model, h):
    p = DATA / "render" / safe(h) / "imprint.jpg"
    if not p.exists():
        return {"host": h, "skipped": "no_screenshot"}
    content = [{"type": "text", "text": VISION_ALL_PROMPT}] + [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b}} for b in _tiles_b64(p)
    ]
    try:
        r = client.chat.completions.create(
            model=model, temperature=0, max_tokens=800, messages=[{"role": "user", "content": content}]
        )
        return {"host": h, "vision": _parse_json(r.choices[0].message.content), "raw": r.choices[0].message.content[:1500]}
    except Exception as e:  # noqa: BLE001
        return {"host": h, "vision_error": type(e).__name__ + str(e)[:100]}


def stage_vision_all(args):
    """Read every rendered imprint screenshot; addresses whose postcode is not in
    the DOM text are image-only (screenshot-required)."""
    client = _client()
    hs = [h for h in hosts() if (DATA / "render" / safe(h) / "imprint.jpg").exists()]
    print(f"vision_all: {len(hs)} imprint screenshots")
    _run_parallel(lambda h: vision_all_one(client, args.model, h), hs, DATA / f"vision_all_{args.model}.jsonl", args.workers)


def _client():
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv(ROOT / ".env")
    return OpenAI(base_url=os.environ["MODEL_API_ENDPOINT"], api_key=os.environ["MODEL_API_KEY"], timeout=180)


def _parse_json(s: str):
    s = s or ""
    m = re.search(r"\{.*\}", s, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        try:
            import json_repair  # type: ignore

            return json_repair.loads(m.group(0))
        except Exception:
            return None


def _read(p: Path) -> str:
    return p.read_text(errors="replace") if p.exists() else ""


def llm_one(client, model, h):
    rd = DATA / "render" / safe(h)
    sd = DATA / "static" / safe(h)
    rmeta = json.loads(_read(rd / "meta.json") or "{}")
    smeta = json.loads(_read(sd / "meta.json") or "{}")
    landing = _read(rd / "landing.txt") or visible_text(_read(sd / "landing.html"))
    imprint = _read(rd / "imprint.txt") or visible_text(_read(sd / "imprint.html"))
    out = {"host": h, "model": model}
    if not landing.strip() and not imprint.strip():
        out["skipped"] = "no_text"
        return out
    prompt = TEXT_PROMPT.format(
        ops=OPERATOR_TYPES, topics=TOPICS11,
        landing_url=rmeta.get("final_url") or smeta.get("final_url"), landing=landing[:4000],
        imprint_url=(rmeta.get("imprint") or {}).get("url") or (smeta.get("imprint") or {}).get("url") or "(kein Impressum gefunden; nutze Startseite)",
        imprint=imprint[:10000],
    )
    try:
        r = client.chat.completions.create(model=model, temperature=0, max_tokens=800, messages=[{"role": "user", "content": prompt}])
        out["text"] = _parse_json(r.choices[0].message.content)
        out["text_raw"] = r.choices[0].message.content[:2000]
    except Exception as e:  # noqa: BLE001
        out["text_error"] = type(e).__name__ + str(e)[:100]
    return out


def vision_one(client, model, h):
    from PIL import Image

    p = DATA / "render" / safe(h) / "imprint.jpg"
    if not p.exists():
        return {"host": h, "skipped": "no_screenshot"}
    im = Image.open(p)
    im = im.crop((0, 0, im.width, min(im.height, 3200)))
    if im.height > 2400:
        im = im.resize((int(im.width * 2400 / im.height), 2400))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode()
    try:
        r = client.chat.completions.create(
            model=model, temperature=0, max_tokens=300,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
            ]}],
        )
        return {"host": h, "vision": _parse_json(r.choices[0].message.content), "raw": r.choices[0].message.content[:1000]}
    except Exception as e:  # noqa: BLE001
        return {"host": h, "vision_error": type(e).__name__ + str(e)[:100]}


def _run_parallel(fn, items, path, workers):
    done = set()
    if path.exists():
        done = {json.loads(l)["host"] for l in open(path) if l.strip()}
    todo = [h for h in items if h not in done]
    lock = threading.Lock()
    with open(path, "a") as f, ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(fn, h) for h in todo]
        for i, fu in enumerate(as_completed(futs)):
            res = fu.result()
            with lock:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
                f.flush()
            if i % 100 == 0:
                print(f"{path.name} {i}/{len(todo)}", flush=True)


def stage_llm(args):
    client = _client()
    model = args.model
    _run_parallel(lambda h: llm_one(client, model, h), hosts(), DATA / f"llm_text_{model}.jsonl", args.workers)


def stage_vision(args):
    """Vision check on imprint screenshots: all rendered imprints whose text
    judgement found no address, plus a control sample of 40 with an address."""
    client = _client()
    model = args.model
    texts = {}
    for l in open(DATA / f"llm_text_{model}.jsonl"):
        d = json.loads(l)
        texts[d["host"]] = d
    no_addr, with_addr = [], []
    for h in hosts():
        if not (DATA / "render" / safe(h) / "imprint.jpg").exists():
            continue
        t = (texts.get(h) or {}).get("text") or {}
        has = any((a or {}).get("postcode") or (a or {}).get("street") for a in (t.get("addresses") or []))
        (with_addr if has else no_addr).append(h)
    random.seed(SEED)
    control = random.sample(with_addr, min(40, len(with_addr)))
    print(f"vision: {len(no_addr)} no-address imprints + {len(control)} controls")
    (DATA / "vision_selection.json").write_text(json.dumps({"no_addr": no_addr, "control": control}))
    _run_parallel(lambda h: vision_one(client, model, h), no_addr + control, DATA / f"vision_{model}.jsonl", args.workers)


# ---------------------------------------------------------------------------
def _e4_index():
    idx = {}
    if not E4_FILE.exists():
        return idx
    want = set(hosts())
    with gzip.open(E4_FILE, "rt") as f:
        for l in f:
            d = json.loads(l)
            if d["host"] in want:
                imp = d.get("impressum") or {}
                idx[d["host"]] = {"e4_imprint_found": bool(imp), "e4_imprint_url": imp.get("url")}
    return idx


def _model_has_address(t):
    return any((a or {}).get("postcode") or (a or {}).get("street") for a in ((t or {}).get("addresses") or []))


def stage_features(args):
    model = args.model
    wb = {}
    if (DATA / "wayback.jsonl").exists():
        for l in open(DATA / "wayback.jsonl"):
            d = json.loads(l)
            wb[d["host"]] = d
    llm = {}
    p = DATA / f"llm_text_{model}.jsonl"
    if p.exists():
        for l in open(p):
            d = json.loads(l)
            llm[d["host"]] = d
    vis = {}
    p = DATA / f"vision_{model}.jsonl"
    if p.exists():
        for l in open(p):
            d = json.loads(l)
            vis[d["host"]] = d
    vis_all = {}
    p = DATA / f"vision_all_{model}.jsonl"
    if p.exists():
        for l in open(p):
            d = json.loads(l)
            vis_all[d["host"]] = d
    e4 = _e4_index()
    RES.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(RES / "pilot_features.jsonl", "w") as out:
        for h in hosts():
            sd, rd = DATA / "static" / safe(h), DATA / "render" / safe(h)
            sm = json.loads(_read(sd / "meta.json") or "{}")
            rm = json.loads(_read(rd / "meta.json") or "{}")
            s_html, r_html = _read(sd / "landing.html"), _read(rd / "landing.html")
            s_txt = visible_text(s_html) if s_html else ""
            r_txt = _read(rd / "landing.txt")
            si_html = _read(sd / "imprint.html")
            si_txt = visible_text(si_html) if si_html else ""
            ri_html, ri_txt = _read(rd / "imprint.html"), _read(rd / "imprint.txt")
            final_url = rm.get("final_url") or sm.get("final_url")
            status, status_ev = D.site_status(r_txt or s_txt, final_url, h, sm.get("status"))
            tech = D.detect_tech(s_html or r_html, sm.get("headers") or {}, sm.get("final_url") or final_url or "")
            r_tech = D.detect_tech(r_html, {}, rm.get("final_url") or "") if r_html else None
            if tech["tech"] == "unknown" and r_tech and r_tech["tech"] != "unknown":
                tech = dict(r_tech, signals=["rendered:" + x for x in r_tech["signals"]])
            # imprint reached = page fetched and imprint-like or has an address
            s_hits = D.find_addresses(si_txt) if si_txt else []
            r_hits = D.find_addresses(ri_txt) if ri_txt else []
            s_imp = bool(si_txt) and (D.is_imprint_text(si_txt) or bool(s_hits))
            r_imp = bool(ri_txt) and (D.is_imprint_text(ri_txt) or bool(r_hits))
            landing_is_imp = D.is_imprint_text(r_txt or s_txt) and bool(D.find_addresses(r_txt or s_txt))
            lt = llm.get(h, {}).get("text") or {}
            model_addr = _model_has_address(lt)
            vis_d = (vis.get(h) or {}).get("vision") or {}
            # rendering need uses rule-based address finding on both variants;
            # landing-page imprints count for both
            r_has = bool(r_hits) or (landing_is_imp and bool(r_txt))
            s_has = bool(s_hits) or (D.is_imprint_text(s_txt) and bool(D.find_addresses(s_txt)))
            rneed, rneed_ev = D.rendering_need(len(s_txt.strip()), len(r_txt.strip()), s_imp, r_imp, s_has, r_has,
                static_fetch_ok=(sm.get("status") or 999) < 400,
            )
            r_scan = D.scan_html(ri_html, (rm.get("imprint") or {}).get("url") or "http://x/") if ri_html else None
            shot_cand, shot_ev = D.screenshot_candidate(
                bool(rm.get("imprint")) and not (rm.get("imprint") or {}).get("pdf"), ri_txt, bool(r_hits) or model_addr,
                r_scan.images if r_scan else [],
            )
            r_cands = [D.ImprintCandidate(**c) for c in rm.get("imprint_candidates") or []]
            s_cands = [D.ImprintCandidate(**c) for c in sm.get("imprint_candidates") or []]
            best = r_cands[0] if r_cands else (s_cands[0] if s_cands else None)
            imp_reached = r_imp or s_imp or bool((rm.get("imprint") or {}).get("pdf")) or bool((sm.get("imprint") or {}).get("pdf"))
            loc = D.imprint_location(best if imp_reached else None, landing_is_imp, imp_reached)
            if loc == "probe_only" and ((rm.get("imprint") or {}).get("via") == "probe" or (sm.get("imprint") or {}).get("via") == "probe"):
                loc = "unlinked_probe"
            op_text = ri_txt or si_txt or (r_txt if landing_is_imp else "")
            op_rule, op_toks = D.operator_type_rules(op_text) if op_text else ("unknown", [])
            year = None
            fc = (wb.get(h) or {}).get("first_capture")
            if fc:
                year = int(fc[:4])
            cyears = D.copyright_years(r_txt or s_txt)
            hits_for_flags = r_hits or s_hits
            va = vis_all.get(h)
            va_addrs = ((va or {}).get("vision") or {}).get("addresses") if va else None
            img_only = D.image_only_addresses(va_addrs or [], ri_txt + "\n" + (visible_text(ri_html) if ri_html else "")) if va_addrs is not None else None
            rec = {
                "host": h,
                "tld": D.tld_class(h),
                "site_status": status,
                "site_status_evidence": status_ev,
                "static_status": sm.get("status"),
                "static_error": sm.get("error"),
                "final_url": final_url,
                "render_ok": bool(rm.get("final_url")),
                "tech": tech["tech"],
                "tech_family": tech["family"],
                "spa_framework": tech["spa_framework"],
                "server_lang": tech["server_lang"],
                "generator": tech["generator"],
                "wp_version": D.wordpress_version(tech["generator"]),
                "frameset": tech["frameset"],
                "tech_signals": tech["signals"][:5],
                "wayback_first_capture": fc,
                "wayback_error": (wb.get(h) or {}).get("error"),
                "age_bin": D.age_bin(year) if h in wb else "not_queried",
                "copyright_max_year": max(cyears) if cyears else None,
                "last_modified": (sm.get("headers") or {}).get("Last-Modified") or (sm.get("headers") or {}).get("last-modified"),
                "static_landing_chars": len(s_txt.strip()),
                "rendered_landing_chars": len(r_txt.strip()),
                "static_imprint_reached": s_imp,
                "rendered_imprint_reached": r_imp,
                "imprint_url": (rm.get("imprint") or sm.get("imprint") or {}).get("url"),
                "imprint_pdf": bool((rm.get("imprint") or {}).get("pdf") or (sm.get("imprint") or {}).get("pdf")),
                "imprint_location": loc,
                "landing_is_imprint": landing_is_imp,
                "rendering_need": rneed,
                "rendering_need_evidence": rneed_ev,
                "rule_addresses_static": len(s_hits),
                "rule_addresses_rendered": len(r_hits),
                **D.address_flags(hits_for_flags),
                "obfuscation": D.obfuscation_signals(ri_html or si_html),
                "screenshot_candidate": shot_cand,
                "screenshot_candidate_evidence": shot_ev,
                "vision_address_visible": vis_d.get("address_visible") if vis_d else None,
                "vision_in_image": vis_d.get("in_image") if vis_d else None,
                "vision_all_n_addresses": len(va_addrs) if va_addrs is not None else None,
                "image_only_address": bool(img_only) if img_only is not None else None,
                "image_only_postcodes": img_only or [],
                "operator_type_rule": op_rule,
                "operator_tokens": op_toks[:4],
                "model_imprint_present": lt.get("imprint_present"),
                "model_n_addresses": len([a for a in (lt.get("addresses") or []) if (a or {}).get("postcode") or (a or {}).get("street")]),
                "model_operator_type": lt.get("operator_type"),
                "model_topic": lt.get("topic"),
                "model_addresses": (lt.get("addresses") or [])[:4],
                **(e4.get(h) or {"e4_imprint_found": None, "e4_imprint_url": None}),
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} records to {RES / 'pilot_features.jsonl'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["sample", "static", "render", "wayback", "llm", "vision", "vision_all", "features"])
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--model", default="gemma4-31b-it")
    ap.add_argument("--retry", action="store_true", help="static/render: only hosts whose static fetch failed or gave HTTP >= 400")
    a = ap.parse_args()
    {"sample": stage_sample, "static": stage_static, "render": stage_render, "wayback": stage_wayback,
     "llm": stage_llm, "vision": stage_vision, "vision_all": stage_vision_all, "features": stage_features}[a.stage](a)


if __name__ == "__main__":
    main()
