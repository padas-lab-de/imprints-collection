"""
Per-hosting-provider politeness for the fetcher.

Hosts are grouped by the network of their resolved IP address (/24 for IPv4,
/48 for IPv6). Large shared hosters put many thousands of sites behind one
such network (IONOS 217.160.0.0/24, Strato 81.169.145.0/24), so a cap per
network caps the load on one provider front end, while CDNs that spread
tenants over many networks (Cloudflare) are not throttled as a whole.

Two parts:
- ProviderLimiter: per group, at most `max_concurrent` requests at a time and
  at least `min_delay` seconds between request starts; a 429/503 pauses the
  group for `cooldown` seconds.
- HostScheduler: hands hosts to worker threads so that at most
  `max_per_group` hosts of one group are in flight. Hosts of a saturated group
  wait in a per-group queue instead of blocking a worker, and hosts that got a
  429/503 come back once after a back-off.
"""

import heapq
import socket
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from typing import Callable, Deque, Dict, List, Optional, Tuple

# getaddrinfo errors that mean the name does not exist (no point in requesting)
_NO_NAME_ERRORS = {
    getattr(socket, name)
    for name in ("EAI_NONAME", "EAI_NODATA", "EAI_ADDRFAMILY")
    if hasattr(socket, name)
}

NOT_FOUND = "dns"


def network_key(ip: str) -> str:
    """Group key of an IP address: the /24 of an IPv4 address, the /48 of an IPv6 address."""
    if ":" in ip:
        parts = socket.inet_pton(socket.AF_INET6, ip)
        return "v6:" + parts[:6].hex()
    return "v4:" + ".".join(ip.split(".")[:3])


def resolve_key(hostname: str, resolver: Callable = socket.getaddrinfo) -> Optional[str]:
    """
    Resolve a host name and return its group key, NOT_FOUND if the name does not
    exist, or None if resolution failed for another reason (temporary error).
    IPv4 is preferred so that dual-stack hosts group with their IPv4 network.
    """
    try:
        infos = resolver(hostname, 443, 0, socket.SOCK_STREAM)
    except socket.gaierror as e:
        return NOT_FOUND if e.errno in _NO_NAME_ERRORS else None
    except (UnicodeError, OSError, ValueError):
        return None
    if not infos:
        return NOT_FOUND
    infos = sorted(infos, key=lambda i: i[0] != socket.AF_INET)
    return network_key(infos[0][4][0])


def parse_retry_after(value: Optional[str], now: Optional[float] = None) -> Optional[float]:
    """Seconds from a Retry-After header (delta seconds or HTTP date), or None."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError, IndexError):
        return None
    return max(0.0, when - (time.time() if now is None else now))


class _Group:
    __slots__ = ("active", "next_start", "requests", "throttled", "wait")

    def __init__(self) -> None:
        self.active = 0
        self.next_start = 0.0
        self.requests = 0
        self.throttled = 0
        self.wait = 0.0


class ProviderLimiter:
    """Concurrency cap and minimum delay between request starts per provider group."""

    def __init__(
        self,
        max_concurrent: int = 4,
        min_delay: float = 0.25,
        cooldown: float = 10.0,
        resolver: Callable[[str], Optional[str]] = resolve_key,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        cache_size: int = 500_000,
    ) -> None:
        self.max_concurrent = max_concurrent
        self.min_delay = min_delay
        self.cooldown = cooldown
        self._resolver = resolver
        self._clock = clock
        self._sleep = sleep
        self._cache: Dict[str, Optional[str]] = {}
        self._cache_size = cache_size
        self._groups: Dict[str, _Group] = defaultdict(_Group)
        self._cond = threading.Condition()

    @property
    def enabled(self) -> bool:
        return self.max_concurrent > 0

    def key_for(self, hostname: str) -> Optional[str]:
        """Cached group key of a host name (see resolve_key)."""
        hostname = (hostname or "").lower()
        if hostname in self._cache:
            return self._cache[hostname]
        key = self._resolver(hostname)
        if len(self._cache) >= self._cache_size:
            self._cache.clear()
        # Temporary failures are not cached
        if key is not None:
            self._cache[hostname] = key
        return key

    @contextmanager
    def request(self, key: Optional[str]):
        """Hold a request slot of the group `key` (no limit for key None)."""
        if not self.enabled or key is None or key == NOT_FOUND:
            yield
            return
        t0 = self._clock()
        with self._cond:
            group = self._groups[key]
            while group.active >= self.max_concurrent:
                self._cond.wait()
            group.active += 1
            group.requests += 1
            now = self._clock()
            start = max(now, group.next_start)
            group.next_start = start + self.min_delay
        try:
            if start > now:
                self._sleep(start - now)
            with self._cond:
                group.wait += self._clock() - t0
            yield
        finally:
            with self._cond:
                group.active -= 1
                self._cond.notify_all()

    def throttled(self, key: Optional[str]) -> None:
        """Record a 429/503 answer and pause the group for `cooldown` seconds."""
        if key is None or key == NOT_FOUND:
            return
        with self._cond:
            group = self._groups[key]
            group.throttled += 1
            group.next_start = max(group.next_start, self._clock() + self.cooldown)

    def stats(self) -> Dict[str, Tuple[int, int, float]]:
        """Group -> (requests, 429/503 answers, seconds waited)."""
        with self._cond:
            return {k: (g.requests, g.throttled, g.wait) for k, g in self._groups.items()}


class HostScheduler:
    """
    Thread-safe work queue of hosts with a per-group cap on hosts in flight and
    a delayed queue for hosts that are retried later.

    Worker loop:
        item = sched.get()            # None when everything is done
        if not item.admitted:
            item.key = item.key or key_of(item.host)
            if not sched.admit(item): # group saturated, parked
                continue
        ... process ...
        sched.finish(item)  or  sched.retry_later(item, delay)
    """

    class Item:
        __slots__ = ("host", "attempt", "key", "admitted")

        def __init__(self, host: str, attempt: int = 0, key: Optional[str] = None) -> None:
            self.host = host
            self.attempt = attempt
            self.key = key
            self.admitted = False

    def __init__(
        self,
        hosts: List[str],
        max_per_group: int = 4,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_per_group = max_per_group
        self._clock = clock
        self._pending: Deque[HostScheduler.Item] = deque(self.Item(h) for h in hosts)
        self._ready: Deque[HostScheduler.Item] = deque()
        self._waiting: Dict[str, Deque[HostScheduler.Item]] = defaultdict(deque)
        self._in_flight: Dict[str, int] = defaultdict(int)
        self._delayed: List[Tuple[float, int, HostScheduler.Item]] = []
        self._seq = 0
        self._taken = 0  # items handed out and not yet admitted/parked/finished
        self._cond = threading.Condition()

    def _limited(self, key: Optional[str]) -> bool:
        return self.max_per_group > 0 and key is not None and key != NOT_FOUND

    def _release_due(self) -> Optional[float]:
        """Move due delayed items to the front of the queue; return seconds to the next one."""
        now = self._clock()
        while self._delayed and self._delayed[0][0] <= now:
            _, _, item = heapq.heappop(self._delayed)
            self._ready.appendleft(item)
        return self._delayed[0][0] - now if self._delayed else None

    def get(self, poll: float = 1.0) -> Optional["HostScheduler.Item"]:
        with self._cond:
            while True:
                next_due = self._release_due()
                if self._ready:
                    item = self._ready.popleft()
                elif self._pending:
                    item = self._pending.popleft()
                else:
                    item = None
                if item is not None:
                    self._taken += 1
                    return item
                waiting = any(self._waiting.values())
                in_flight = sum(self._in_flight.values())
                if not self._delayed and not waiting and not in_flight and not self._taken:
                    self._cond.notify_all()
                    return None
                timeout = poll if next_due is None else min(poll, max(next_due, 0.01))
                self._cond.wait(timeout)

    def admit(self, item: "HostScheduler.Item") -> bool:
        """Start the item if its group has room, else park it (returns False)."""
        with self._cond:
            self._taken -= 1
            if self._limited(item.key) and self._in_flight[item.key] >= self.max_per_group:
                self._waiting[item.key].append(item)
                return False
            if self._limited(item.key):
                self._in_flight[item.key] += 1
            item.admitted = True
            self._taken += 1
            return True

    def _free_slot(self, key: Optional[str]) -> None:
        if not self._limited(key):
            return
        self._in_flight[key] -= 1
        queue = self._waiting.get(key)
        if queue:
            nxt = queue.popleft()
            self._in_flight[key] += 1
            nxt.admitted = True
            self._ready.append(nxt)
        if not self._in_flight[key]:
            del self._in_flight[key]
        if queue is not None and not queue:
            del self._waiting[key]

    def finish(self, item: "HostScheduler.Item") -> None:
        with self._cond:
            self._taken -= 1
            if item.admitted:
                self._free_slot(item.key)
            self._cond.notify_all()

    def retry_later(self, item: "HostScheduler.Item", delay: float) -> None:
        """Give the slot back and queue the host again after `delay` seconds."""
        with self._cond:
            self._taken -= 1
            if item.admitted:
                self._free_slot(item.key)
            retry = self.Item(item.host, item.attempt + 1, item.key)
            self._seq += 1
            heapq.heappush(self._delayed, (self._clock() + delay, self._seq, retry))
            self._cond.notify_all()

    def snapshot(self) -> Dict[str, object]:
        with self._cond:
            waiting = sorted(
                ((len(q), k) for k, q in self._waiting.items() if q), reverse=True
            )
            return {
                "pending": len(self._pending),
                "ready": len(self._ready),
                "parked": sum(n for n, _ in waiting),
                "top_parked": [(k, n) for n, k in waiting[:3]],
                "delayed": len(self._delayed),
                "in_flight_limited": sum(self._in_flight.values()),
            }
