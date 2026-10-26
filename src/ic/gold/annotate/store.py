"""Storage for the labelling tool: assignment, captures, labels.

Layout (docs/gold_set_design.md section 3), below ``data_dir`` (default ``datasets/gold``):

    assignment.jsonl            item, host, labeller, role, order
    <host>/landing.png|.jpg     screenshots (E8 pilot captures use .jpg)
    <host>/landing.txt          rendered body text
    <host>/imprint.png|.jpg, imprint.txt
    <host>/meta.json            provenance (capture timestamp, final URLs, ...)
    labels/<labeller>.jsonl     one JSON line per save; the last line per host wins
    prefill.jsonl               suggested labels (scripts/gold/e21_prefill.py), optional

A labeller only ever reads its own labels file. Suggestions are shown only for the
roles in ``prefill_roles``. The CLI shows them on all items (D24 B); agreement between
labellers therefore includes anchoring on the shared suggestion.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from .schema import normalise_label, text_warnings, validate_label

PAGES = ("landing", "imprint")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
MAX_TEXT_CHARS = 400_000  # cap what is sent to the browser
_HOST_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_META_TIME_KEYS = (
    "capture_id",
    "capture_started",
    "captured_at",
    "landing_captured_at",
    "timestamp",
    "rendered_at",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Store:
    def __init__(
        self,
        data_dir: str | Path,
        labeller: str,
        assignment: str | Path | None = None,
        prefill_roles: tuple[str, ...] = ("primary",),
    ):
        self.data_dir = Path(data_dir)
        self.prefill_roles = tuple(prefill_roles)
        self.labeller = labeller
        self.assignment_path = Path(assignment) if assignment else self.data_dir / "assignment.jsonl"
        self.labels_path = self.data_dir / "labels" / f"{labeller}.jsonl"
        self._lock = threading.Lock()
        self.items = self._load_assignment()
        self._by_host = {it["host"]: it for it in self.items}
        self._prefill = self._load_prefill()

    # ---- assignment -------------------------------------------------
    def _load_assignment(self) -> list[dict]:
        if not self.assignment_path.exists():
            raise FileNotFoundError(
                f"{self.assignment_path} not found; run scripts/gold/e18_assign.py first"
            )
        rows = []
        with open(self.assignment_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    if r.get("labeller") == self.labeller:
                        rows.append(r)
        rows.sort(key=lambda r: r["order"])
        for r in rows:
            if not _HOST_RE.match(r["host"]):
                raise ValueError(f"unsafe host name in assignment: {r['host']!r}")
        return rows

    def _load_prefill(self) -> dict[str, dict]:
        p = self.data_dir / "prefill.jsonl"
        out: dict[str, dict] = {}
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        out[r["host"]] = r
        return out

    def prefill(self, host: str) -> dict | None:
        """Suggested label for this labeller's item, or None (role not pre-filled, no suggestion)."""
        it = self._by_host.get(host)
        r = self._prefill.get(host)
        if not it or not r or it.get("role") not in self.prefill_roles:
            return None
        src = r.get("source") or {}
        return {"label": r.get("label") or {}, "source": f"{src.get('model', '?')}/{src.get('prompt', '?')}"}

    def has_host(self, host: str) -> bool:
        return host in self._by_host

    # ---- labels -----------------------------------------------------
    def load_labels(self) -> dict[str, dict]:
        """Last line per host wins."""
        out: dict[str, dict] = {}
        if self.labels_path.exists():
            with open(self.labels_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue  # a torn last line must not block the tool
                    out[r["host"]] = r
        return out

    def save_label(self, label: dict, elapsed: float = 0.0) -> tuple[dict | None, list[str], list[str]]:
        """Validate and append. Returns (saved_record, errors, warnings)."""
        host = (label or {}).get("host", "")
        if not self.has_host(host):
            return None, [f"host {host!r} is not assigned to {self.labeller}"], []
        label = normalise_label(label)
        label["annotator"] = self.labeller
        errors = validate_label(label)
        if errors:
            return None, errors, []
        cap = self.capture(host)
        warnings = text_warnings(label, [cap["texts"].get(p, "") for p in PAGES])
        with self._lock:
            prev = self.load_labels().get(host)
            prior = float(prev.get("seconds_spent", 0)) if prev else 0.0
            rec = {k: v for k, v in label.items() if k not in ("seconds_spent", "capture_id", "prefilled_from")}
            rec["item"] = self._by_host[host].get("item")
            pf = self.prefill(host)
            # which suggestion the labeller saw (None = labelled from scratch)
            rec["prefilled_from"] = pf["source"] if pf and label.get("prefilled_from") else None
            rec["capture_id"] = cap["capture_id"]
            rec["seconds_spent"] = int(round(prior + max(0.0, min(float(elapsed or 0), 3600.0))))
            rec["saved_at"] = now_utc()
            self.labels_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.labels_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec, [], warnings

    # ---- captures ---------------------------------------------------
    def host_dir(self, host: str) -> Path:
        return self.data_dir / host

    def find_image(self, host: str, page: str) -> str | None:
        if page not in PAGES:
            return None
        for ext in IMAGE_EXT:
            if (self.host_dir(host) / f"{page}{ext}").is_file():
                return f"{page}{ext}"
        return None

    def capture(self, host: str) -> dict:
        d = self.host_dir(host)
        meta: dict = {}
        mp = d / "meta.json"
        if mp.is_file():
            try:
                meta = json.loads(mp.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = {}
        capture_id = None
        for k in _META_TIME_KEYS:
            if isinstance(meta.get(k), str) and meta[k]:
                capture_id = meta[k]
                break
        texts, images = {}, {}
        for p in PAGES:
            tp = d / f"{p}.txt"
            if tp.is_file():
                texts[p] = tp.read_text(encoding="utf-8", errors="replace")[:MAX_TEXT_CHARS]
            images[p] = self.find_image(host, p)
        return {
            "host": host,
            "exists": d.is_dir(),
            "capture_id": capture_id,
            "meta": meta,
            "texts": texts,
            "images": images,
        }

    def image_path(self, host: str, name: str) -> Path | None:
        """Resolve an image request safely (assigned host, known file name only)."""
        if not self.has_host(host):
            return None
        m = re.match(r"^(landing|imprint)\.(png|jpg|jpeg|webp)$", name)
        if not m:
            return None
        p = self.host_dir(host) / name
        return p if p.is_file() else None

    # ---- progress ---------------------------------------------------
    def listing(self) -> list[dict]:
        labels = self.load_labels()
        return [
            {
                "host": it["host"],
                "order": it["order"],
                "phase": "calibration" if it.get("role") == "calibration" else "main",
                "prefill": self.prefill(it["host"]) is not None,
                "done": it["host"] in labels,
            }
            for it in self.items
        ]
