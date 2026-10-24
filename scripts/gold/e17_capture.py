"""E17-gold-capture: freeze the gold-set items (docs/gold_set_design.md section 3).

Per host, writes datasets/gold/<host>/ with
  landing.static.html, imprint.static.html   plain HTTP GET (same client as the E8/E12 screening)
  landing.dom.html, imprint.dom.html         Playwright Chromium, networkidle + 2 s, page.content()
  landing.txt, imprint.txt                   document.body.innerText of the rendered page
  landing.png, imprint.png                   full-page screenshot, 1280 px wide, at most 20,000 px tall
  imprint.pdf                                the file itself, if the imprint is a PDF
  meta.json                                  provenance; written last, "complete": true marks a finished item
No WARC files.

Imprint URL: the E12 link detection (ic.gold.detectors.find_imprint_links on the rendered landing DOM, the
first candidate that looks like an imprint; /impressum probes only when there is no link). If the render finds
none, the URL found by the static fetch is used. If there is none, only the landing page is captured.

Cookie banners: a visible button whose text equals one of CONSENT_REJECT_LABELS is clicked; otherwise the
banner is left alone. The action is recorded in meta.json.

Politeness: at most 2 concurrent items per resolved /24 (IPv6 /48), 1 s rest between items of one group,
8 workers (browser pages) by default. Hosts that resolve into 81.169.145.0/24 (Strato, blocked from the crawl
VM) are not captured but written to deferred_strato.txt; pass --no-strato-filter on another machine.

  PYTHONPATH=src LD_LIBRARY_PATH=<render libs> <venv-render>/bin/python scripts/gold/e17_capture.py \
      [--hosts file] [--workers 8] [--retry-failed] [--limit N]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import ipaddress
import json
import os
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(os.environ.get("IC_DATA_ROOT", "/home/dinzinger/GitHub/imprints-collection"))
OUT = ROOT / "datasets" / "gold"
SAMPLE = ROOT / "datasets" / "E12" / "gold_sample.jsonl"

STRATO_NET = ipaddress.ip_network("81.169.145.0/24")
PER_GROUP = 2
GROUP_GAP = 1.0
VIEWPORT = {"width": 1280, "height": 900}
MAX_SHOT_H = 20_000
ITEM_TIMEOUT = 300
PDF_MAX = 25_000_000

CONSENT_REJECT_LABELS = [
    "ablehnen", "alle ablehnen", "alles ablehnen", "cookies ablehnen", "alle cookies ablehnen",
    "ich lehne ab", "nicht zustimmen", "ablehnen und schliessen", "ablehnen und schließen",
    "nur notwendige", "nur notwendige cookies", "nur notwendige akzeptieren", "nur notwendige cookies akzeptieren",
    "nur notwendige cookies zulassen", "nur notwendige zulassen",
    "nur essenzielle", "nur essenzielle cookies", "nur essentielle", "nur essentielle cookies",
    "nur essenzielle cookies akzeptieren", "nur erforderliche", "nur erforderliche cookies",
    "nur technisch notwendige", "nur technisch notwendige cookies", "nur technisch notwendige cookies akzeptieren",
    "nur funktionale cookies", "nur funktionale", "nur notwendiges", "notwendige cookies",
    "weiter ohne zustimmung", "weiter ohne einwilligung", "ohne zustimmung fortfahren", "ohne einwilligung fortfahren",
    "reject", "reject all", "decline", "decline all", "deny", "deny all", "refuse", "refuse all",
    "only necessary", "only necessary cookies", "only essential", "only essential cookies",
    "necessary only", "essential only", "continue without accepting",
]

_spec = importlib.util.spec_from_file_location("e8_pilot", Path(__file__).with_name("e8_pilot.py"))
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)
D = E.D


# ---------------------------------------------------------------------------
# pure helpers (unit-tested without network)
def norm_label(text: str) -> str:
    """Lower-case, collapse whitespace, drop surrounding punctuation/symbols (ticks, arrows, quotes)."""
    t = re.sub(r"\s+", " ", (text or "").strip().lower())
    return re.sub(r"^[^\w]+|[^\w]+$", "", t)


def is_reject_label(text: str) -> bool:
    return norm_label(text) in set(CONSENT_REJECT_LABELS)


def pick_reject(texts: list) -> int | None:
    """Index of the first text that is a reject label, else None."""
    for i, t in enumerate(texts):
        if is_reject_label(t):
            return i
    return None


def in_strato(ips: list) -> bool:
    for ip in ips:
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if a.version == 4 and a in STRATO_NET:
            return True
    return False


def provider_key(ips: list) -> str | None:
    v4 = [i for i in ips if ":" not in i]
    if v4:
        return str(ipaddress.ip_network(v4[0] + "/24", strict=False))
    if ips:
        return str(ipaddress.ip_network(ips[0] + "/48", strict=False))
    return None


def host_dir(host: str, out: Path = OUT) -> Path:
    return out / E.safe(host)


def is_complete(d: Path, retry_failed: bool = False) -> bool:
    """A capture is done if meta.json parses, says complete, and every file it lists exists.
    With retry_failed, failed captures count as not done."""
    p = Path(d) / "meta.json"
    try:
        m = json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return False
    if not m.get("complete"):
        return False
    if retry_failed and str(m.get("outcome", "")).startswith("failed"):
        return False
    return all((Path(d) / f).exists() for f in m.get("files", []))


def interleave(items: list, group_of: dict) -> list:
    """Round-robin over provider groups so a big group does not block the queue head."""
    buckets: dict = {}
    for h in items:
        buckets.setdefault(group_of.get(h) or ("_none", h), []).append(h)
    out, i = [], 0
    lists = sorted(buckets.values(), key=len, reverse=True)
    while lists:
        for lst in lists:
            out.append(lst[i])
        i += 1
        lists = [l for l in lists if len(l) > i]
    return out


class GroupScheduler:
    """At most `cap` items in flight per group, `gap` seconds of rest after an item of a group."""

    def __init__(self, items, group_of, cap=PER_GROUP, gap=GROUP_GAP):
        self.group_of, self.cap, self.gap = group_of, cap, gap
        self.active: dict = {}
        self.next_ok: dict = {}
        self.pending = interleave(list(items), group_of)

    def pick(self, now=None):
        now = time.monotonic() if now is None else now
        for i, h in enumerate(self.pending):
            g = self.group_of.get(h)
            if g is None or (self.active.get(g, 0) < self.cap and self.next_ok.get(g, 0) <= now):
                self.pending.pop(i)
                if g is not None:
                    self.active[g] = self.active.get(g, 0) + 1
                    self.next_ok[g] = now + self.gap  # gap between starts of the same group
                return h
        return None

    def release(self, h):
        g = self.group_of.get(h)
        if g is not None:
            self.active[g] -= 1


def failure_reason(host: str, dns: dict, render_error: str | None, landing: dict) -> str:
    """Short label for why no landing page could be captured."""
    if (dns.get(host) or {}).get("error"):
        return "no_dns"
    for s in (landing.get("goto_error"), render_error):
        m = re.search(r"(ERR_[A-Z_]+)", s or "")
        if m:
            return m.group(1).lower()
    if render_error:
        return "item_timeout" if "Timeout" in render_error else render_error.split(":")[0][:40]
    se = (landing.get("static") or {}).get("error")
    return (se or "no_response")[:40]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# DNS
def resolve(h: str) -> dict:
    try:
        infos = socket.getaddrinfo(h, 443, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos}, key=lambda x: (":" in x, x))
        return {"host": h, "ips": ips[:6], "group": provider_key(ips), "strato": in_strato(ips), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"host": h, "ips": [], "group": None, "strato": False, "error": type(e).__name__}


# ---------------------------------------------------------------------------
# static phase (blocking, runs in a thread)
def static_phase(host: str) -> dict:
    import requests

    s = requests.Session()
    s.max_redirects = 10
    res: dict = {"started": now_iso(), "landing": {}, "imprint": None, "files": {}}
    r, err = None, None
    for scheme in ("https://", "http://"):
        r, err = E._get(s, scheme + host + "/")
        if r is not None and r.status_code < 500:
            break
    if r is None:
        res["landing"] = {"error": err}
        return res
    html = E._decode(r)
    mr = E._META_REFRESH.search(html[:20000]) if len(E.visible_text(html).strip()) < 1500 else None
    meta_refresh = None
    if mr and r.status_code < 400:
        from urllib.parse import urljoin

        r2, _ = E._get(s, urljoin(r.url, mr.group(1)))
        if r2 is not None and r2.status_code < 400:
            meta_refresh, r, html = r2.url, r2, E._decode(r2)
    res["landing"] = {
        "final_url": r.url, "status": r.status_code, "meta_refresh": meta_refresh,
        "redirects": [{"url": h.url, "status": h.status_code} for h in r.history],
        "headers": dict(r.headers), "bytes": len(r.content or b""),
    }
    res["files"]["landing.static.html"] = html
    scan = D.scan_html(html, r.url)
    cands = D.find_imprint_links(scan, r.url)
    tried, imprint, fallback = [], None, None
    for c in [c for c in cands if c.kind in ("same_host", "other_host")][:4]:
        ri = static_imprint_fetch(s, c.url, tried)
        if ri is None:
            continue
        if ri["pdf"]:
            imprint = ri
            break
        vt = E.visible_text(ri["html"])
        if D.is_imprint_text(vt) or D.find_addresses(vt):
            imprint = ri
            break
        fallback = fallback or dict(ri, not_imprint_like=True)
    imprint = imprint or fallback
    if imprint is None and not [c for c in cands if c.kind in ("same_host", "other_host")]:
        u = urlparse(r.url)
        for p in E.PROBE_PATHS:
            ri = static_imprint_fetch(s, f"{u.scheme}://{u.netloc}{p}", tried)
            if ri and not ri["pdf"] and ri["url"].rstrip("/") != r.url.rstrip("/") and D.is_imprint_text(E.visible_text(ri["html"])):
                imprint = dict(ri, via="probe")
                break
    res["tried"] = tried
    if imprint is not None:
        res["imprint"] = imprint
    res["session"] = s
    return res


def static_imprint_fetch(s, url: str, tried: list) -> dict | None:
    ri, e = E._get(s, url)
    tried.append({"url": url, "status": ri.status_code if ri is not None else e})
    if ri is None or ri.status_code != 200:
        return None
    ctype = ri.headers.get("content-type", "")
    rec = {
        "url": ri.url, "via": "link", "status": ri.status_code, "content_type": ctype, "headers": dict(ri.headers),
        "redirects": [{"url": h.url, "status": h.status_code} for h in ri.history],
    }
    if "pdf" in ctype or re.search(r"\.pdf($|\?)", ri.url, re.I):
        return dict(rec, pdf=True, html=None, body=ri.content)
    t = E._decode(ri)
    return dict(rec, pdf=False, html=t) if t else None


def fetch_pdf(url: str) -> tuple[bytes | None, dict]:
    import requests

    try:
        r = requests.get(url, headers=E.HDRS, timeout=(6, 30), stream=True)
        body = r.raw.read(PDF_MAX, decode_content=True)
        return (body if r.status_code == 200 and body[:4] == b"%PDF" else None), {
            "status": r.status_code, "final_url": r.url, "content_type": r.headers.get("content-type", ""), "bytes": len(body)}
    except Exception as e:  # noqa: BLE001
        return None, {"error": type(e).__name__}


# ---------------------------------------------------------------------------
# render phase
async def settle(page):
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:  # noqa: BLE001
        pass
    await page.wait_for_timeout(2000)


async def accept_nothing_click_reject(page) -> dict | None:
    """Click a reject button from the fixed label list in the page or any of its frames."""
    js = """() => {
      const out = [];
      document.querySelectorAll('button, a, [role=button], input[type=button], input[type=submit]').forEach((el, i) => {
        const r = el.getBoundingClientRect(); const st = getComputedStyle(el);
        if (r.width < 2 || r.height < 2 || st.visibility === 'hidden' || st.display === 'none') return;
        const t = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
        if (!t || t.length > 80) return;
        el.setAttribute('data-ic-idx', String(i)); out.push([i, t]);
      });
      return out.slice(0, 400);
    }"""
    for frame in page.frames:
        try:
            items = await frame.evaluate(js)
            k = pick_reject([t for _, t in items])
            if k is None:
                continue
            idx, text = items[k]
            await frame.locator(f'[data-ic-idx="{idx}"]').first.click(timeout=3000)
            await page.wait_for_timeout(1500)
            try:  # verify: is a reject-label button still visible in that frame?
                left = await frame.evaluate(js)
                persisted = pick_reject([t for _, t in left]) is not None
            except Exception:  # noqa: BLE001  (frame gone: the banner closed)
                persisted = False
            return {"clicked": text, "frame": frame.url[:120] if frame != page.main_frame else "main", "persisted": persisted}
        except Exception:  # noqa: BLE001
            continue
    return None


async def scroll_lazy(page):
    try:
        await page.evaluate(
            """async () => { const h = Math.min(document.documentElement.scrollHeight, 20000);
               for (let y = 0; y < h; y += 900) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
               window.scrollTo(0, 0); }"""
        )
        await page.wait_for_timeout(400)
    except Exception:  # noqa: BLE001
        pass


def _png_compress(raw: bytes, path: Path) -> tuple[int, int]:
    import io

    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.save(path, format="PNG", optimize=True, compress_level=9)
    return im.size


async def capture_page(page, out: Path, name: str, banner_log: list) -> dict:
    """Settle, handle the cookie banner, write <name>.dom.html, .txt, .png. Returns facts."""
    await settle(page)
    act = await accept_nothing_click_reject(page)
    action = "none" if not act else ("clicked_banner_persisted" if act["persisted"] else "rejected")
    banner_log.append({"page": name, "action": action, **(act or {})})
    await scroll_lazy(page)
    facts: dict = {"url": page.url, "captured_at": now_iso()}
    html = await page.content()
    (out / f"{name}.dom.html").write_text(html)
    try:
        txt = await page.inner_text("body", timeout=5000)
    except Exception:  # noqa: BLE001
        txt = ""
    (out / f"{name}.txt").write_text(txt)
    try:
        h = int(await page.evaluate("() => Math.max(document.body ? document.body.scrollHeight : 0, document.documentElement.scrollHeight)") or 900)
        facts["page_height"] = h
        facts["screenshot_truncated"] = h > MAX_SHOT_H
        raw = await page.screenshot(full_page=True, clip={"x": 0, "y": 0, "width": VIEWPORT["width"], "height": min(max(h, 1), MAX_SHOT_H)}, timeout=40000)
        facts["raw_png_bytes"] = len(raw)
        size = await asyncio.to_thread(_png_compress, raw, out / f"{name}.png")
        facts["png_size"] = list(size)
    except Exception as e:  # noqa: BLE001
        facts["screenshot_error"] = type(e).__name__ + ":" + str(e)[:100]
    return facts


def redirect_chain(resp) -> list:
    chain, req = [], resp.request if resp else None
    while req is not None and req.redirected_from is not None:
        req = req.redirected_from
        chain.append(req.url)
    return list(reversed(chain))


async def goto(page, url, timeout=25000):
    resp = await page.goto(url, wait_until="load", timeout=timeout)
    return resp


async def render_phase(browser, host: str, out: Path, static: dict, rec: dict) -> None:
    ctx = await browser.new_context(user_agent=E.UA, locale="de-DE", viewport=VIEWPORT, ignore_https_errors=True)
    page = await ctx.new_page()
    banners: list = rec["consent_banner"]
    try:
        resp = None
        for scheme in ("https://", "http://"):
            try:
                resp = await goto(page, scheme + host + "/")
                break
            except Exception as e:  # noqa: BLE001
                rec["landing"]["goto_error"] = type(e).__name__ + ":" + str(e)[:100]
                if "ERR_NAME_NOT_RESOLVED" in str(e):
                    break
                if "interrupted by another navigation" in str(e):  # client-side redirect: let it land
                    await page.wait_for_timeout(4000)
                    if page.url not in ("about:blank", "") and not page.url.startswith("chrome-error:"):
                        rec["landing"]["note"] = "goto interrupted by a client-side redirect; captured after it landed"
                        break
        if resp is None and (page.url in ("about:blank", "") or page.url.startswith("chrome-error:")):
            return  # nothing to capture: the browser has no page (error page is not a capture)
        rec["landing"].update(
            render_final_url=page.url, render_status=resp.status if resp else None,
            render_redirects=redirect_chain(resp), render_headers=await resp.all_headers() if resp else None,
        )
        landing_url = page.url
        facts = await capture_page(page, out, "landing", banners)
        rec["landing"].update(facts)
        rec["files"] += [f"landing.{x}" for x in ("dom.html", "txt")] + (["landing.png"] if (out / "landing.png").exists() else [])
        html = (out / "landing.dom.html").read_text()
        cands = D.find_imprint_links(D.scan_html(html, page.url), page.url)
        rec["imprint_candidates"] = [c.__dict__ for c in cands[:5]]
        imprint, fallback, on_landing = None, None, True
        for c in cands[:4]:
            try:
                if c.kind in ("same_host", "other_host"):
                    if re.search(r"\.pdf($|\?)", c.url, re.I):
                        imprint = {"url": c.url, "via": "link", "pdf": True}
                        break
                    r2 = await goto(page, c.url, 20000)
                    on_landing = False
                    await E._settle(page)
                    if r2 is not None and r2.status < 400:
                        cand = {"url": page.url, "via": "link", "pdf": False, "status": r2.status, "redirects": redirect_chain(r2), "in_place": True}
                        t2 = await E._text(page)
                        if D.is_imprint_text(t2) or D.find_addresses(t2):
                            imprint = cand
                            break
                        fallback = fallback or cand
                else:  # fragment / javascript link: click it (modal or in-page)
                    if not on_landing:
                        await goto(page, landing_url, 20000)
                        await E._settle(page)
                        on_landing = True
                    await page.locator("a", has_text=re.compile(r"impressum|imprint", re.I)).first.click(timeout=5000)
                    on_landing = False
                    await page.wait_for_timeout(1500)
                    imprint = {"url": page.url, "via": "click", "pdf": False, "in_place": True}
                    break
            except Exception as e:  # noqa: BLE001
                rec.setdefault("imprint_errors", []).append(type(e).__name__)
        if imprint is None and fallback is not None:
            imprint = dict(fallback, not_imprint_like=True, in_place=False)
        if imprint is None and not [c for c in cands if c.kind in ("same_host", "other_host")]:
            base = f"{urlparse(landing_url).scheme}://{urlparse(landing_url).netloc}"
            for p in E.PROBE_PATHS[:2]:
                try:
                    r2 = await goto(page, base + p, 15000)
                    await E._settle(page)
                    if r2 is not None and r2.status == 200 and D.is_imprint_text(await E._text(page)):
                        imprint = {"url": page.url, "via": "probe", "pdf": False, "status": 200, "in_place": True}
                        break
                except Exception:  # noqa: BLE001
                    pass
        if imprint is None and static.get("imprint"):  # the static fetch found one the render did not
            si = static["imprint"]
            imprint = {"url": si["url"], "via": "static_fallback", "pdf": si["pdf"], "in_place": False}
        rec["imprint"] = imprint
        if imprint is None:
            return
        if imprint.get("pdf"):
            return
        if not imprint.get("in_place"):
            try:
                r3 = await goto(page, imprint["url"], 20000)
                imprint["status"] = r3.status if r3 else None
                imprint["redirects"] = redirect_chain(r3)
            except Exception as e:  # noqa: BLE001
                imprint["goto_error"] = type(e).__name__ + ":" + str(e)[:100]
                return
        imprint["final_url"] = page.url
        ifacts = await capture_page(page, out, "imprint", banners)
        imprint.update(ifacts)
        rec["files"] += [f"imprint.{x}" for x in ("dom.html", "txt")] + (["imprint.png"] if (out / "imprint.png").exists() else [])
    finally:
        await ctx.close()


# ---------------------------------------------------------------------------
async def capture_one(browser, item: dict, dns: dict, out_root: Path, versions: dict) -> dict:
    host = item["host"]
    out = host_dir(host, out_root)
    if out.exists():
        for f in out.iterdir():
            f.unlink()
    out.mkdir(parents=True, exist_ok=True)
    rec: dict = {
        "item": item.get("item"), "host": host, "screening_site_status": item.get("site_status"),
        "screening_final_url": item.get("final_url"), "capture_started": now_iso(), "user_agent": E.UA,
        "viewport": VIEWPORT, "max_screenshot_height": MAX_SHOT_H, "browser": versions, "dns": dns.get(host),
        "landing": {}, "imprint": None, "consent_banner": [], "files": [],
    }
    # static phase
    st = await asyncio.to_thread(static_phase, host)
    session = st.pop("session", None)
    rec["static_started"] = st["started"]
    rec["landing"]["static"] = st["landing"]
    if "landing.static.html" in st["files"]:
        (out / "landing.static.html").write_text(st["files"]["landing.static.html"])
        rec["files"].append("landing.static.html")
    si = st.get("imprint")
    if si:
        if si["pdf"]:
            (out / "imprint.pdf").write_bytes(si["body"])
            rec["files"].append("imprint.pdf")
        else:
            (out / "imprint.static.html").write_text(si["html"])
            rec["files"].append("imprint.static.html")
        rec["imprint_static"] = {k: v for k, v in si.items() if k not in ("html", "body")}
        rec["imprint_static"]["tried"] = st.get("tried")
    # render phase
    err = None
    try:
        await asyncio.wait_for(render_phase(browser, host, out, st, rec), timeout=ITEM_TIMEOUT)
    except Exception as e:  # noqa: BLE001
        err = type(e).__name__ + ":" + str(e)[:120]
        rec["render_error"] = err
    imp = rec.get("imprint")
    # PDF imprint through the file itself
    if imp and imp.get("pdf") and "imprint.pdf" not in rec["files"]:
        body, info = await asyncio.to_thread(fetch_pdf, imp["url"])
        imp["pdf_fetch"] = info
        if body:
            (out / "imprint.pdf").write_bytes(body)
            rec["files"].append("imprint.pdf")
    # static copy of the imprint the render chose, if the static fetch did not get that URL
    if imp and not imp.get("pdf") and "imprint.static.html" not in rec["files"] and (out / "imprint.dom.html").exists():
        ri, _e = await asyncio.to_thread(E._get, session, imp["url"]) if session else (None, "nosession")
        if ri is not None and ri.status_code == 200:
            (out / "imprint.static.html").write_text(E._decode(ri))
            rec["files"].append("imprint.static.html")
            rec["imprint_static"] = {"url": ri.url, "status": 200, "headers": dict(ri.headers), "via": "render_url"}
    # outcome
    rec["files"] = sorted(set(rec["files"]))
    l = rec["landing"]
    got_landing = (out / "landing.dom.html").exists()
    got_imprint = (out / "imprint.dom.html").exists() or (out / "imprint.pdf").exists()
    status_now = l.get("render_status") or (l.get("static") or {}).get("status")
    fu = l.get("render_final_url") or (l.get("static") or {}).get("final_url")
    if not got_landing and not (out / "landing.static.html").exists():
        rec["outcome"] = "failed"
        rec["failure_reason"] = failure_reason(host, dns, err, l)
        rec["site_status_at_capture"] = "unreachable"
    else:
        rec["outcome"] = "landing+imprint" if got_imprint else "landing_only"
        if imp is None:
            rec["imprint_note"] = "no imprint link/probe found on the landing page; landing only"
        elif not got_imprint:
            rec["imprint_note"] = "imprint located but its capture failed: " + str(imp.get("goto_error") or "unknown")
        if status_now and status_now >= 400:
            rec["site_status_at_capture"] = "http_error"
        elif fu and D.registered_domain(urlparse(fu).netloc) != D.registered_domain(host):
            rec["site_status_at_capture"] = "redirect_other_domain"
        else:
            rec["site_status_at_capture"] = "live"
    rec["capture_finished"] = now_iso()
    rec["complete"] = True
    (out / "meta.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str))
    return rec


async def run(items: list, dns: dict, workers: int, out_root: Path, retry_failed: bool):
    from playwright.async_api import async_playwright

    todo = [i for i in items if not is_complete(host_dir(i["host"], out_root), retry_failed)]
    by_host = {i["host"]: i for i in items}
    print(f"capture: {len(todo)} of {len(items)} items to do ({len(items) - len(todo)} already complete), {workers} workers", flush=True)
    groups = {i["host"]: (dns.get(i["host"]) or {}).get("group") for i in todo}
    sched = GroupScheduler([i["host"] for i in todo], groups)
    done = [0]
    t0 = time.time()
    async with async_playwright() as p:
        probe = await p.chromium.launch(args=["--disable-dev-shm-usage"])
        versions = {"name": "chromium", "version": probe.version, "playwright": __import__("importlib.metadata").metadata.version("playwright")}
        await probe.close()

        async def worker():
            browser, used = None, 0
            while True:
                if not sched.pending:
                    break
                h = sched.pick()
                if h is None:
                    await asyncio.sleep(0.5)
                    continue
                if browser is None or used >= 100 or not browser.is_connected():
                    if browser is not None:
                        try:
                            await browser.close()
                        except Exception:  # noqa: BLE001
                            pass
                    browser = await p.chromium.launch(args=["--disable-dev-shm-usage"])
                    used = 0
                used += 1
                try:
                    await asyncio.wait_for(capture_one(browser, by_host[h], dns, out_root, versions), timeout=ITEM_TIMEOUT + 120)
                except Exception as e:  # noqa: BLE001
                    print("ERR", h, type(e).__name__, str(e)[:100], file=sys.stderr, flush=True)
                    try:
                        await browser.close()
                    except Exception:  # noqa: BLE001
                        pass
                    browser = None
                finally:
                    sched.release(h)
                done[0] += 1
                if done[0] % 20 == 0:
                    print(f"capture {done[0]}/{len(todo)} {time.strftime('%H:%M:%S')} elapsed {time.time() - t0:.0f}s", flush=True)
            if browser is not None:
                await browser.close()

        await asyncio.gather(*(worker() for _ in range(workers)))
    print(f"capture done {done[0]} items in {time.time() - t0:.0f}s", flush=True)


def load_items(hosts_file: str | None, limit: int | None) -> list:
    if hosts_file:
        by_host = {}
        if SAMPLE.exists():
            by_host = {json.loads(l)["host"]: json.loads(l) for l in open(SAMPLE) if l.strip()}
        items = []
        for i, l in enumerate(x.strip() for x in open(hosts_file)):
            if l:
                items.append(by_host.get(l) or {"item": None, "host": l})
    else:
        items = [json.loads(l) for l in open(SAMPLE) if l.strip()]
    return items[:limit] if limit else items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", help="file with one host per line (default: the 1,000 hosts of datasets/E12/gold_sample.jsonl)")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--no-strato-filter", action="store_true", help="capture Strato hosts too (run from another machine)")
    a = ap.parse_args()
    out_root = Path(a.out)
    out_root.mkdir(parents=True, exist_ok=True)
    items = load_items(a.hosts, a.limit)
    socket.setdefaulttimeout(10)
    with ThreadPoolExecutor(max_workers=32) as ex:
        dns = {d["host"]: d for d in ex.map(resolve, [i["host"] for i in items])}
    if not a.no_strato_filter:
        deferred = [i["host"] for i in items if dns[i["host"]]["strato"]]
        (out_root / "deferred_strato.txt").write_text("\n".join(deferred) + ("\n" if deferred else ""))
        items = [i for i in items if not dns[i["host"]]["strato"]]
        print(f"strato: {len(deferred)} hosts deferred", flush=True)
    (out_root / "dns.json").write_text(json.dumps(dns, indent=0))
    asyncio.run(run(items, dns, a.workers, out_root, a.retry_failed))


if __name__ == "__main__":
    main()
