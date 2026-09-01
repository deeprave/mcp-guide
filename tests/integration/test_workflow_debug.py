"""Integration coverage for Session-owned workflow task state."""

import pytest

from tests.helpers import create_test_session


@pytest.fixture(autouse=True)
async def bound_session(tmp_path):
    """Install an isolated bound Session for each task-manager interaction."""
    session = await create_test_session("workflow", _config_dir_for_tests=str(tmp_path))
    yield session


@pytest.mark.anyio
async def test_workflow_task_registration(bound_session) -> None:
    """A bound interaction owns a usable task manager."""
    task_manager = bound_session.task_manager
    assert task_manager is bound_session.task_manager


@pytest.mark.anyio
async def test_basic_task_manager(bound_session) -> None:
    """Task state is isolated to the active Session."""
    task_manager = bound_session.task_manager
    task_manager.set_cached_data("test_key", "test_value")
    assert task_manager.get_cached_data("test_key") == "test_value"
