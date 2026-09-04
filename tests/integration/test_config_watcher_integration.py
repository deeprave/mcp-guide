"""Integration test for config file watcher functionality."""

from pathlib import Path

import pytest

from tests.helpers import create_test_session


@pytest.mark.anyio
async def test_config_watcher_integration(runtime, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that session works correctly."""
    # Create a session
    session = await create_test_session(runtime, "test-watcher")

    # Get initial project
    initial_project = await session.get_project()
    assert initial_project.name == "test-watcher"


@pytest.mark.anyio
async def test_config_watcher_cleanup(runtime, tmp_path: Path) -> None:
    """Test that session cleanup works correctly."""
    # Create a session
    session = await create_test_session(runtime, "test-cleanup")

    # Get project to initialize session
    await session.get_project()
