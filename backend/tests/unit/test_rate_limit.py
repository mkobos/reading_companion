from app.rate_limit import SlidingWindowRateLimiter


def test_allows_requests_up_to_the_limit():
    clock = _FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60, now=clock.now)

    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True


def test_rejects_requests_over_the_limit_within_the_window():
    clock = _FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60, now=clock.now)

    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False


def test_allows_again_once_the_window_has_elapsed():
    clock = _FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, now=clock.now)

    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False

    clock.advance(61)

    assert limiter.allow("client-a") is True


def test_keys_are_independent():
    clock = _FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, now=clock.now)

    assert limiter.allow("client-a") is True
    assert limiter.allow("client-b") is True
    assert limiter.allow("client-a") is False
    assert limiter.allow("client-b") is False


def test_retry_after_reports_seconds_until_the_oldest_request_expires():
    clock = _FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, now=clock.now)

    limiter.allow("client-a")
    clock.advance(10)
    limiter.allow("client-a")

    assert limiter.retry_after("client-a") == 50


class _FakeClock:
    def __init__(self) -> None:
        self._t = 1000.0

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds
