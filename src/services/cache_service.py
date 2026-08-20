import threading
import time

from config import settings


class SentimentCache:
    def __init__(self, maxsize: int = 10_000, ttl: float = 300.0) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._entries: dict[tuple[str, str], tuple[float, dict[str, float]]] = {}
        self._lock = threading.Lock()

    def get(self, text: str, language: str) -> dict[str, float] | None:
        key = (language, text)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() >= expires_at:
                del self._entries[key]
                return None
            return value

    def set(self, text: str, language: str, value: dict[str, float]) -> None:
        key = (language, text)
        with self._lock:
            if len(self._entries) >= self._maxsize:
                oldest_key = next(iter(self._entries))
                del self._entries[oldest_key]
            self._entries[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> int:
        with self._lock:
            cleared = len(self._entries)
            self._entries.clear()
        return cleared

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)


sentiment_cache = SentimentCache(
    maxsize=settings.cache_maxsize, ttl=settings.cache_ttl_seconds
)
