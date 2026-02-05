"""Tests for ClientContextTask acknowledgement tracking."""

import pytest

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset TaskManager singleton before each test."""
    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class TestClientContextTaskAcknowledgement:
    """Test ClientContextTask acknowledgement tracking."""

    @pytest.mark.anyio
    async def test_os_info_request_stores_instruction_id(self):
        """Test that OS info request stores instruction ID."""
        manager = TaskManager()
        task = ClientContextTask(manager)

        await task.request_basic_os_info()

        assert task._os_instruction_id is not None
        assert task._os_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_os_info_response_acknowledges_instruction(self):
        """Test that OS info response acknowledges instruction."""
        manager = TaskManager()
        task = ClientContextTask(manager)

        await task.request_basic_os_info()
        instruction_id = task._os_instruction_id

        # Simulate OS info response
        await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".client-os.json", "content": '{"client": {}}'})

        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_detailed_context_request_stores_instruction_id(self):
        """Test that detailed context request stores instruction ID."""
        manager = TaskManager()
        task = ClientContextTask(manager)

        await task._request_detailed_context({"client": {}})

        assert task._context_instruction_id is not None
        assert task._context_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_detailed_context_response_acknowledges_instruction(self):
        """Test that detailed context response acknowledges instruction."""
        manager = TaskManager()
        task = ClientContextTask(manager)

        await task._request_detailed_context({"client": {}})
        instruction_id = task._context_instruction_id

        # Simulate context response
        await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".client-context.json", "content": "{}"})

        assert instruction_id not in manager._tracked_instructions
