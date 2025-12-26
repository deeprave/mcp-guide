"""Tests for file content caching."""

from mcp_guide.filesystem.cache import FileCache


class TestFileCache:
    """Tests for FileCache class."""

    def test_cache_basic_operations(self):
        """FileCache should support basic get/put operations."""
        cache = FileCache()

        # Cache miss
        assert cache.get("file1.txt") is None

        # Cache put and hit
        cache.put("file1.txt", "content1", mtime=1000.0)
        assert cache.get("file1.txt") == "content1"

    def test_cache_different_content_types(self):
        """FileCache should handle different content types."""
        cache = FileCache()

        # Text content
        cache.put("text.txt", "Hello World", mtime=1000.0)
        assert cache.get("text.txt") == "Hello World"

        # JSON-like content
        cache.put("data.json", '{"key": "value"}', mtime=1001.0)
        assert cache.get("data.json") == '{"key": "value"}'

        # Empty content
        cache.put("empty.txt", "", mtime=1002.0)
        assert cache.get("empty.txt") == ""

        # Unicode content
        cache.put("unicode.txt", "Hello 世界 🌍", mtime=1003.0)
        assert cache.get("unicode.txt") == "Hello 世界 🌍"

    def test_cache_modification_time_invalidation(self):
        """FileCache should invalidate entries based on modification time."""
        cache = FileCache()

        cache.put("file.txt", "old content", mtime=1000.0)
        assert cache.get("file.txt", current_mtime=1000.0) == "old content"

        # File modified - should invalidate
        assert cache.get("file.txt", current_mtime=1001.0) is None

    def test_cache_lru_eviction_by_count(self):
        """FileCache should evict LRU entries when count limit exceeded."""
        cache = FileCache(max_entries=2)

        cache.put("file1.txt", "content1", mtime=1000.0)
        cache.put("file2.txt", "content2", mtime=1001.0)

        # Both should be cached
        assert cache.get("file1.txt") == "content1"
        assert cache.get("file2.txt") == "content2"

        # Add third file - should evict LRU (file1)
        cache.put("file3.txt", "content3", mtime=1002.0)

        assert cache.get("file1.txt") is None  # Evicted
        assert cache.get("file2.txt") == "content2"
        assert cache.get("file3.txt") == "content3"

    def test_cache_lru_eviction_by_size(self):
        """FileCache should evict LRU entries when size limit exceeded."""
        cache = FileCache(max_size=20)  # 20 bytes

        cache.put("file1.txt", "12345", mtime=1000.0)  # 5 bytes
        cache.put("file2.txt", "67890", mtime=1001.0)  # 5 bytes

        # Add large file that exceeds limit - should evict file1
        cache.put("file3.txt", "1234567890123", mtime=1002.0)  # 13 bytes

        assert cache.get("file1.txt") is None  # Evicted
        assert cache.get("file2.txt") == "67890"  # Still cached (5+13=18 < 20)
        assert cache.get("file3.txt") == "1234567890123"

    def test_cache_statistics(self):
        """FileCache should track performance statistics."""
        cache = FileCache(max_entries=2)

        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["entries"] == 0

        # Cache miss
        cache.get("missing.txt")
        stats = cache.get_stats()
        assert stats["misses"] == 1

        # Cache put and hit
        cache.put("file.txt", "content", mtime=1000.0)
        cache.get("file.txt")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["entries"] == 1

        # Eviction
        cache.put("file2.txt", "content2", mtime=1001.0)
        cache.put("file3.txt", "content3", mtime=1002.0)  # Should evict file.txt
        stats = cache.get_stats()
        assert stats["evictions"] == 1

        # Hit rate calculation
        assert stats["hit_rate"] == 1 / 2  # 1 hit out of 2 total requests

    def test_cache_invalidation(self):
        """FileCache should support manual invalidation."""
        cache = FileCache()

        cache.put("file.txt", "content", mtime=1000.0)
        assert cache.get("file.txt") == "content"

        # Manual invalidation
        assert cache.invalidate("file.txt") is True
        assert cache.get("file.txt") is None

        # Invalidate non-existent file
        assert cache.invalidate("missing.txt") is False

        stats = cache.get_stats()
        assert stats["invalidations"] == 1

    def test_cache_clear(self):
        """FileCache should support clearing all entries."""
        cache = FileCache()

        cache.put("file1.txt", "content1", mtime=1000.0)
        cache.put("file2.txt", "content2", mtime=1001.0)

        assert cache.get_stats()["entries"] == 2

        cache.clear()

        assert cache.get("file1.txt") is None
        assert cache.get("file2.txt") is None
        assert cache.get_stats()["entries"] == 0

    def test_cache_access_count_tracking(self):
        """FileCache should track access counts for entries."""
        cache = FileCache()

        cache.put("file.txt", "content", mtime=1000.0)

        # Access multiple times
        cache.get("file.txt")
        cache.get("file.txt")
        cache.get("file.txt")

        # Verify access behavior through public stats API
        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 0
