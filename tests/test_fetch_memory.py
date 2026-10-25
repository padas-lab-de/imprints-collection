"""E20: a request the caller gave up on must not keep downloading in the background."""

import gzip
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import ic.cli.fetch as fetch

PAGE = "<html><body><p>Impressum Müller GmbH</p></body></html>".encode("UTF-8")


class _Handler(BaseHTTPRequestHandler):
    sent = {}  # path -> bytes of body sent so far

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/page":
            body = PAGE
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/gzip":
            body = gzip.compress(PAGE * 1000)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/stream":
            # Endless body (like an internet radio stream), 64 KiB every 10 ms;
            # stops after 20 s so that a failing test does not hang the run
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.end_headers()
            chunk = b"x" * 65536
            end = time.time() + 20
            try:
                while time.time() < end:
                    self.wfile.write(chunk)
                    _Handler.sent[self.path] = _Handler.sent.get(self.path, 0) + len(chunk)
                    time.sleep(0.01)
            except (BrokenPipeError, ConnectionResetError):
                return


@pytest.fixture
def server():
    _Handler.sent = {}
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.daemon_threads = True
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _request_threads():
    return [t for t in threading.enumerate() if t.name.startswith("ThreadPoolExecutor")]


def test_response_body_is_read_as_before(server):
    resp = fetch.requests_get_with_timeout(server + "/page", 5, allow_redirects=False)
    assert resp is not None and resp.status_code == 200
    assert resp.content == PAGE
    resp = fetch.requests_get_with_timeout(server + "/gzip", 5, allow_redirects=False)
    assert resp.content == PAGE * 1000  # decoded like resp.content without stream


def test_abandoned_endless_body_stops_downloading(server):
    before = set(_request_threads())
    fetch._ctx.last_error = "none"
    resp = fetch.requests_get_with_timeout(server + "/stream", 0.5, allow_redirects=False)
    assert resp is None
    assert fetch._ctx.last_error == "timeout"
    # The orphaned request thread must end soon instead of reading forever
    deadline = time.time() + 3
    while time.time() < deadline and set(_request_threads()) - before:
        time.sleep(0.05)
    assert not set(_request_threads()) - before
    sent = _Handler.sent.get("/stream", 0)
    time.sleep(0.5)
    # Server stops being read: at most what fits in the socket buffers is sent on
    assert _Handler.sent.get("/stream", 0) - sent < 8 * 2**20
