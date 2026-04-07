from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass(slots=True)
class _CacheEntry(Generic[V]):
    value: V
    expires_at: datetime


class MemoryTTLCache(Generic[K, V]):
    def __init__(self, max_size: int, ttl_seconds: int) -> None:
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = Lock()
        self._entries: OrderedDict[K, _CacheEntry[V]] = OrderedDict()

    def get(self, key: K) -> V | None:
        with self._lock:
            self._evict_expired_locked()
            entry = self._entries.get(key)
            if entry is None:
                return None
            self._entries.move_to_end(key)
            return entry.value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            self._evict_expired_locked()
            self._entries[key] = _CacheEntry(value=value, expires_at=datetime.now(timezone.utc) + self._ttl)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_size:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _evict_expired_locked(self) -> None:
        now = datetime.now(timezone.utc)
        expired_keys = [key for key, entry in self._entries.items() if entry.expires_at <= now]
        for key in expired_keys:
            self._entries.pop(key, None)
