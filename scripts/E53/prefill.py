"""E53 step 10 (D61 A): main-address suggestions for the gold labelling tool, from a paid model via OpenRouter.

Model: anthropic/claude-haiku-5.5 (not an E52 candidate, so no candidate is scored on its own suggestions).
Prompt, output schema and parse: the release address extraction (E50 final_config: mode main, json_schema,
reasoning none, imprint input, 6000 chars), imported from scripts/E50/address.py. Items without imprint text
get no call; the suggestion is "no address" (reason no_imprint, E50 rule).

Input (one of):
  --input F.jsonl                  generic: one JSON per line with "host", "imprint_text" (optional "homepage_text").
                                   The E53 screen inputs (datasets/E53/screen/inputs.jsonl) have this form.
  --ic-fetch-dir datasets/E53/gold per-item dir <host>/ic_fetch.jsonl (the same-day `ic fetch` record, design
                                   3.2; the last line wins), turned into the model input by scripts/E51
                                   build_sample.record (clean_text, 6000 chars). --hosts F.txt limits/orders hosts.
Output: <out-dir>/prefill.jsonl, one line per host in the e21_prefill format
  {"host", "source": {"model", "prompt", "created"}, "prefilled_from", "label": {"addresses": [...],
   "main_address_index"}, "no_address_reason", "error"}.
  The labelling tool shows source as "<model>/<prompt>". Fields not found verbatim in the item's text carry
  "check" (also checked against <host>/{imprint,landing}.txt of the capture if present).
Resumable: hosts with an error-free line are skipped; hosts whose last line has an error are retried.

Cost guard (CLAUDE.md spend limits, D61): docs/cost_ledger.csv. Before the run: the D61 total (experiment
E53-prefill, cap USD 10), today's UTC total (cap USD 30), the per-run cap (USD 20, or --max-usd) and the dry-run
estimate; refuse to start if the estimate crosses a limit. During the run: the reported usage.cost is summed and
no call starts if spent + reserve for calls in flight + worst case of this call would cross the remaining limit.
One ledger row per run, also after a crash or a stop. The key OPENROUTER_API_KEY comes from --env; it is never
printed or logged.

    python3 -I scripts/E53/prefill.py --input in.jsonl --out-dir datasets/E53/prefill_pilot --limit 20 \
        --max-usd 0.20 --note pilot [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE.parent / "E50"))
sys.path.insert(0, str(HERE.parent / "E51"))
import address as AD  # noqa: E402
from build_sample import clean_text, norm_host, record  # noqa: E402,F401

from ic.gold.annotate import schema  # noqa: E402

MODEL = "anthropic/claude-haiku-5.5"
PREFILLED_FROM = MODEL + " via openrouter"
PROMPT_VERSION = "e53-v1 (E50 address main, json_schema)"
EXPERIMENT = "E53-prefill"
SERVICE = "openrouter"
URL = "https://openrouter.ai/api/v1/chat/completions"
PRICE_IN, PRICE_OUT = (
    0.10,
    0.50,
)  # USD per million tokens (verified list price 2026-11-13)
CAP_TOTAL, CAP_RUN, CAP_DAY = 10.0, 20.0, 30.0
MAX_TOKENS = 1000
EXPECTED_OUT = 120  # tokens per answer (pilot: mean 114)
CHARS_PER_TOKEN = (
    2.0  # German text on this tokenizer (pilot slope: 0.5 tokens per char)
)
SYSTEM_EXTRA_TOKENS = (
    600  # structured-output overhead on top of the prompt chars (pilot intercept)
)
LEDGER = ROOT / "docs" / "cost_ledger.csv"
COLUMNS = [
    "date_utc",
    "experiment",
    "service",
    "model",
    "calls",
    "input_tokens",
    "output_tokens",
    "usd",
    "usd_source",
    "output_path",
    "note",
]

CFG = AD.full_cfg(
    mode="main", fmt="schema", reasoning="none", addr_input="imprint", lang="de"
)


# ------------------------------------------------------------------------------------------------ ledger
def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def read_ledger(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_ledger(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.is_file() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in COLUMNS})


def _usd(r: dict) -> float:
    try:
        return float(r.get("usd") or 0)
    except ValueError:
        return 0.0


def ledger_totals(rows: list[dict], today: str) -> tuple[float, float]:
    """(USD used by experiment E53-prefill, USD of all paid runs on `today`)."""
    total = sum(_usd(r) for r in rows if r.get("experiment") == EXPERIMENT)
    day = sum(_usd(r) for r in rows if r.get("date_utc") == today)
    return total, day


def run_limit(
    total: float, day: float, max_usd: float | None = None
) -> tuple[float, str]:
    """Largest spend this run may reach, and the limit that binds."""
    lims = {
        "run cap $20": CAP_RUN,
        "D61 total $10": CAP_TOTAL - total,
        "UTC day $30": CAP_DAY - day,
    }
    if max_usd is not None:
        lims["--max-usd"] = max_usd
    name = min(lims, key=lims.get)
    return max(0.0, lims[name]), name


# ------------------------------------------------------------------------------------------------ estimate
def usd_of(in_tok: float, out_tok: float) -> float:
    return in_tok * PRICE_IN / 1e6 + out_tok * PRICE_OUT / 1e6


def est_input_tokens(msgs: list[dict]) -> int:
    return (
        int(sum(len(m["content"]) for m in msgs) / CHARS_PER_TOKEN)
        + SYSTEM_EXTRA_TOKENS
    )


def estimate(items: list[dict]) -> dict:
    """Dry-run estimate for the items that need a call (no network)."""
    n = in_tok = 0
    for it in items:
        msgs = AD.messages(it, CFG)
        if msgs is None:
            continue
        n += 1
        in_tok += est_input_tokens(msgs)
    out_tok = n * EXPECTED_OUT
    return {
        "calls": n,
        "skipped_no_imprint": len(items) - n,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "usd": usd_of(in_tok, out_tok),
        "usd_worst": usd_of(in_tok, n * MAX_TOKENS),
    }


def check_budget(
    est: dict, rows: list[dict], today: str, max_usd: float | None = None
) -> tuple[bool, str]:
    total, day = ledger_totals(rows, today)
    lim, name = run_limit(total, day, max_usd)
    msg = (
        f"ledger: E53-prefill total ${total:.4f} of ${CAP_TOTAL:.2f}, UTC {today} ${day:.4f} of ${CAP_DAY:.2f}; "
        f"run limit ${lim:.4f} ({name}); estimate ${est['usd']:.4f} for {est['calls']} calls "
        f"({est['input_tokens']} in / {est['output_tokens']} out tokens), worst case ${est['usd_worst']:.4f}"
    )
    return est["usd"] <= lim, msg


# ------------------------------------------------------------------------------------------------ input
def read_generic(path: Path) -> list[dict]:
    out = []
    for line in path.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out.append(
                {
                    "host": r["host"],
                    "imprint_text": r.get("imprint_text") or "",
                    "homepage_text": r.get("homepage_text") or "",
                    "meta": r.get("meta") or {},
                }
            )
    return out


def read_ic_fetch(root: Path, hosts: list[str] | None = None) -> list[dict]:
    """Per-item dirs <root>/<host>/ic_fetch.jsonl -> model-input records (last line of each file)."""
    names = (
        hosts
        if hosts is not None
        else sorted(p.parent.name for p in root.glob("*/ic_fetch.jsonl"))
    )
    out = []
    for h in names:
        p = root / h / "ic_fetch.jsonl"
        if not p.is_file():
            out.append(
                {
                    "host": h,
                    "imprint_text": "",
                    "homepage_text": "",
                    "meta": {"no_ic_fetch": True},
                }
            )
            continue
        lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        r = json.loads(lines[-1]) if lines else {}
        r.setdefault("host", h)
        rec = record(r, f"{h}/ic_fetch.jsonl")
        rec["host"] = h
        out.append(rec)
    return out


# ------------------------------------------------------------------------------------------------ OpenRouter
class BudgetStop(Exception):
    pass


class Meter:
    """Thread-safe spend meter. reserve() before a call, settle() after it."""

    def __init__(self, limit: float):
        self.limit, self.spent, self.reserved, self.stopped = limit, 0.0, 0.0, False
        self.calls = self.in_tok = self.out_tok = 0
        self.estimated_calls = 0
        self.lock = threading.Lock()

    def reserve(self, worst: float) -> None:
        with self.lock:
            if self.stopped or self.spent + self.reserved + worst > self.limit:
                self.stopped = True
                raise BudgetStop(
                    f"spent ${self.spent:.5f} + in flight ${self.reserved:.5f} + ${worst:.5f} > ${self.limit:.4f}"
                )
            self.reserved += worst

    def settle(self, worst: float, usage: dict | None) -> None:
        with self.lock:
            self.reserved -= worst
            if usage is None:  # request failed without a charge we can see
                return
            p, c = int(usage.get("prompt_tokens") or 0), int(
                usage.get("completion_tokens") or 0
            )
            cost = usage.get("cost")
            if cost is None:
                cost, self.estimated_calls = usd_of(p, c), self.estimated_calls + 1
            self.spent += float(cost)
            self.calls += 1
            self.in_tok += p
            self.out_tok += c

    @property
    def source(self) -> str:
        return "estimated" if self.estimated_calls else "reported"


def post(key: str, body: dict, retries: int = 5, timeout: int = 120) -> dict:
    """POST with retries on 429/5xx and network errors. Never includes the key in an error text."""
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            URL,
            data=data,
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://webkurator.de",
                "X-Title": "imprints-collection E53 prefill",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.load(r)
            err = resp.get("error")  # OpenRouter may answer 200 with an upstream error
            if err and not resp.get("choices"):
                code = err.get("code") if isinstance(err, dict) else None
                if (
                    isinstance(code, int)
                    and (code == 429 or code >= 500)
                    and attempt < retries
                ):
                    time.sleep(min(60, 2**attempt + random.random()))
                    continue
                raise RuntimeError(f"upstream error {code}")
            return resp
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and attempt < retries:
                ra = e.headers.get("Retry-After")
                time.sleep(
                    min(
                        60,
                        (
                            float(ra)
                            if ra and ra.isdigit()
                            else 2**attempt + random.random()
                        ),
                    )
                )
                continue
            raise RuntimeError(f"HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < retries:
                time.sleep(min(60, 2**attempt + random.random()))
                continue
            raise RuntimeError("network error") from None
    raise RuntimeError("retries exhausted")


def build_body(msgs: list[dict]) -> dict:
    return {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
        "messages": msgs,
        "response_format": AD.response_format(CFG),
        "usage": {"include": True},
    }


# ------------------------------------------------------------------------------------------------ one item
def _n(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def to_label(parsed: dict, texts: str) -> dict:
    """AD.parse output -> labelling-tool label (addresses + main_address_index), with verbatim checks."""
    hay = _n(texts)
    lines = [l.strip() for l in texts.splitlines() if l.strip()]
    addrs = []
    for a in parsed["addresses"]:
        b = schema.empty_address()
        for k in ("street", "number", "postcode", "town", "country"):
            b[k] = a[k]
        b["po_box"] = _n(a["street"]).startswith("postfach")
        pc = next(
            (i for i, l in enumerate(lines) if a["postcode"] and a["postcode"] in l),
            None,
        )
        if (
            pc is not None
        ):  # evidence: the postcode line and the street line right before it
            st = (
                pc - 1
                if pc > 0 and a["street"] and _n(a["street"]) in _n(lines[pc - 1])
                else pc
            )
            b["evidence"] = "\n".join(lines[st : pc + 1])
        b["check"] = [
            k
            for k in ("street", "number", "postcode", "town", "country")
            if b[k] and _n(b[k]) not in hay
        ]
        if not b["evidence"]:
            b["check"].append("evidence")
        addrs.append(b)
    label: dict = {"addresses": addrs}
    if parsed["main_index"] is not None:
        label["main_address_index"] = parsed["main_index"]
    return label


def capture_texts(item_dir: Path | None) -> str:
    if not item_dir:
        return ""
    return "\n".join(
        (item_dir / n).read_text(errors="replace")
        for n in ("imprint.txt", "landing.txt")
        if (item_dir / n).is_file()
    )


def one(
    key: str, it: dict, meter: Meter, item_dir: Path | None = None, post_fn=post
) -> dict:
    host = it["host"]
    rec = {
        "host": host,
        "source": {
            "model": PREFILLED_FROM,
            "prompt": PROMPT_VERSION,
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "prefilled_from": PREFILLED_FROM,
        "label": {"addresses": []},
        "no_address_reason": None,
        "error": None,
    }
    msgs = AD.messages(it, CFG)
    if msgs is None:  # no imprint text: no call (E50 rule)
        rec["no_address_reason"] = "no_imprint"
        return rec
    worst = usd_of(est_input_tokens(msgs), MAX_TOKENS)
    meter.reserve(worst)  # raises BudgetStop
    usage = None
    try:
        resp = post_fn(key, build_body(msgs))
        usage = resp.get("usage") or {}
        rec["usage"] = {
            k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "cost")
        }
        ch = (resp.get("choices") or [{}])[0]
        txt = ((ch.get("message") or {}).get("content")) or ""
        try:
            ans = json.JSONDecoder(strict=False).raw_decode(
                txt[max(txt.find("{"), 0) :]
            )[0]
            if not isinstance(ans, dict):
                raise ValueError("not an object")
            parsed = AD.parse(ans, "main")
        except (ValueError, TypeError, KeyError) as e:
            rec["error"] = (
                f"parse: {type(e).__name__}: {str(e)[:120]} (finish {ch.get('finish_reason')}) raw: {txt[:200]!r}"
            )
            return rec
        rec["label"] = to_label(
            parsed, it.get("imprint_text", "") + "\n" + capture_texts(item_dir)
        )
        rec["no_address_reason"] = parsed["no_address_reason"]
    except RuntimeError as e:
        rec["error"] = f"api: {e}"[:200]
    finally:
        meter.settle(worst, usage)
    return rec


# ------------------------------------------------------------------------------------------------ run
def done_hosts(path: Path) -> set[str]:
    """Hosts whose last line in the output is error-free."""
    last: dict = {}
    if path.is_file():
        for l in path.open(encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                last[r["host"]] = r.get("error") is None
    return {h for h, ok in last.items() if ok}


def run(
    items: list[dict],
    out: Path,
    key: str,
    limit_usd: float,
    workers: int,
    ledger: Path,
    note: str,
    post_fn=post,
    dirs: dict | None = None,
) -> dict:
    """Process items, append to `out`, append one ledger row (also on failure). Returns a summary."""
    todo = [it for it in items if it["host"] not in done_hosts(out)]
    meter = Meter(limit_usd)
    n = {
        "written": 0,
        "errors": 0,
        "parse_failures": 0,
        "no_imprint": 0,
        "stopped_unprocessed": 0,
    }
    lock = threading.Lock()
    out.parent.mkdir(parents=True, exist_ok=True)
    status = "ok"
    try:
        with out.open("a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as ex:

            def work(it):
                try:
                    return one(key, it, meter, (dirs or {}).get(it["host"]), post_fn)
                except BudgetStop:
                    return None

            for rec in ex.map(work, todo):
                with lock:
                    if rec is None:
                        n["stopped_unprocessed"] += 1
                        continue
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    n["written"] += 1
                    n["errors"] += bool(rec["error"])
                    n["parse_failures"] += bool(
                        rec["error"] and rec["error"].startswith("parse")
                    )
                    n["no_imprint"] += (
                        rec["no_address_reason"] == "no_imprint" and "usage" not in rec
                    )
        if n["stopped_unprocessed"]:
            status = f"stopped at the limit, {n['stopped_unprocessed']} items not run"
    except (
        BaseException
    ) as e:  # incl. KeyboardInterrupt: the ledger row must still be written
        status = f"failed: {type(e).__name__}"
        raise
    finally:
        append_ledger(
            ledger,
            {
                "date_utc": today_utc(),
                "experiment": EXPERIMENT,
                "service": SERVICE,
                "model": MODEL,
                "calls": meter.calls,
                "input_tokens": meter.in_tok,
                "output_tokens": meter.out_tok,
                "usd": f"{meter.spent:.6f}",
                "usd_source": meter.source,
                "output_path": str(out),
                "note": "; ".join(
                    x for x in (note, status if status != "ok" else "") if x
                ),
            },
        )
    return {
        **n,
        "calls": meter.calls,
        "input_tokens": meter.in_tok,
        "output_tokens": meter.out_tok,
        "usd": meter.spent,
        "usd_source": meter.source,
        "status": status,
    }


def load_key(env_path: str) -> str:
    for line in Path(env_path).read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*)", line)
        if m:
            return m.group(1).strip().strip("'\"")
    raise SystemExit(f"OPENROUTER_API_KEY not found in {env_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="generic JSONL: host, imprint_text[, homepage_text]")
    g.add_argument(
        "--ic-fetch-dir", help="datasets/E53/gold (per-item <host>/ic_fetch.jsonl)"
    )
    ap.add_argument(
        "--hosts", help="host list (one per line); with --input: filter and order"
    )
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=0, help="first N items of the input")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument(
        "--max-usd",
        type=float,
        default=None,
        help="cap for this run (also bounded by the ledger limits)",
    )
    ap.add_argument("--note", default="")
    ap.add_argument("--ledger", default=str(LEDGER))
    ap.add_argument(
        "--env", default="/home/dinzinger/GitLab/fim/imprints-collection/.env"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print the estimate and the ledger state; no calls",
    )
    a = ap.parse_args()

    hosts = [l.strip() for l in open(a.hosts) if l.strip()] if a.hosts else None
    dirs = None
    if a.ic_fetch_dir:
        root = Path(a.ic_fetch_dir)
        items = read_ic_fetch(root, hosts)
        dirs = {it["host"]: root / it["host"] for it in items}
    else:
        items = read_generic(Path(a.input))
        if hosts is not None:
            by = {it["host"]: it for it in items}
            items = [by[h] for h in hosts if h in by]
    out = Path(a.out_dir) / "prefill.jsonl"
    items = [it for it in items if it["host"] not in done_hosts(out)]
    if a.limit:
        items = items[: a.limit]
    est = estimate(items)
    ledger = Path(a.ledger)
    rows = read_ledger(ledger)
    ok, msg = check_budget(est, rows, today_utc(), a.max_usd)
    print(
        f"{len(items)} items to do ({est['skipped_no_imprint']} without imprint text)"
    )
    print(msg)
    if a.dry_run:
        return
    if not ok:
        raise SystemExit("REFUSED: the estimate crosses a limit")
    total, day = ledger_totals(rows, today_utc())
    limit, name = run_limit(total, day, a.max_usd)
    summary = run(
        items, out, load_key(a.env), limit, a.workers, ledger, a.note, dirs=dirs
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
