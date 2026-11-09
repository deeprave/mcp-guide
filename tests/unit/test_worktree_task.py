"""Tests for worktree session preflight and inventory handling."""

import time
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.activation import TaskActivation
from mcp_guide.worktree_task import WorktreeTask


class Activation:
    """Small task activation double that records task-owned state."""

    def __init__(self, session):
        self.session = session
        self.data = {}

    def get_cached_data(self, key):
        return self.data.get(key)

    def set_cached_data(self, key, value):
        self.data[key] = value


@pytest.mark.anyio
async def test_other_worktree_cwd_requires_a_fresh_session():
    task = WorktreeTask()
    activation = Activation(
        SimpleNamespace(
            bound_root_path=Path("/client/project"),
            worktree_path=Path("/client/project_languid-lizard"),
            worktree_name="languid-lizard",
        )
    )
    activation.data["worktree_inventory"] = {
        "/client/project",
        "/client/project_languid-lizard",
        "/client/project_calm-otter",
    }
    activation.data["worktree_inventory_observed_at"] = time.time()
    task.activation = cast(TaskActivation, activation)

    result = await task.handle_event(EventType.FS_CWD, {"working_directory": "/client/project_calm-otter"})

    assert result is not None
    assert result.result is False
    assert result.message is not None
    assert "fresh Guide interaction" in result.message
    assert "project_languid-lizard" not in result.message


@pytest.mark.anyio
async def test_worktree_cwd_allows_descendants_of_the_configured_bound_worktree():
    task = WorktreeTask()
    activation = Activation(
        SimpleNamespace(
            bound_root_path=Path("/client/project"),
            worktree_path=Path("/client/project_languid-lizard"),
            worktree_name="languid-lizard",
        )
    )
    activation.data["worktree_inventory"] = {"/client/project", "/client/project_languid-lizard"}
    activation.data["worktree_inventory_observed_at"] = time.time()
    task.activation = cast(TaskActivation, activation)

    result = await task.handle_event(
        EventType.FS_CWD, {"working_directory": "/client/project_languid-lizard/src/mcp_guide"}
    )

    assert result is None


@pytest.mark.anyio
async def test_worktree_cwd_rejects_a_path_absent_from_the_git_worktree_inventory():
    task = WorktreeTask()
    activation = Activation(
        SimpleNamespace(
            bound_root_path=Path("/client/project"),
            worktree_path=Path("/client/project_languid-lizard"),
            worktree_name="languid-lizard",
        )
    )
    activation.data["worktree_inventory"] = {"/client/project"}
    activation.data["worktree_inventory_observed_at"] = time.time()
    task.activation = cast(TaskActivation, activation)

    result = await task.handle_event(EventType.FS_CWD, {"working_directory": "/client/project_calm-otter"})

    assert result is not None
    assert result.result is False
    assert result.message is not None
    assert "not a configured Git worktree" in result.message


@pytest.mark.anyio
async def test_different_worktree_cwd_requires_inventory_before_preflight():
    task = WorktreeTask()
    activation = Activation(
        SimpleNamespace(
            bound_root_path=Path("/client/project"),
            worktree_path=Path("/client/project_languid-lizard"),
            worktree_name="languid-lizard",
        )
    )
    task.activation = cast(TaskActivation, activation)

    result = await task.handle_event(EventType.FS_CWD, {"working_directory": "/client/project_calm-otter"})

    assert result is not None
    assert result.result is False
    assert result.message is not None
    assert "guide://_worktree/list" in result.message


def test_worktree_inventory_expires_after_handoff_lock_timeout():
    task = WorktreeTask()
    activation = Activation(SimpleNamespace(bound_root_path=Path("/client/project")))
    activation.data["worktree_inventory"] = {"/client/project"}
    activation.data["worktree_inventory_observed_at"] = 100.0
    task.activation = cast(TaskActivation, activation)

    assert task.is_inventory_current(now=190.0)
    assert not task.is_inventory_current(now=190.1)
    assert task.active_worktree_paths() == set()

    activation.data["worktree_inventory_observed_at"] = time.time()
    task.invalidate_inventory()
    assert not task.is_inventory_current()
