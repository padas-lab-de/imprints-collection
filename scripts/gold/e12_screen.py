"""E12-gold-screening: screen 10,000 random seed hosts with the E8 detectors.

Reuses the E8 stage functions (scripts/gold/e8_pilot.py) with data paths under
datasets/E12 and results/E12, and adds a polite scheduler: at most one
concurrent request per hosting provider (resolved IPv4 /24, IPv6 /48), a pause
of GAP seconds between two hosts of the same provider, 8 static workers and 4
render workers by default.

Stages:
  sample    10,000 hosts (seed 20261024) from seed_hosts.txt.gz, excluding the
            E8 pilot hosts and the hosts of the old gold set
  dns       resolve every host once (provider key = IP /24)
  static    plain HTTP fetch of landing + imprint (E8 static_one)
  render    headless Chromium (E8 render_one), skipping hosts with no DNS,
            a connection failure on both schemes, or a static redirect to
            another registered domain
  wayback   Wayback CDX first capture (E8 stage_wayback, <= 1 request/s)
  llm       innkube gemma4-31b-it text judgement (E8 llm_one)
  vision    vision_all (E8 vision_all_one) on image-only candidates only
  features  combine with src/ic/gold/detectors.py -> results/E12/screening_features.jsonl

  static --retry / render --retry: hosts that answered 403/429/503 (once, after a pause).

Run from the repository root, e.g.
  PYTHONPATH=src LD_LIBRARY_PATH=<render libs> <venv-render>/bin/python scripts/gold/e12_screen.py static
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import importlib.util
import ipaddress
import json
import os
import random
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from ic.gold import detectors as D

ROOT = Path(os.environ.get("IC_DATA_ROOT", "/home/dinzinger/GitHub/imprints-collection"))
REPO = Path(__file__).resolve().parents[2]
DATA = ROOT / "datasets" / "E12"
RES = ROOT / "results" / "E12"
SEED_LIST = REPO / "seed_hosts.txt.gz"
OLD_GOLD = REPO / "evaluation" / "gold_standard_data.jsonl"
E8_HOSTS = ROOT / "datasets" / "E8" / "hosts.txt"
SEED = 20261024
N = 10_000
GAP = 2.0  # seconds between two hosts of the same provider
RETRY_STATUSES = (403, 429, 503)

_spec = importlib.util.spec_from_file_location("e8_pilot", Path(__file__).with_name("e8_pilot.py"))
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)
E.DATA, E.RES = DATA, RES
E.ROOT = Path("/home/dinzinger/GitHub/imprints-collection")  # E._client loads E.ROOT / ".env"
E.E4_FILE = DATA / "no_e4_file"  # E12 hosts are not in E4; e4_* fields stay None


def norm_host(h: str) -> str:
    h = (h or "").strip().lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def hosts() -> list:
    return E.hosts()


# ---------------------------------------------------------------------------
def stage_sample(_args):
    excl = set()
    for l in open(E8_HOSTS):
        if l.strip():
            excl.add(norm_host(l))
    n_e8 = len(excl)
    for l in open(OLD_GOLD):
        if l.strip():
            excl.add(norm_host(urlparse(json.loads(l)["url"]).netloc))
    with gzip.open(SEED_LIST, "rt") as f:
        seeds = [l.strip() for l in f if l.strip()]
    frame = [h for h in seeds if norm_host(h) not in excl]
    rng = random.Random(SEED)
    sample = rng.sample(frame, N)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "hosts.txt").write_text("\n".join(sample) + "\n")
    meta = {
        "seed": SEED, "n_sample": N, "seed_list_hosts": len(seeds), "frame_hosts": len(frame),
        "excluded_seed_hosts": len(seeds) - len(frame), "excluded_keys_e8": n_e8, "excluded_keys_total": len(excl),
    }
    (DATA / "frame.json").write_text(json.dumps(meta, indent=1))
    print(meta)


# ---------------------------------------------------------------------------
def provider_key(ips: list) -> str | None:
    """Group key for a hosting provider: first IPv4 /24, else first IPv6 /48."""
    v4 = [i for i in ips if ":" not in i]
    if v4:
        return str(ipaddress.ip_network(v4[0] + "/24", strict=False))
    if ips:
        return str(ipaddress.ip_network(ips[0] + "/48", strict=False))
    return None


def _resolve(h):
    try:
        infos = socket.getaddrinfo(h, 443, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos}, key=lambda x: (":" in x, x))
        return {"host": h, "ips": ips[:4], "group": provider_key(ips), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"host": h, "ips": [], "group": None, "error": type(e).__name__ + ":" + str(e)[:60]}


def stage_dns(args):
    path = DATA / "dns.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(l)["host"] for l in open(path) if l.strip()}
    todo = [h for h in hosts() if h not in done]
    socket.setdefaulttimeout(10)
    with open(path, "a") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, rec in enumerate(ex.map(_resolve, todo)):
            f.write(json.dumps(rec) + "\n")
            if i % 1000 == 0:
                print(f"dns {i}/{len(todo)}", flush=True)


def dns_index() -> dict:
    return {d["host"]: d for d in map(json.loads, open(DATA / "dns.jsonl"))}


# ---------------------------------------------------------------------------
class ProviderScheduler:
    """Hands out hosts so that no two hosts of the same provider group run at
    once and a group rests `gap` seconds between hosts. Hosts with no group
    (DNS failure) are unconstrained."""

    def __init__(self, items: list, group_of: dict, gap: float = GAP):
        self.group_of = group_of
        self.gap = gap
        self.busy: set = set()
        self.next_ok: dict = {}
        self.pending = interleave(items, group_of)
        self.cond = threading.Condition()

    def _pick(self):
        now = time.monotonic()
        for i, h in enumerate(self.pending):
            g = self.group_of.get(h)
            if g is None or (g not in self.busy and self.next_ok.get(g, 0) <= now):
                self.pending.pop(i)
                if g is not None:
                    self.busy.add(g)
                return h
        return None

    def take(self):
        with self.cond:
            while self.pending:
                h = self._pick()
                if h is not None:
                    return h
                self.cond.wait(timeout=0.5)
            return None

    def release(self, h):
        with self.cond:
            g = self.group_of.get(h)
            if g is not None:
                self.busy.discard(g)
                self.next_ok[g] = time.monotonic() + self.gap
            self.cond.notify_all()


def interleave(items: list, group_of: dict) -> list:
    """Round-robin over provider groups, so one big group does not block the
    head of the queue."""
    buckets: dict = {}
    for h in items:
        buckets.setdefault(group_of.get(h) or ("_none", h), []).append(h)
    out = []
    lists = sorted(buckets.values(), key=len, reverse=True)
    i = 0
    while any(lists):
        for lst in lists:
            if i < len(lst):
                out.append(lst[i])
        i += 1
        lists = [l for l in lists if len(l) > i]
    return out


def _static_meta(h):
    p = DATA / "static" / E.safe(h) / "meta.json"
    return json.loads(p.read_text()) if p.exists() else None


def static_retry_hosts() -> list:
    return [h for h in hosts() if (_static_meta(h) or {}).get("status") in RETRY_STATUSES]


def stage_static(args):
    dns = dns_index()
    groups = {h: (dns.get(h) or {}).get("group") for h in hosts()}
    if args.retry:
        hs = static_retry_hosts()
        (DATA / "static_retry_hosts.txt").write_text("\n".join(hs) + "\n")
    else:
        hs = [h for h in hosts() if _static_meta(h) is None]
    print(f"static: {len(hs)} hosts, {args.workers} workers", flush=True)
    sched = ProviderScheduler(hs, groups)
    done = [0]
    lock = threading.Lock()

    def worker():
        while True:
            h = sched.take()
            if h is None:
                return
            try:
                if groups.get(h) is None and not args.retry:  # no DNS: record without fetching
                    d = DATA / "static" / E.safe(h)
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "meta.json").write_text(json.dumps({"host": h, "final_url": None, "status": None, "error": "NoDNS"}))
                else:
                    E.static_one(h, force=args.retry)
            except Exception as e:  # noqa: BLE001
                print("ERR", h, e, file=sys.stderr)
            finally:
                sched.release(h)
            with lock:
                done[0] += 1
                if done[0] % 200 == 0:
                    print(f"static {done[0]}/{len(hs)} {time.strftime('%H:%M:%S')}", flush=True)

    ts = [threading.Thread(target=worker) for _ in range(args.workers)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    print("static done", flush=True)


# ---------------------------------------------------------------------------
def needs_render(h, dns) -> bool:
    if (dns.get(h) or {}).get("group") is None:
        return False
    m = _static_meta(h) or {}
    if m.get("final_url") is None and m.get("error") in ("ConnectionError", "ConnectTimeout", "NoDNS"):
        return False  # refused / no route on both schemes
    fu = m.get("final_url")
    if fu and (m.get("status") or 0) < 400:
        fh = urlparse(fu).netloc.lower()
        if fh and D.registered_domain(fh) != D.registered_domain(h):
            return False  # redirect to another domain: not this site
    return True


def _render_meta(h):
    p = DATA / "render" / E.safe(h) / "meta.json"
    return json.loads(p.read_text()) if p.exists() else None


def render_retry_hosts(dns) -> list:
    out = []
    for h in hosts():
        m = _render_meta(h)
        if m is None or not needs_render(h, dns):
            continue
        if (m.get("status") in RETRY_STATUSES) or ((_static_meta(h) or {}).get("status") in RETRY_STATUSES and not m.get("imprint")):
            out.append(h)
    return out


async def _render_sched(hs, groups, workers, force, per_browser=150):
    from playwright.async_api import async_playwright

    sched = ProviderScheduler(hs, groups)
    done = [0]

    async def take():
        while True:
            with sched.cond:
                if not sched.pending:
                    return None
                h = sched._pick()
            if h is not None:
                return h
            await asyncio.sleep(0.5)

    async with async_playwright() as p:

        async def worker():
            browser, used = None, 0
            while True:
                h = await take()
                if h is None:
                    break
                if browser is None or used >= per_browser or not browser.is_connected():
                    if browser is not None:
                        try:
                            await browser.close()
                        except Exception:  # noqa: BLE001
                            pass
                    browser = await p.chromium.launch(args=["--disable-dev-shm-usage"])
                    used = 0
                used += 1
                try:
                    await asyncio.wait_for(E.render_one(browser, h, force), timeout=150)
                except Exception as e:  # noqa: BLE001
                    d = DATA / "render" / E.safe(h)
                    d.mkdir(parents=True, exist_ok=True)
                    if force or not (d / "meta.json").exists():
                        (d / "meta.json").write_text(json.dumps({"host": h, "error": "timeout:" + type(e).__name__}))
                    try:
                        await browser.close()
                    except Exception:  # noqa: BLE001
                        pass
                    browser = None
                finally:
                    sched.release(h)
                done[0] += 1
                if done[0] % 100 == 0:
                    print(f"render {done[0]}/{len(hs)} {time.strftime('%H:%M:%S')}", flush=True)
            if browser is not None:
                await browser.close()

        await asyncio.gather(*(worker() for _ in range(workers)))
    print("render done", flush=True)


def stage_render(args):
    dns = dns_index()
    groups = {h: (dns.get(h) or {}).get("group") for h in hosts()}
    if args.retry:
        hs = render_retry_hosts(dns)
        (DATA / "render_retry_hosts.txt").write_text("\n".join(hs) + "\n")
    else:
        hs = [h for h in hosts() if needs_render(h, dns) and _render_meta(h) is None]
    print(f"render: {len(hs)} hosts, {args.workers} workers", flush=True)
    asyncio.run(_render_sched(hs, groups, args.workers, force=args.retry))


# ---------------------------------------------------------------------------
def stage_wayback(args):
    E.stage_wayback(args)
    print("wayback done", flush=True)


def stage_llm(args):
    """Text judgement for every host with text. With --follow, keeps picking up
    hosts as the render stage finishes them (render marker: render.done)."""
    client = E._client()
    path = DATA / f"llm_text_{args.model}.jsonl"
    dns = dns_index()
    while True:
        finished = (DATA / "render.done").exists()
        ready = [h for h in hosts() if _static_meta(h) is not None and (not needs_render(h, dns) or _render_meta(h) is not None)]
        E._run_parallel(lambda h: E.llm_one(client, args.model, h), ready, path, args.workers)
        if not args.follow or finished:
            break
        time.sleep(120)
    print("llm done", flush=True)


def vision_candidates(model: str) -> list:
    """Image-only candidates: a rendered imprint screenshot exists, and either
    the rule-based screenshot candidate fires, or neither the address rules nor
    the text LLM find an address in the imprint text."""
    texts = {}
    p = DATA / f"llm_text_{model}.jsonl"
    if p.exists():
        for l in open(p):
            d = json.loads(l)
            texts[d["host"]] = d
    out = []
    for h in hosts():
        rd = DATA / "render" / E.safe(h)
        if not (rd / "imprint.jpg").exists():
            continue
        ri_txt = E._read(rd / "imprint.txt")
        rule = bool(D.find_addresses(ri_txt))
        model_addr = E._model_has_address((texts.get(h) or {}).get("text"))
        ri_html = E._read(rd / "imprint.html")
        rm = _render_meta(h) or {}
        scan = D.scan_html(ri_html, (rm.get("imprint") or {}).get("url") or "http://x/") if ri_html else None
        cand, _ = D.screenshot_candidate(True, ri_txt, rule or model_addr, scan.images if scan else [])
        if cand or not (rule and model_addr):
            out.append(h)
    return out


def stage_vision(args):
    client = E._client()
    hs = vision_candidates(args.model)
    (DATA / "vision_candidates.txt").write_text("\n".join(hs) + "\n")
    print(f"vision: {len(hs)} candidates", flush=True)
    E._run_parallel(lambda h: E.vision_all_one(client, args.model, h), hs, DATA / f"vision_all_{args.model}.jsonl", args.workers)
    print("vision done", flush=True)


def stage_features(args):
    E.stage_features(args)
    src = RES / "pilot_features.jsonl"
    dst = RES / "screening_features.jsonl"
    dns = dns_index()
    with open(src) as fi, open(dst, "w") as fo:
        for l in fi:
            d = json.loads(l)
            d["provider_group"] = (dns.get(d["host"]) or {}).get("group")
            d["rendered"] = _render_meta(d["host"]) is not None
            fo.write(json.dumps(d, ensure_ascii=False) + "\n")
    src.unlink()
    print(f"wrote {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["sample", "dns", "static", "render", "wayback", "llm", "vision", "features"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--model", default="gemma4-31b-it")
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--follow", action="store_true")
    a = ap.parse_args()
    globals()["stage_" + a.stage](a)


if __name__ == "__main__":
    main()
