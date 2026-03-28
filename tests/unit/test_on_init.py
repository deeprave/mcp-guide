"""Tests for @guide.on_init() decorator and initialization flow."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.render.content import RenderedContent
from mcp_guide.render.frontmatter import Frontmatter


def make_rendered_content(content: str, instruction: str | None = None) -> RenderedContent:
    """Helper to create RenderedContent for mocking."""
    return RenderedContent(
        content=content,
        frontmatter=Frontmatter({"instruction": instruction} if instruction else {}),
        template_path=Path("test.mustache"),
        template_name="test",
        frontmatter_length=0,
        content_length=len(content),
    )


class TestOnInitDecorator:
    """Test @guide.on_init() decorator functionality."""

    def test_on_init_decorator_registers_handler(self):
        """Test that @guide.on_init() registers startup handlers."""
        from mcp_guide.guide import GuideMCP

        guide = GuideMCP("test")

        handler_called = False

        @guide.on_init()
        async def test_handler():
            nonlocal handler_called
            handler_called = True

        assert len(guide._startup_handlers) == 1
        assert guide._startup_handlers[0] == test_handler

    def test_on_init_decorator_multiple_handlers(self):
        """Test that multiple handlers can be registered."""
        from mcp_guide.guide import GuideMCP

        guide = GuideMCP("test")

        @guide.on_init()
        async def handler1():
            pass

        @guide.on_init()
        async def handler2():
            pass

        assert len(guide._startup_handlers) == 2


class TestLifespanExecution:
    """Test guide_lifespan() context manager execution."""

    @pytest.mark.anyio
    async def test_lifespan_executes_handlers(self):
        """Test that lifespan executes all registered handlers."""
        from mcp_guide.guide import GuideMCP
        from mcp_guide.server import guide_lifespan

        guide = GuideMCP("test")

        handler1_called = False
        handler2_called = False

        @guide.on_init()
        async def handler1():
            nonlocal handler1_called
            handler1_called = True

        @guide.on_init()
        async def handler2():
            nonlocal handler2_called
            handler2_called = True

        async with guide_lifespan(guide):
            pass

        assert handler1_called
        assert handler2_called

    @pytest.mark.anyio
    async def test_lifespan_continues_on_handler_error(self):
        """Test that lifespan continues executing handlers even if one fails."""
        from mcp_guide.guide import GuideMCP
        from mcp_guide.server import guide_lifespan

        guide = GuideMCP("test")

        handler2_called = False

        @guide.on_init()
        async def failing_handler():
            raise RuntimeError("Test error")

        @guide.on_init()
        async def handler2():
            nonlocal handler2_called
            handler2_called = True

        async with guide_lifespan(guide):
            pass

        # Second handler should still execute
        assert handler2_called


class TestTaskManagerOnInit:
    """Test TaskManager flag resolution."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "scenario,flags,expected",
        [
            ("enabled", {"test-flag": True}, True),
            ("disabled", {"test-flag": False}, False),
            ("missing", {}, False),
        ],
        ids=lambda x: x if isinstance(x, str) else str(x),
    )
    async def test_task_manager_requires_flag(self, scenario, flags, expected):
        """Test that requires_flag() returns correct value based on flag state."""
        from mcp_guide.task_manager.manager import TaskManager

        await TaskManager._reset_for_testing()
        task_manager = TaskManager()
        task_manager._resolved_flags = flags

        assert await task_manager.requires_flag("test-flag") is expected

    @pytest.mark.anyio
    async def test_resolved_flags_lazy_resolution(self):
        """Test that resolved_flags() lazily resolves on first call and caches."""
        from mcp_guide.task_manager.manager import TaskManager

        await TaskManager._reset_for_testing()
        task_manager = TaskManager()

        mock_session = Mock()
        mock_session.add_listener = Mock()

        with (
            patch("mcp_guide.task_manager.manager.get_session", new_callable=AsyncMock, return_value=mock_session),
            patch(
                "mcp_guide.task_manager.manager.resolve_all_flags", new_callable=AsyncMock, return_value={"flag": True}
            ),
        ):
            flags = await task_manager.resolved_flags()
            assert flags == {"flag": True}
            mock_session.add_listener.assert_called_once_with(task_manager)

    @pytest.mark.anyio
    async def test_resolved_flags_cache_invalidated_on_project_change(self):
        """Test that on_project_changed clears the cached flags."""
        from mcp_guide.task_manager.manager import TaskManager

        await TaskManager._reset_for_testing()
        task_manager = TaskManager()
        task_manager._resolved_flags = {"old": True}

        await task_manager.on_project_changed(Mock(), "old", "new")

        assert task_manager._resolved_flags is None

    @pytest.mark.anyio
    async def test_resolved_flags_cache_invalidated_on_config_change(self):
        """Test that on_config_changed clears the cached flags."""
        from mcp_guide.task_manager.manager import TaskManager

        await TaskManager._reset_for_testing()
        task_manager = TaskManager()
        task_manager._resolved_flags = {"cached": True}

        await task_manager.on_config_changed(Mock())

        assert task_manager._resolved_flags is None


class TestTaskInitialise:
    """Test task initialisation via TIMER_ONCE dispatch through handle_event."""

    @pytest.mark.anyio
    async def test_openspec_task_initialise_checks_flag(self):
        """Test that OpenSpecTask unsubscribes when flag is disabled via TIMER_ONCE."""
        from mcp_guide.openspec.task import OpenSpecTask
        from mcp_guide.task_manager.interception import EventType

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = AsyncMock(return_value=False)
        mock_task_manager.unsubscribe = AsyncMock()

        task = OpenSpecTask(task_manager=mock_task_manager)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        assert result is not None
        assert result.result is True
        mock_task_manager.requires_flag.assert_called_once_with("openspec")
        mock_task_manager.unsubscribe.assert_called_once_with(task)
        assert task._flag_checked

    @pytest.mark.anyio
    async def test_workflow_task_initialise_queues_setup(self):
        """Test that WorkflowMonitorTask queues setup instruction via TIMER_ONCE."""
        from mcp_guide.task_manager.interception import EventType
        from mcp_guide.workflow.tasks import WorkflowMonitorTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = AsyncMock(return_value=True)
        mock_task_manager.resolved_flags = AsyncMock(return_value={"workflow": True})
        mock_task_manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")

        with patch("mcp_guide.workflow.tasks.render_workflow_template") as mock_render:
            mock_render.return_value = make_rendered_content("setup content")

            task = WorkflowMonitorTask()
            task.task_manager = mock_task_manager

            result = await task.handle_event(EventType.TIMER_ONCE, {})

            assert result is not None
            assert result.result is True
            mock_task_manager.requires_flag.assert_called_once_with("workflow")
            mock_render.assert_called_once_with("monitoring-setup")
            mock_task_manager.queue_instruction_with_ack.assert_called_once_with("setup content")
            assert task._setup_done

    @pytest.mark.anyio
    async def test_workflow_task_initialise_unsubscribes_when_disabled(self):
        """Test that WorkflowMonitorTask unsubscribes when flag is disabled via TIMER_ONCE."""
        from mcp_guide.task_manager.interception import EventType
        from mcp_guide.workflow.tasks import WorkflowMonitorTask

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = AsyncMock(return_value=False)
        mock_task_manager.unsubscribe = AsyncMock()

        task = WorkflowMonitorTask()
        task.task_manager = mock_task_manager

        result = await task.handle_event(EventType.TIMER_ONCE, {})

        assert result is not None
        assert result.result is True
        mock_task_manager.requires_flag.assert_called_once_with("workflow")
        mock_task_manager.unsubscribe.assert_called_once_with(task)

    @pytest.mark.anyio
    async def test_client_context_task_initialise_requests_info_when_enabled(self):
        """Test that ClientContextTask requests OS info via TIMER_ONCE when flag is enabled."""
        from mcp_guide.context.tasks import ClientContextTask
        from mcp_guide.task_manager.interception import EventType

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = AsyncMock(return_value=True)
        mock_task_manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")

        with patch("mcp_guide.context.tasks.render_context_template") as mock_render:
            mock_render.return_value = make_rendered_content("client context setup")

            task = ClientContextTask(task_manager=mock_task_manager)
            result = await task.handle_event(EventType.TIMER_ONCE, {})

            assert result is not None
            assert result.result is True
            mock_task_manager.requires_flag.assert_called_once_with("allow-client-info")
            mock_render.assert_called_once_with("client-context-setup")
            mock_task_manager.queue_instruction_with_ack.assert_called_once_with("client context setup")
            assert task._os_info_requested
            assert task._flag_checked

    @pytest.mark.anyio
    async def test_client_context_task_initialise_unsubscribes_when_disabled(self):
        """Test that ClientContextTask unsubscribes via TIMER_ONCE when flag is disabled."""
        from mcp_guide.context.tasks import ClientContextTask
        from mcp_guide.task_manager.interception import EventType

        mock_task_manager = Mock()
        mock_task_manager.requires_flag = AsyncMock(return_value=False)
        mock_task_manager.unsubscribe = AsyncMock()

        task = ClientContextTask(task_manager=mock_task_manager)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        assert result is not None
        assert result.result is True
        mock_task_manager.requires_flag.assert_called_once_with("allow-client-info")
        mock_task_manager.unsubscribe.assert_called_once_with(task)
        assert task._flag_checked
