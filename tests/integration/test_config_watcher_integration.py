"""Integration test for config file watcher functionality."""

import asyncio
import logging
from pathlib import Path

import pytest

from mcp_guide.session import get_or_create_session, remove_current_session


@pytest.mark.asyncio
async def test_config_watcher_integration(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that config file changes trigger session reload with warning log."""
    # Setup logging to capture warnings
    caplog.set_level(logging.WARNING)

    # Create a session with config watcher
    session = await get_or_create_session(project_name="test-watcher", _config_dir_for_tests=str(tmp_path))

    # Get initial project to populate cache
    initial_project = await session.get_project()
    assert initial_project.name == "test-watcher"

    # Verify cache is populated
    assert session._cached_project is not None

    # Modify the config file externally to trigger watcher
    config_file = session._config_manager.config_file

    # Wait a moment to ensure watcher is running
    await asyncio.sleep(0.1)

    # Modify the config file
    config_content = config_file.read_text()
    config_file.write_text(config_content + "\n# External modification")

    # Wait for watcher to detect change and process it
    await asyncio.sleep(1.5)  # Longer than poll interval

    # Verify cache was invalidated
    assert session._cached_project is None

    # Verify warning log was generated
    warning_logs = [record for record in caplog.records if record.levelno >= logging.WARNING]
    assert len(warning_logs) > 0

    # Check that the warning message contains expected content
    warning_message = warning_logs[0].message
    assert "Configuration file changed externally" in warning_message
    assert "reloading session test-watcher" in warning_message
    assert str(config_file) in warning_message

    # Cleanup
    await remove_current_session("test-watcher")


@pytest.mark.asyncio
async def test_config_watcher_cleanup(tmp_path: Path) -> None:
    """Test that config watcher is properly cleaned up when session is removed."""
    # Create a session
    session = await get_or_create_session(project_name="test-cleanup", _config_dir_for_tests=str(tmp_path))

    # Verify watcher was created
    assert session._config_watcher is not None

    # Remove session (should trigger cleanup)
    await remove_current_session("test-cleanup")

    # Wait for cleanup to complete
    await asyncio.sleep(0.1)

    # Verify watcher was cleaned up
    assert session._config_watcher is None
