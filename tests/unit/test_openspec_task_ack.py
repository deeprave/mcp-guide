"""Tests for OpenSpecTask acknowledgement tracking."""

import pytest

from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset TaskManager singleton before each test."""
    TaskManager._instance = None
    yield
    TaskManager._instance = None


class TestOpenSpecTaskAcknowledgement:
    """Test OpenSpecTask acknowledgement tracking."""

    @pytest.mark.anyio
    async def test_cli_check_stores_instruction_id(self):
        """Test that CLI check stores instruction ID."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_cli_check()

        assert task._cli_instruction_id is not None
        assert task._cli_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_cli_response_acknowledges_instruction(self):
        """Test that CLI response acknowledges instruction."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_cli_check()
        instruction_id = task._cli_instruction_id

        # Simulate CLI response
        await task.handle_event(
            EventType.FS_COMMAND, {"command": "openspec", "found": True, "path": "/usr/bin/openspec"}
        )

        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_version_check_stores_instruction_id(self):
        """Test that version check stores instruction ID."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_version_check()

        assert task._version_instruction_id is not None
        assert task._version_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_version_response_acknowledges_instruction(self):
        """Test that version response acknowledges instruction."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_version_check()
        instruction_id = task._version_instruction_id

        # Simulate version response
        await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".openspec-version.txt", "content": "1.2.3"})

        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_project_check_stores_instruction_id(self):
        """Test that project check stores instruction ID."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_project_check()

        assert task._project_instruction_id is not None
        assert task._project_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_changes_request_stores_instruction_id(self):
        """Test that changes request stores instruction ID."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_changes_json()

        assert task._changes_instruction_id is not None
        assert task._changes_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_changes_response_acknowledges_instruction(self):
        """Test that changes response acknowledges instruction."""
        manager = TaskManager()
        task = OpenSpecTask(manager)

        await task.request_changes_json()
        instruction_id = task._changes_instruction_id

        # Simulate changes response
        await task.handle_event(
            EventType.FS_FILE_CONTENT, {"path": ".openspec-changes.json", "content": '{"changes": []}'}
        )

        assert instruction_id not in manager._tracked_instructions
