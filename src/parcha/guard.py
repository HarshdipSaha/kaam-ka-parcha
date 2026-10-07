"""Public-demo hardening: per-client rate limits, upload caps, optional access code.

Everything here is pure and in-memory (one instance, one worker, like the session store). Limits of 0
mean "off", which is the local-development default; deployment sets them through the environment.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import hmac
from threading import Lock
import time
from typing import Callable

ACCESS_COOKIE = "demo_access"
GUARDED_PATH_PARTS = ("/intake", "/reask/", "/readback", "/reply", "/fallback", "/consent")


class SlidingWindow:
    """At most `limit` hits per `window` seconds per key; `limit <= 0` disables the check."""

    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.monotonic):
        self.limit, self.window, self._clock = limit, window, clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str) -> float:
        """Record a hit. Returns 0.0 if allowed, else the seconds to wait before retrying."""
        if self.limit <= 0:
            return 0.0
        now = self._clock()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return max(0.1, self.window - (now - q[0]))
            q.append(now)
            if len(self._hits) > 10_000:
                for stale in [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]:
                    del self._hits[stale]
            return 0.0


def client_ip(headers, peer: str | None, trust_proxy: bool) -> str:
    """The caller's address. Behind one trusted proxy the rightmost X-Forwarded-For entry is the one the
    proxy itself appended; earlier entries are client-supplied and spoofable."""
    if trust_proxy:
        forwarded = headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[-1]
    return peer or "unknown"


def access_token(code: str) -> str:
    return hmac.new(code.encode(), b"parcha-demo-access", hashlib.sha256).hexdigest()


def access_ok(code: str, cookie: str | None) -> bool:
    return not code or (cookie is not None and hmac.compare_digest(cookie, access_token(code)))


def is_guarded(method: str, path: str) -> bool:
    """POSTs that create sessions or spend speech/LLM credits."""
    if method != "POST":
        return False
    return path == "/sessions" or (path.startswith("/sessions/") and any(p in path for p in GUARDED_PATH_PARTS))
