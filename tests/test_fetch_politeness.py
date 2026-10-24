"""E13: per-provider limiter, host scheduler, 429/503 retry and batch resume (no network)."""

import gzip
import json
import os
import socket
import threading
import time

import pytest

import ic.cli.fetch as fetch
from ic.utils.fetch_state import (
    iter_gzip_lines_tolerant,
    read_done_hosts,
    salvage_batch_output,
)
from ic.utils.politeness import (
    NOT_FOUND,
    HostScheduler,
    ProviderLimiter,
    network_key,
    parse_retry_after,
    resolve_key,
)

# --- grouping -------------------------------------------------------------


def test_network_key_groups_ipv4_by_24_and_ipv6_by_48():
    assert network_key("81.169.145.97") == network_key("81.169.145.12") == "v4:81.169.145"
    assert network_key("81.169.146.1") != network_key("81.169.145.1")
    assert network_key("2a01:238:20a:202:1000::1") == network_key("2a01:238:20a:ffff::2")


def test_resolve_key_prefers_ipv4_and_maps_missing_names():
    def resolver(host, port, family, socktype):
        if host == "gone.de":
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        if host == "flaky.de":
            raise socket.gaierror(socket.EAI_AGAIN, "Temporary failure")
        return [
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2a01:238::1", 443, 0, 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("217.160.0.5", 443)),
        ]

    assert resolve_key("x.de", resolver) == "v4:217.160.0"
    assert resolve_key("gone.de", resolver) == NOT_FOUND
    assert resolve_key("flaky.de", resolver) is None


def test_parse_retry_after():
    assert parse_retry_after("120") == 120.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("soon") is None
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT", now=1445412480 - 30) == 30.0


# --- limiter --------------------------------------------------------------


class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.sleeps = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(round(s, 3))
        self.t += s


def test_limiter_spaces_request_starts_per_group():
    clock = FakeClock()
    lim = ProviderLimiter(max_concurrent=4, min_delay=0.5, clock=clock, sleep=clock.sleep)
    for _ in range(3):
        with lim.request("v4:1.2.3"):
            pass
    with lim.request("v4:9.9.9"):  # other group: no wait
        pass
    assert clock.sleeps == [0.5, 0.5]
    assert lim.stats()["v4:1.2.3"][0] == 3


def test_limiter_caps_concurrent_requests_per_group():
    lim = ProviderLimiter(max_concurrent=2, min_delay=0.0)
    active = {"a": 0, "b": 0}
    peak = {"a": 0, "b": 0}
    lock = threading.Lock()

    def job(group):
        with lim.request(group):
            with lock:
                active[group] += 1
                peak[group] = max(peak[group], active[group])
            time.sleep(0.02)
            with lock:
                active[group] -= 1

    threads = [threading.Thread(target=job, args=(g,)) for g in "ab" * 6]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert peak == {"a": 2, "b": 2}


def test_limiter_cooldown_after_throttle_and_no_limit_for_unknown_group():
    clock = FakeClock()
    lim = ProviderLimiter(max_concurrent=4, min_delay=0.0, cooldown=10, clock=clock, sleep=clock.sleep)
    with lim.request("g"):
        pass
    lim.throttled("g")
    with lim.request("g"):
        pass
    assert clock.sleeps == [10.0]
    with lim.request(None):
        pass
    lim.throttled(None)
    assert lim.stats()["g"][1] == 1


def test_disabled_limiter_does_not_wait():
    clock = FakeClock()
    lim = ProviderLimiter(max_concurrent=0, min_delay=5, clock=clock, sleep=clock.sleep)
    for _ in range(3):
        with lim.request("g"):
            pass
    assert clock.sleeps == []


def test_key_for_caches_but_not_temporary_failures():
    calls = []

    def resolver(host):
        calls.append(host)
        return None if host == "flaky.de" else "v4:1.2.3"

    lim = ProviderLimiter(resolver=resolver)
    assert lim.key_for("a.de") == lim.key_for("A.de") == "v4:1.2.3"
    lim.key_for("flaky.de")
    lim.key_for("flaky.de")
    assert calls == ["a.de", "flaky.de", "flaky.de"]


# --- scheduler ------------------------------------------------------------


def test_scheduler_parks_hosts_of_saturated_group_without_blocking():
    sched = HostScheduler(["a1", "a2", "a3", "b1"], max_per_group=2)
    keys = {"a1": "A", "a2": "A", "a3": "A", "b1": "B"}
    running = []
    for _ in range(4):
        item = sched.get()
        item.key = keys[item.host]
        if sched.admit(item):
            running.append(item)
    assert [i.host for i in running] == ["a1", "a2", "b1"]
    assert sched.snapshot()["parked"] == 1
    # Finishing an A host releases a3, already admitted
    sched.finish(running[0])
    nxt = sched.get()
    assert nxt.host == "a3" and nxt.admitted
    for item in running[1:] + [nxt]:
        sched.finish(item)
    assert sched.get(poll=0.01) is None


def test_scheduler_retry_later_comes_back_once_after_delay():
    clock = FakeClock()
    sched = HostScheduler(["h"], max_per_group=1, clock=clock)
    item = sched.get()
    item.key = "G"
    assert sched.admit(item)
    sched.retry_later(item, 60)
    assert sched.snapshot()["delayed"] == 1
    clock.t = 59
    got = []
    t = threading.Thread(target=lambda: got.append(sched.get(poll=0.01)))
    t.start()
    time.sleep(0.05)
    assert not got  # not yet due
    clock.t = 61
    t.join(1)
    assert got[0].host == "h" and got[0].attempt == 1 and got[0].key == "G"
    assert sched.admit(got[0])
    sched.finish(got[0])
    assert sched.get(poll=0.01) is None


def test_scheduler_threads_respect_group_cap():
    hosts = [f"h{i}" for i in range(40)]
    sched = HostScheduler(hosts, max_per_group=3)
    lock = threading.Lock()
    active, peak, seen = {}, {}, []

    def worker():
        while True:
            item = sched.get(poll=0.01)
            if item is None:
                return
            if not item.admitted:
                item.key = "G" if int(item.host[1:]) % 2 else None
                if not sched.admit(item):
                    continue
            with lock:
                active[item.key] = active.get(item.key, 0) + 1
                peak[item.key] = max(peak.get(item.key, 0), active[item.key])
                seen.append(item.host)
            time.sleep(0.005)
            with lock:
                active[item.key] -= 1
            sched.finish(item)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert sorted(seen) == sorted(hosts)
    assert peak["G"] == 3 and peak[None] > 3


# --- try_fetch with 429/503 -----------------------------------------------


class Resp:
    def __init__(self, code, content=b"", headers=None):
        self.status_code = code
        self.content = content
        self.headers = headers or {}


def _limited(monkeypatch, responses):
    lim = ProviderLimiter(max_concurrent=4, min_delay=0.0, cooldown=0.0, resolver=lambda h: "v4:1.2.3")
    monkeypatch.setattr(fetch, "LIMITER", lim)
    monkeypatch.setattr(fetch, "RETRY_PAUSE", 0)
    it = iter(responses)
    monkeypatch.setattr(fetch, "requests_get_with_timeout", lambda *a, **k: next(it))
    return lim


def test_throttled_answer_defers_host_on_first_attempt(monkeypatch):
    lim = _limited(monkeypatch, [Resp(503, headers={"Retry-After": "120"})])
    fetch._ctx.allow_defer = True
    with pytest.raises(fetch.RetryLater) as e:
        fetch.try_fetch("https://example.de/", retry=True)
    assert e.value.status_code == 503 and e.value.retry_after == 120
    assert lim.stats()["v4:1.2.3"][1] == 1


def test_throttled_answer_on_retry_attempt_behaves_as_before(monkeypatch):
    html = "<html><body><p>Hallo Welt</p></body></html>".encode()
    _limited(monkeypatch, [Resp(503), Resp(200, html)])
    fetch._ctx.allow_defer = False
    url, text = fetch.try_fetch("https://example.de/", retry=True)
    assert url == "https://example.de/" and "Hallo" in text
    _limited(monkeypatch, [Resp(429)])
    assert fetch.try_fetch("https://example.de/", retry=True) == (None, None)
    assert fetch._ctx.last_error == "http429"


def test_unresolvable_host_is_not_requested(monkeypatch):
    lim = ProviderLimiter(resolver=lambda h: NOT_FOUND)
    monkeypatch.setattr(fetch, "LIMITER", lim)

    def boom(*a, **k):
        raise AssertionError("requested")

    monkeypatch.setattr(fetch, "requests_get_with_timeout", boom)
    assert fetch.try_fetch("https://gone.de/") == (None, None)
    assert fetch._ctx.last_error == "dns"


# --- resume ---------------------------------------------------------------


def _write_cut_gzip(path, records, extra_partial=True):
    """Write records like the fetcher (flush per line) and cut the file like a kill."""
    f = gzip.open(path, "wt", encoding="UTF-8")
    for r in records:
        f.write(json.dumps(r) + "\n")
        f.flush()
    if extra_partial:
        f.write('{"host": "partial.de", "main"')
        f.flush()
    raw = open(path, "rb").read()  # no gzip trailer yet: as left by SIGKILL
    open(path, "wb").write(raw)


def test_salvage_keeps_logged_records_of_cut_file(tmp_path):
    path = str(tmp_path / "imprints_batch000000.jsonl.gz")
    _write_cut_gzip(path, [{"host": "a.de"}, {"host": "b.de"}, {"host": "c.de"}])
    assert [json.loads(l)["host"] for l in iter_gzip_lines_tolerant(path)] == ["a.de", "b.de", "c.de"]
    assert salvage_batch_output(path, {"a.de", "b.de"}) == 2
    with gzip.open(path, "at", encoding="UTF-8") as f:
        f.write(json.dumps({"host": "d.de"}) + "\n")
    with gzip.open(path, "rt", encoding="UTF-8") as f:
        assert [json.loads(l)["host"] for l in f] == ["a.de", "b.de", "d.de"]


def test_read_done_hosts_ignores_cut_last_line(tmp_path):
    path = tmp_path / "fetch_status_batch000000.tsv"
    cols = "host\tstatus\tdetail\tprovider\tattempts\trequests\tthrottled\tseconds\tend_time\n"
    path.write_text(cols + "a.de\timprint_found\t\tv4:1.2.3\t1\t5\t0\t1.0\t1\nb.de\timpr")
    assert read_done_hosts(str(path)) == {"a.de"}


def _fake_process_host(calls, crash_after=None, throttle_once=()):
    seen_throttle = set()

    def fake(host, output_file, output_lock, pbar, hosts_dict):
        calls.append(host)
        if host in throttle_once and host not in seen_throttle:
            seen_throttle.add(host)
            raise fetch.RetryLater(503, 0)
        if crash_after is not None and len(calls) > crash_after:
            raise KeyboardInterrupt  # stands in for a kill: not caught by the worker
        with output_lock:
            output_file.write(json.dumps({"host": host}) + "\n")
            output_file.flush()
        return fetch.CrawlStatus.IMPRINT_FOUND

    return fake


def test_run_batch_resumes_and_retries_throttled_host(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "OUTPUT_DIR", str(tmp_path))
    hosts = [f"h{i}.de" for i in range(20)]
    lim = ProviderLimiter(max_concurrent=2, min_delay=0.0, resolver=lambda h: "v4:1.2.3")

    # First run: a single worker processes 7 hosts, then the 8th "crashes" the run
    calls = []
    monkeypatch.setattr(fetch, "process_host", _fake_process_host(calls, crash_after=7))
    with pytest.raises(KeyboardInterrupt):
        sched_run = fetch.run_batch  # run the worker loop in this thread
        _run_inline(sched_run, hosts, lim, monkeypatch)
    status_path = tmp_path / "fetch_status_batch000000.tsv"
    assert len(read_done_hosts(str(status_path))) == 7

    # Second run: only the 13 missing hosts, one of them answers 503 once
    calls2 = []
    monkeypatch.setattr(
        fetch, "process_host", _fake_process_host(calls2, throttle_once={"h15.de"})
    )
    counts = fetch.run_batch(0, hosts, 4, lim, retry_backoff=0, progress_interval=60)
    assert sorted(set(calls2)) == sorted(hosts[7:])
    assert calls2.count("h15.de") == 2
    assert counts["deferred"] == 1 and counts[fetch.CrawlStatus.IMPRINT_FOUND] == 13
    with gzip.open(tmp_path / "imprints_batch000000.jsonl.gz", "rt") as f:
        assert sorted(json.loads(l)["host"] for l in f) == sorted(hosts)
    lines = status_path.read_text().splitlines()
    assert len(lines) == 21 and lines[0].startswith("host\t")
    row = [l.split("\t") for l in lines if l.startswith("h15.de\t")][0]
    assert row[3] == "v4:1.2.3" and row[4] == "2"

    # Third run: batch complete, nothing fetched
    calls3 = []
    monkeypatch.setattr(fetch, "process_host", _fake_process_host(calls3))
    assert fetch.run_batch(0, hosts, 4, lim) == {}
    assert calls3 == []


def _run_inline(run_batch, hosts, lim, monkeypatch):
    """Run run_batch with worker threads replaced by inline execution, so an
    exception in process_host ends the run like a killed process."""

    class InlineThread:
        def __init__(self, target, daemon=True):
            self.target = target

        def start(self):
            if self.target.__name__ == "worker":
                self.target()

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(fetch.threading, "Thread", InlineThread)
    try:
        run_batch(0, hosts, 1, lim, retry_backoff=0, progress_interval=60)
    finally:
        monkeypatch.setattr(fetch.threading, "Thread", threading.Thread)
