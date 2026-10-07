from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException


class RateLimiter:
    """Single-process limiter; a Redis-backed store can replace it without changing the API contract."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            cutoff = now - window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now))
                raise HTTPException(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    detail={
                        "code": "RATE_LIMITED",
                        "message": "Too many analysis requests. Please try again later.",
                        "retry_after_seconds": retry_after,
                    },
                )
            events.append(now)
