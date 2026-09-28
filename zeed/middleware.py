import time
import threading

from .logger import get_logger

log = get_logger("zeed.middleware")


class BaseMiddleware:
    def __call__(self, handler, event, data):
        return handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, logger=None):
        self.log = logger or log

    def __call__(self, handler, event, data):
        name = getattr(handler, "__name__", repr(handler))
        self.log.debug("-> %s", name)
        try:
            result = handler(event, data)
            self.log.debug("<- %s ok", name)
            return result
        except Exception:
            self.log.exception("X %s failed", name)
            raise


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate=0.5, key_func=None, cleanup_every=1000):
        self.rate = float(rate)
        self._last = {}
        self._lock = threading.RLock()
        self._calls = 0
        self._cleanup_every = cleanup_every
        self._key_func = key_func or self._default_key

    @staticmethod
    def _default_key(event):
        u = getattr(event, "from_user", None)
        return u.id if u else None

    def _cleanup(self, now):
        ttl = max(self.rate * 10, 60)
        stale = [k for k, t in self._last.items() if now - t > ttl]
        for k in stale:
            self._last.pop(k, None)

    def __call__(self, handler, event, data):
        k = self._key_func(event)
        if k is None:
            return handler(event, data)
        now = time.monotonic()
        with self._lock:
            self._calls += 1
            if self._calls % self._cleanup_every == 0:
                self._cleanup(now)
            last = self._last.get(k, 0.0)
            if now - last < self.rate:
                return None
            self._last[k] = now
        return handler(event, data)


class TimingMiddleware(BaseMiddleware):
    def __init__(self, logger=None, threshold=0.5):
        self.log = logger or log
        self.threshold = threshold

    def __call__(self, handler, event, data):
        t0 = time.perf_counter()
        try:
            return handler(event, data)
        finally:
            dt = time.perf_counter() - t0
            if dt >= self.threshold:
                self.log.warning(
                    "slow handler %s: %.3fs",
                    getattr(handler, "__name__", "?"), dt,
                )