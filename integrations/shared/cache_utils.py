"""
프로젝트간 공유 캐시 유틸리티.
Portfiq의 thread-safe TTLCache 구현에서 추출.

사용법:
    from cache_utils import ThreadSafeTTLCache

    cache = ThreadSafeTTLCache(maxsize=100, ttl=300)
    cache.set("key", "value")
    result = cache.get("key")
    cache.clear()
    stats = cache.stats()
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class ThreadSafeTTLCache:
    """Thread-safe TTL cache wrapper over cachetools.TTLCache.

    Args:
        maxsize: Maximum number of entries.
        ttl: Time-to-live in seconds.
    """

    def __init__(self, maxsize: int = 100, ttl: int = 900) -> None:
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Retrieve a value. Returns None if missing or expired."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Store a value."""
        with self._lock:
            self._cache[key] = value

    def clear(self) -> int:
        """Clear all entries. Returns count of removed entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info("Cache cleared: %d entries removed", count)
            return count

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            return {
                "current_size": len(self._cache),
                "max_size": self._cache.maxsize,
                "ttl_seconds": int(self._cache.ttl),
                "keys": list(self._cache.keys()),
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache
