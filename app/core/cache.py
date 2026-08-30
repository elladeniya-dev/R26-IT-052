"""Tiny in-process TTL cache."""
import time
from typing import Any, Callable


class TTLCache:
    def __init__(self, ttl_seconds: float = 60.0):
        self.ttl_seconds = ttl_seconds
        self._store: dict[Any, tuple[float, Any]] = {}

    def get_or_set(self, key: Any, factory: Callable[[], Any]) -> Any:
        now = time.monotonic()
        cached = self._store.get(key)
        if cached is not None and now - cached[0] < self.ttl_seconds:
            return cached[1]
        value = factory()
        self._store[key] = (now, value)
        return value

    def invalidate(self, key: Any | None = None) -> None:
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)
