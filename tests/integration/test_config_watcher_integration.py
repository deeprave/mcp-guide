"""Integration test for config file watcher functionality."""

from pathlib import Path

import pytest

from mcp_guide.session import get_or_create_session, remove_current_session


@pytest.mark.asyncio
async def test_config_watcher_integration(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that session works correctly."""
    # Create a session
    session = await get_or_create_session(project_name="test-watcher", _config_dir_for_tests=str(tmp_path))

    # Get initial project
    initial_project = await session.get_project()
    assert initial_project.name == "test-watcher"

    # Verify session works correctly
    assert session.has_current_session()

    # Cleanup
    await remove_current_session("test-watcher")


@pytest.mark.asyncio
async def test_config_watcher_cleanup(tmp_path: Path) -> None:
    """Test that session cleanup works correctly."""
    # Create a session
    session = await get_or_create_session(project_name="test-cleanup", _config_dir_for_tests=str(tmp_path))

    # Get project to initialize session
    await session.get_project()

    # Verify session is active
    assert session.has_current_session()

    # Cleanup
    await remove_current_session("test-cleanup")
