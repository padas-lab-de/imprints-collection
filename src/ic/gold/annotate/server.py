"""Stdlib HTTP server for the labelling tool (no extra dependencies)."""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import schema
from .store import Store

PAGE = Path(__file__).with_name("page.html")
MAX_BODY = 2_000_000


def make_handler(store: Store):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ic-annotate/1"

        def log_message(self, fmt, *args):  # keep the console quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/api/state":
                self._json(
                    {
                        "labeller": store.labeller,
                        "items": store.listing(),
                        "enums": {
                            "site_status": schema.SITE_STATUS,
                            "imprint_location": schema.IMPRINT_LOCATION,
                            "roles": schema.ROLES,
                            "modality": schema.MODALITY,
                            "operator_type": schema.OPERATOR_TYPE,
                            "topics": schema.TOPICS,
                            "flags": schema.FLAGS,
                            "no_address_reason": schema.NO_ADDRESS_REASON,
                        },
                    }
                )
            elif u.path == "/api/item":
                host = parse_qs(u.query).get("host", [""])[0]
                if not store.has_host(host):
                    return self._json({"error": "unknown host"}, 404)
                cap = store.capture(host)
                cap.pop("meta", None)  # nothing from meta.json is shown
                self._json({"capture": cap, "label": store.load_labels().get(host),
                            "prefill": store.prefill(host)})
            elif u.path.startswith("/img/"):
                parts = unquote(u.path[5:]).split("/")
                p = store.image_path(parts[0], parts[1]) if len(parts) == 2 else None
                if p is None:
                    return self._send(404, b"no image", "text/plain")
                ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
                self._send(200, p.read_bytes(), ctype)
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):
            if urlparse(self.path).path != "/api/label":
                return self._send(404, b"not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n <= 0 or n > MAX_BODY:
                    raise ValueError("bad length")
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                label, elapsed = body["label"], body.get("elapsed", 0)
            except (ValueError, KeyError, json.JSONDecodeError):
                return self._json({"ok": False, "errors": ["malformed request"]}, 400)
            rec, errors, warnings = store.save_label(label, elapsed)
            if errors:
                return self._json({"ok": False, "errors": errors}, 400)
            self._json({"ok": True, "warnings": warnings, "saved": rec})

    return Handler


def serve(store: Store, host: str = "127.0.0.1", port: int = 8800) -> None:
    httpd = ThreadingHTTPServer((host, port), make_handler(store))
    print(f"Labeller {store.labeller}: {len(store.items)} items, labels -> {store.labels_path}")
    print(f"Open http://{host}:{port}/  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
