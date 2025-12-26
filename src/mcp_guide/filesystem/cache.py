"""File content caching with LRU eviction."""

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Cache entry with content and metadata."""

    content: str
    size: int
    mtime: float
    cached_at: float
    access_count: int = 0


class FileCache:
    """LRU cache for file contents with size limits and TTL."""

    def __init__(self, max_size: int = 10 * 1024 * 1024, max_entries: int = 1000):
        """Initialize FileCache.

        Args:
            max_size: Maximum cache size in bytes
            max_entries: Maximum number of cache entries
        """
        self.max_size = max_size
        self.max_entries = max_entries
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._current_size = 0
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "invalidations": 0}

    def get(self, path: str, current_mtime: Optional[float] = None) -> Optional[str]:
        """Get cached content for path.

        Args:
            path: File path
            current_mtime: Current modification time for invalidation check

        Returns:
            Cached content if valid, None otherwise
        """
        if path not in self._cache:
            self._stats["misses"] += 1
            return None

        entry = self._cache[path]

        # Check if entry is invalidated by modification time
        if current_mtime is not None and entry.mtime < current_mtime:
            self.invalidate(path)
            self._stats["misses"] += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(path)
        entry.access_count += 1
        self._stats["hits"] += 1
        return entry.content

    def put(self, path: str, content: str, mtime: Optional[float] = None) -> None:
        """Cache content for path.

        Args:
            path: File path
            content: File content
            mtime: File modification time
        """
        if mtime is None:
            mtime = time.time()

        content_size = len(content.encode("utf-8"))

        # Remove existing entry if present
        if path in self._cache:
            self._current_size -= self._cache[path].size
            del self._cache[path]

        # Evict entries if needed
        self._evict_if_needed(content_size)

        # Add new entry
        entry = CacheEntry(content=content, size=content_size, mtime=mtime, cached_at=time.time())
        self._cache[path] = entry
        self._current_size += content_size

    def invalidate(self, path: str) -> bool:
        """Invalidate cached entry for path.

        Args:
            path: File path to invalidate

        Returns:
            True if entry was invalidated, False if not found
        """
        if path in self._cache:
            entry = self._cache.pop(path)
            self._current_size -= entry.size
            self._stats["invalidations"] += 1
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._current_size = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "entries": len(self._cache),
            "size_bytes": self._current_size,
            "hit_rate": hit_rate,
            "max_size": self.max_size,
            "max_entries": self.max_entries,
        }

    def _evict_if_needed(self, new_entry_size: int) -> None:
        """Evict LRU entries if needed to make space."""
        # Evict by count limit
        while len(self._cache) >= self.max_entries:
            self._evict_lru()

        # Evict by size limit
        while self._current_size + new_entry_size > self.max_size and self._cache:
            self._evict_lru()

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._cache:
            path, entry = self._cache.popitem(last=False)  # Remove first (LRU)
            self._current_size -= entry.size
            self._stats["evictions"] += 1
