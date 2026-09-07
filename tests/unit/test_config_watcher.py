"""Configuration polling delivers changes despite a failing callback."""

import asyncio
import os
from pathlib import Path

import pytest

from mcp_guide.watchers.config_watcher import ConfigWatcher


@pytest.mark.anyio
async def test_config_watcher_requires_existing_file(tmp_path):
    watcher = ConfigWatcher(str(tmp_path / "missing.yaml"))
    with pytest.raises(FileNotFoundError, match="Path does not exist"):
        await watcher.has_changed()


@pytest.mark.anyio
async def test_polling_notifies_all_callbacks_and_survives_callback_failure(tmp_path, monkeypatch):
    # Suppress expected exception logging, not watcher execution.
    monkeypatch.setattr("mcp_guide.core.path_watcher.logger.exception", lambda *args, **kwargs: None)
    config_file = tmp_path / "config.yaml"
    config_file.write_text("initial: value")
    received = []
    notified = asyncio.Event()

    def record_first(path):
        received.append(("first", path, Path(path).read_text()))

    def fail(path):
        raise RuntimeError("Callback error")

    async def record_last(path):
        received.append(("last", path, Path(path).read_text()))
        notified.set()

    watcher = ConfigWatcher(str(config_file), record_first, poll_interval=0.01)
    watcher.add_callback(fail)
    watcher.add_callback(record_last)
    assert not await watcher.has_changed()
    assert not watcher.is_running()
    await watcher.start()
    try:
        assert watcher.is_running()
        for value in ("modified: value", "modified: again"):
            notified.clear()
            previous_mtime = config_file.stat().st_mtime
            config_file.write_text(value)
            os.utime(config_file, (previous_mtime + 1, previous_mtime + 1))
            await asyncio.wait_for(notified.wait(), timeout=2)
            assert received[-2:] == [
                ("first", str(config_file), value),
                ("last", str(config_file), value),
            ]
        assert len(received) == 4
    finally:
        await watcher.stop()
    assert not watcher.is_running()
