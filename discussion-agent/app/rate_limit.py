"""Per-process sliding-window rate limiter.

Known limitation (see plan's Security Boundaries section): this counts
requests in a single process's memory. Under multi-instance Cloud Run
scaling it under-counts — each instance has its own window — so it is a
best-effort abuse deterrent for this phase, not a hard guarantee. Closing
that gap needs a shared counter store (Firestore/Redis), deliberately out
of scope here.
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowRateLimiter:
    def __init__(
        self,
        max_requests: int,
        window_seconds: float,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._now = now
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        timestamps = self._requests[key]
        self._evict_expired(timestamps)
        if len(timestamps) >= self._max_requests:
            return False
        timestamps.append(self._now())
        return True

    def retry_after(self, key: str) -> int:
        timestamps = self._requests[key]
        self._evict_expired(timestamps)
        if not timestamps:
            return 0
        oldest = timestamps[0]
        remaining = self._window_seconds - (self._now() - oldest)
        return max(0, int(remaining))

    def _evict_expired(self, timestamps: deque[float]) -> None:
        cutoff = self._now() - self._window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
