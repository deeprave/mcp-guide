"""Tests for file locking mechanism."""

import asyncio
import os
import time
from pathlib import Path

import pytest

from mcp_guide.file_lock import is_lock_stale, is_process_running, lock_update


class TestProcessChecking:
    """Tests for process validation."""

    def test_is_process_running_current_process(self):
        """Current process should be detected as running."""
        assert is_process_running(os.getpid()) is True

    def test_is_process_running_nonexistent_process(self):
        """Nonexistent process should not be detected as running."""
        # Use a very high PID that's unlikely to exist
        assert is_process_running(999999) is False


class TestStaleLockDetection:
    """Tests for stale lock detection."""

    def test_is_lock_stale_old_file(self, tmp_path):
        """Lock file older than timeout should be stale."""
        lock_file = tmp_path / "test.lock"
        lock_file.write_text("hostname:12345")

        # Set mtime to 11 minutes ago (past 10 minute threshold)
        old_time = time.time() - 660
        os.utime(lock_file, (old_time, old_time))

        assert is_lock_stale(lock_file, "hostname") is True

    def test_is_lock_stale_recent_file_same_host(self, tmp_path):
        """Recent lock file from same host should not be stale."""
        lock_file = tmp_path / "test.lock"
        hostname = os.uname().nodename.split(".")[0]
        lock_file.write_text(f"{hostname}:{os.getpid()}")

        assert is_lock_stale(lock_file, hostname) is False

    def test_is_lock_stale_different_host_dead_process(self, tmp_path):
        """Lock from different host with dead process should be stale."""
        lock_file = tmp_path / "test.lock"
        lock_file.write_text("otherhost:999999")

        assert is_lock_stale(lock_file, "localhost") is True

    def test_is_lock_stale_invalid_format(self, tmp_path):
        """Lock file with invalid format should be stale."""
        lock_file = tmp_path / "test.lock"
        lock_file.write_text("invalid")

        assert is_lock_stale(lock_file, "localhost") is True

    def test_is_lock_stale_missing_file(self, tmp_path):
        """Missing lock file should be considered stale."""
        lock_file = tmp_path / "nonexistent.lock"

        assert is_lock_stale(lock_file, "localhost") is True

    def test_is_lock_stale_empty_file(self, tmp_path):
        """Empty lock file should be stale."""
        lock_file = tmp_path / "test.lock"
        lock_file.write_text("")

        assert is_lock_stale(lock_file, "localhost") is True


class TestLockUpdate:
    """Tests for lock_update function."""

    @pytest.mark.anyio
    async def test_lock_update_removes_lock_on_error(self, tmp_path):
        """lock_update should remove lock even if function raises error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        lock_file = test_file.with_suffix(".txt.lock")

        async def failing_function(file_path: Path) -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await lock_update(test_file, failing_function)

        # Lock should be removed even after error
        assert not lock_file.exists()

    @pytest.mark.anyio
    async def test_contending_updates_are_serialised_and_release_the_lock(self, tmp_path, monkeypatch):
        monkeypatch.setattr("mcp_guide.file_lock.LOCK_RETRY_SECONDS", 0.001)
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial")
        lock_file = test_file.with_suffix(".txt.lock")
        first_entered, contended, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

        def observe_contention(path, hostname):
            contended.set()
            return is_lock_stale(path, hostname)

        monkeypatch.setattr("mcp_guide.file_lock.is_lock_stale", observe_contention)

        async def update(file_path, suffix):
            assert lock_file.exists()
            content = file_path.read_text()
            if suffix == "first":
                first_entered.set()
                await release.wait()
            file_path.write_text(content + " " + suffix)
            return suffix

        first = asyncio.create_task(lock_update(test_file, update, "first"))
        await first_entered.wait()
        second = asyncio.create_task(lock_update(test_file, update, "second"))
        try:
            await contended.wait()
            assert not second.done()
        finally:
            release.set()
            results = await asyncio.gather(first, second)
        assert results == ["first", "second"]
        assert test_file.read_text() == "initial first second"
        assert not lock_file.exists()

    @pytest.mark.anyio
    async def test_lock_update_removes_stale_lock(self, tmp_path):
        """lock_update should remove stale lock and proceed."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        lock_file = test_file.with_suffix(".txt.lock")

        # Create stale lock (old timestamp, dead process)
        lock_file.write_text("otherhost:999999")
        old_time = time.time() - 660
        os.utime(lock_file, (old_time, old_time))

        async def update_file(file_path: Path) -> str:
            return "success"

        result = await lock_update(test_file, update_file)

        assert result == "success"
        assert not lock_file.exists()
