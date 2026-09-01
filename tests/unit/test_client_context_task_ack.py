"""Tests for ClientContextTask acknowledgement tracking."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager


def _manager() -> TaskManager:
    """Create a manager with the session ownership required for cache updates."""
    return TaskManager(session=Mock(template_cache=Mock()))


@pytest.fixture(autouse=True)
async def reset_task_manager():
    """Reset TaskManager singleton before each test."""
    await TaskManager._reset_for_testing()
    yield
    await TaskManager._reset_for_testing()


@pytest.fixture(autouse=True)
def mock_context_templates():
    """Keep acknowledgement tests focused on task tracking, not rendering."""

    async def render(session, template_name, context=None):
        return Mock(content=f"client context request: {template_name}")

    with patch("mcp_guide.context.tasks.render_context_template", new=AsyncMock(side_effect=render)):
        yield


class TestClientContextTaskAcknowledgement:
    """Test ClientContextTask acknowledgement tracking."""

    @pytest.mark.anyio
    async def test_os_info_request_stores_instruction_id(self):
        """Test that OS info request stores instruction ID."""
        manager = _manager()
        task = ClientContextTask(manager)

        await task.request_basic_os_info()

        assert task._os_instruction_id is not None
        assert task._os_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_os_info_response_acknowledges_instruction(self):
        """Test that OS info response acknowledges instruction."""
        manager = _manager()
        task = ClientContextTask(manager)

        await task.request_basic_os_info()
        instruction_id = task._os_instruction_id
        task._flag_checked = True

        # Simulate OS info response
        await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".client-os.json", "content": '{"client": {}}'})

        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_detailed_context_request_stores_instruction_id(self):
        """Test that detailed context request stores instruction ID."""
        manager = _manager()
        task = ClientContextTask(manager)

        await task._request_detailed_context({"client": {}})

        assert task._context_instruction_id is not None
        assert task._context_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_detailed_context_response_acknowledges_instruction(self):
        """Test that detailed context response acknowledges instruction."""
        manager = _manager()
        task = ClientContextTask(manager)

        await task._request_detailed_context({"client": {}})
        instruction_id = task._context_instruction_id
        task._flag_checked = True

        # Simulate context response
        await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".client-context.json", "content": "{}"})

        assert instruction_id not in manager._tracked_instructions
